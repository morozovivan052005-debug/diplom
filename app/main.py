from __future__ import annotations

from collections import defaultdict

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app import db
from app.forms import ProfileForm, ProgramSelectForm
from app.models import ProgramExercise, TrainingProgram, UserProfile
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
            form.gender.data = "male" if prof.is_male else "female"
            form.activity_level.data = prof.activity_level
            form.goal_code.data = prof.goal_code or "maintain"

    if form.validate_on_submit():
        if prof is None:
            prof = UserProfile(user_id=current_user.id)
            db.session.add(prof)

        prof.height_cm = form.height_cm.data
        prof.weight_kg = form.weight_kg.data
        prof.age_years = form.age_years.data
        prof.is_male = form.gender.data == "male"
        prof.activity_level = form.activity_level.data
        prof.goal = None
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
