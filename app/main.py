from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app import db
from app.forms import ProfileForm, ProgramSelectForm
from app.models import Goal, ProgramExercise, ProgressLog, TrainingProgram, UserProfile
from app.utils.bmr import ACTIVITY_MULTIPLIERS, bmr_mifflin_st_jeor, tdee_from_bmr
from app.utils.recommendations import bmi as calc_bmi
from app.utils.recommendations import build_summary

bp = Blueprint("main", __name__)


def _find_program_for_goal(goal_code: str | None) -> TrainingProgram | None:
    if not goal_code:
        return None
    g = goal_code.strip().lower()
    q = TrainingProgram.query.filter(TrainingProgram.goal_type.isnot(None))
    match = q.filter(db.func.lower(TrainingProgram.goal_type) == g).first()
    if match:
        return match
    return TrainingProgram.query.filter(TrainingProgram.goal_type.ilike(f"%{g}%")).first()


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()
    prof = current_user.profile

    if prof:
        if request.method == "GET":
            form.height_cm.data = prof.height_cm
            form.weight_kg.data = prof.weight_kg
            form.age_years.data = prof.age_years
            form.is_male.data = prof.is_male
            form.activity_level.data = prof.activity_level
            form.goal.data = prof.goal or ""
            form.goal_code.data = prof.goal_code or "maintain"

    if form.validate_on_submit():
        if prof is None:
            prof = UserProfile(user_id=current_user.id)
            db.session.add(prof)

        prof.height_cm = form.height_cm.data
        prof.weight_kg = form.weight_kg.data
        prof.age_years = form.age_years.data
        prof.is_male = form.is_male.data
        prof.activity_level = form.activity_level.data
        prof.goal = form.goal.data or None
        prof.goal_code = form.goal_code.data

        matched = _find_program_for_goal(prof.goal_code)
        prof.assigned_program_id = matched.id if matched else None

        db.session.commit()
        flash("Профиль сохранён. Рекомендации и программа обновлены.", "success")
        return redirect(url_for("main.profile"))

    summary = None
    if prof:
        try:
            bmr = bmr_mifflin_st_jeor(
                prof.weight_kg, prof.height_cm, prof.age_years, prof.is_male
            )
            tdee = tdee_from_bmr(bmr, prof.activity_level)
            bmi_val = calc_bmi(prof.weight_kg, prof.height_cm)
            summary = build_summary(
                bmi_value=bmi_val,
                bmr=bmr,
                tdee=tdee,
                goal_code=prof.goal_code or "maintain",
            )
        except (ValueError, KeyError):
            summary = None

    return render_template(
        "profile.html",
        form=form,
        summary=summary,
        assigned_program=prof.assigned_program if prof else None,
        activity_labels=ACTIVITY_MULTIPLIERS,
    )


@bp.route("/my-program", methods=["GET", "POST"])
@login_required
def my_program():
    prof = current_user.profile
    if not prof:
        flash(
            "Сначала заполните профиль — после этого можно будет выбрать готовую программу.",
            "warning",
        )
        return redirect(url_for("main.profile"))

    select_form = ProgramSelectForm()
    if select_form.validate_on_submit():
        try:
            program_id = int(select_form.program_id.data)
        except (TypeError, ValueError):
            flash("Некорректный номер программы.", "danger")
            return redirect(url_for("main.my_program"))

        program = db.session.get(TrainingProgram, program_id)
        if not program:
            flash("Выбранная программа не найдена.", "danger")
            return redirect(url_for("main.my_program"))

        prof.assigned_program_id = program.id
        db.session.commit()
        flash(f"Программа «{program.name}» выбрана.", "success")
        return redirect(url_for("main.my_program"))

    all_programs = (
        TrainingProgram.query.order_by(
            TrainingProgram.goal_type,
            TrainingProgram.difficulty,
            TrainingProgram.name,
        ).all()
    )

    if not prof.assigned_program_id:
        return render_template(
            "my_program.html",
            program=None,
            by_day={},
            all_programs=all_programs,
            select_form=select_form,
        )

    program = prof.assigned_program
    if not program:
        flash("Программа не найдена. Обратитесь к администратору.", "danger")
        return redirect(url_for("main.profile"))

    rows = (
        ProgramExercise.query.options(joinedload(ProgramExercise.exercise))
        .filter_by(program_id=program.id)
        .order_by(ProgramExercise.day_number, ProgramExercise.order_in_day)
        .all()
    )
    by_day: dict[int, list[ProgramExercise]] = defaultdict(list)
    for row in rows:
        by_day[row.day_number].append(row)

    return render_template(
        "my_program.html",
        program=program,
        by_day=dict(sorted(by_day.items(), key=lambda x: x[0])),
        all_programs=all_programs,
        select_form=select_form,
    )


@bp.route("/calendar", methods=["GET"])
@login_required
def calendar():
    """Отображение интерактивного календаря с целями и логированием прогресса."""
    goals = (
        Goal.query.filter_by(user_id=current_user.id)
        .order_by(Goal.created_at.desc(), Goal.id.desc())
        .all()
    )
    goals_json = [
        {
            "id": goal.id,
            "goal_type": goal.goal_type,
            "current_value": float(goal.current_value),
            "target_value": float(goal.target_value),
            "unit": goal.unit,
        }
        for goal in goals
    ]

    # Получаем текущий месяц и год из параметров запроса (если есть)
    from datetime import date
    today = date.today()
    year = request.args.get("year", default=today.year, type=int)
    month = request.args.get("month", default=today.month, type=int)

    return render_template(
        "calendar.html",
        goals=goals,
        goals_json=goals_json,
        year=year,
        month=month,
        today=today,
    )


@bp.route("/api/calendar/<int:year>/<int:month>")
@login_required
def api_calendar(year: int, month: int):
    """API для получения логирования за месяц."""
    logs = ProgressLog.query.filter(
        ProgressLog.user_id == current_user.id,
        db.func.extract("year", ProgressLog.log_date) == year,
        db.func.extract("month", ProgressLog.log_date) == month,
    ).all()

    goal_ids = {log.goal_id for log in logs if log.goal_id}
    goals_map = {}
    if goal_ids:
        goals_map = {
            goal.id: goal
            for goal in Goal.query.filter(Goal.id.in_(goal_ids), Goal.user_id == current_user.id).all()
        }

    result = {}
    for log in logs:
        day = log.log_date.day
        if day not in result:
            result[day] = []

        goal = goals_map.get(log.goal_id) if log.goal_id else None
        result[day].append({
            "id": log.id,
            "goal_id": log.goal_id,
            "goal_type": goal.goal_type if goal else "custom",
            "value": float(log.value),
            "unit": goal.unit if goal else "",
            "notes": log.notes or "",
        })

    return jsonify(result)


@bp.route("/api/log-progress", methods=["POST"])
@login_required
def api_log_progress():
    """API для добавления/обновления логирования прогресса."""
    data = request.get_json()

    log_date_str = data.get("log_date")
    goal_id = data.get("goal_id")
    value = data.get("value")
    notes = data.get("notes", "")

    if not log_date_str or value is None:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        log_date = datetime.strptime(log_date_str, "%Y-%m-%d").date()
        goal_id = int(goal_id)
        value = float(value)
    except ValueError:
        return jsonify({"error": "Invalid input format"}), 400

    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    if not goal:
        return jsonify({"error": "Goal not found for current user"}), 404

    # Проверяем, существует ли уже такое логирование
    existing = ProgressLog.query.filter_by(
        user_id=current_user.id,
        log_date=log_date,
        goal_id=goal_id,
    ).first()

    if existing:
        existing.value = value
        existing.notes = notes
        db.session.commit()
        return jsonify({
            "id": existing.id,
            "status": "updated",
        })
    else:
        new_log = ProgressLog(
            user_id=current_user.id,
            goal_id=goal.id,
            log_date=log_date,
            value=value,
            notes=notes,
        )
        db.session.add(new_log)
        db.session.commit()
        return jsonify({
            "id": new_log.id,
            "status": "created",
        }), 201


@bp.route("/api/delete-log/<int:log_id>", methods=["DELETE"])
@login_required
def api_delete_log(log_id: int):
    """API для удаления логирования прогресса."""
    log = ProgressLog.query.get(log_id)
    
    if not log or log.user_id != current_user.id:
        return jsonify({"error": "Not found"}), 404
    
    db.session.delete(log)
    db.session.commit()
    
    return jsonify({"status": "deleted"})
