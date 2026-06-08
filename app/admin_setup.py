from flask import redirect, request, url_for
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user

from app import db
from app.models import Exercise, Goal, ProgramExercise, ProgressLog, TrainingProgram, User, UserProfile


class SecureModelView(ModelView):
    page_size = 25
    can_view_details = True

    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, "is_admin", False)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("auth.login", next=request.url))


class UserAdminView(SecureModelView):
    column_list = ("id", "email", "is_admin", "created_at")
    column_searchable_list = ("email",)
    form_columns = ("email", "is_admin")
    column_labels = {
        "email": "Email",
        "is_admin": "Администратор",
        "created_at": "Создан",
    }
    form_widget_args = {
        "email": {"placeholder": "user@example.com"},
    }
    can_delete = True
    can_create = False


class UserProfileAdminView(SecureModelView):
    column_list = ("id", "user", "height_cm", "weight_kg", "age_years", "activity_level", "goal_code")
    column_searchable_list = ("goal", "goal_code")
    form_columns = (
        "user",
        "height_cm",
        "weight_kg",
        "age_years",
        "is_male",
        "activity_level",
        "goal",
        "goal_code",
        "assigned_program",
    )
    column_labels = {
        "user": "Пользователь",
        "height_cm": "Рост (см)",
        "weight_kg": "Вес (кг)",
        "age_years": "Возраст",
        "is_male": "Мужской пол",
        "activity_level": "Активность",
        "goal": "Комментарий цели",
        "goal_code": "Код цели",
        "assigned_program": "Назначенная программа",
    }
    form_choices = {
        "activity_level": [
            ("sedentary", "Малоподвижный"),
            ("light", "Лёгкая нагрузка"),
            ("moderate", "Умеренная"),
            ("high", "Высокая"),
            ("very_high", "Очень высокая"),
        ],
        "goal_code": [
            ("lose_weight", "Снижение веса"),
            ("maintain", "Поддержание веса"),
            ("recomp", "Рекомпозиция"),
            ("gain_muscle", "Набор мышечной массы"),
        ],
    }
    form_widget_args = {
        "height_cm": {"placeholder": "175"},
        "weight_kg": {"placeholder": "72.5"},
        "age_years": {"placeholder": "28"},
        "goal": {"placeholder": "Например: снизить вес к лету"},
    }


class ExerciseAdminView(SecureModelView):
    column_list = ("id", "name", "muscle_group", "equipment", "difficulty")
    column_searchable_list = ("name", "muscle_group", "equipment", "difficulty")
    form_columns = ("name", "description", "muscle_group", "equipment", "difficulty")
    column_labels = {
        "name": "Название",
        "description": "Описание",
        "muscle_group": "Группа мышц",
        "equipment": "Инвентарь",
        "difficulty": "Сложность",
    }
    form_choices = {
        "muscle_group": [
            ("Грудь", "Грудь"),
            ("Спина", "Спина"),
            ("Ноги", "Ноги"),
            ("Плечи", "Плечи"),
            ("Руки", "Руки"),
            ("Пресс", "Пресс"),
            ("Все тело", "Все тело"),
            ("Кардио", "Кардио"),
        ],
        "difficulty": [
            ("Начальный", "Начальный"),
            ("Средний", "Средний"),
            ("Продвинутый", "Продвинутый"),
        ],
    }
    form_widget_args = {
        "name": {"placeholder": "Приседания с собственным весом"},
        "equipment": {"placeholder": "Без инвентаря, гантели, штанга, тренажер"},
    }
    form_args = {
        "description": {
            "description": "Пример: держите спину ровно, колени направлены по линии стоп.",
            "render_kw": {
                "placeholder": "Коротко опишите технику выполнения и важные нюансы."
            }
        },
    }


class TrainingProgramAdminView(SecureModelView):
    column_list = ("id", "name", "goal_type", "difficulty", "duration_weeks")
    column_searchable_list = ("name", "goal_type", "difficulty")
    form_columns = ("name", "description", "goal_type", "difficulty", "duration_weeks")
    column_labels = {
        "name": "Название",
        "description": "Описание",
        "goal_type": "Тип цели",
        "difficulty": "Сложность",
        "duration_weeks": "Длительность (нед.)",
    }
    form_choices = {
        "goal_type": [
            ("lose_weight", "Снижение веса"),
            ("maintain", "Поддержание веса"),
            ("recomp", "Рекомпозиция"),
            ("gain_muscle", "Набор мышечной массы"),
        ],
        "difficulty": [
            ("Начальный", "Начальный"),
            ("Средний", "Средний"),
            ("Продвинутый", "Продвинутый"),
        ],
    }
    form_widget_args = {
        "name": {"placeholder": "Снижение веса: стартовая программа"},
        "duration_weeks": {"placeholder": "8"},
    }
    form_args = {
        "description": {
            "description": "Пример: 3 тренировки в неделю, фокус на технику и постепенное увеличение нагрузки.",
            "render_kw": {
                "placeholder": "Кому подходит программа, сколько тренировок в неделю, основной фокус."
            }
        },
    }


class ProgramExerciseAdminView(SecureModelView):
    column_list = ("id", "program", "exercise", "day_number", "order_in_day", "sets", "reps")
    column_searchable_list = ("reps",)
    form_columns = ("program", "exercise", "day_number", "order_in_day", "sets", "reps", "notes")
    column_labels = {
        "program": "Программа",
        "exercise": "Упражнение",
        "day_number": "День",
        "order_in_day": "Порядок",
        "sets": "Подходы",
        "reps": "Повторения",
        "notes": "Заметки",
    }
    form_widget_args = {
        "day_number": {"placeholder": "1"},
        "order_in_day": {"placeholder": "1"},
        "sets": {"placeholder": "3"},
        "reps": {"placeholder": "10-12 или 30 сек"},
    }
    form_args = {
        "notes": {
            "description": "Пример: отдых 60 секунд между подходами.",
            "render_kw": {"placeholder": "Например: отдых 60 секунд между подходами"}
        },
    }


class GoalAdminView(SecureModelView):
    """Админ-представление для целей по весу/телу."""
    column_list = ("id", "user", "goal_type", "current_value", "target_value", "unit", "deadline")
    column_searchable_list = ("goal_type", "unit")
    form_columns = ("user", "goal_type", "current_value", "target_value", "unit", "deadline", "notes")
    column_labels = {
        "user": "Пользователь",
        "goal_type": "Тип цели",
        "current_value": "Текущее значение",
        "target_value": "Целевое значение",
        "unit": "Единица измерения",
        "deadline": "Срок",
        "notes": "Заметки"
    }
    form_choices = {
        "goal_type": [
            ("weight", "Вес"),
            ("body_fat", "Процент жира"),
            ("muscle", "Мышечная масса"),
            ("waist", "Талия"),
        ],
        "unit": [
            ("кг", "кг"),
            ("%", "%"),
            ("см", "см"),
        ],
    }
    form_widget_args = {
        "current_value": {"placeholder": "82.5"},
        "target_value": {"placeholder": "76"},
        "deadline": {"placeholder": "2026-08-31"},
    }
    form_args = {
        "notes": {
            "description": "Пример: цель на 12 недель.",
            "render_kw": {"placeholder": "Например: цель на 12 недель"}
        },
    }
    can_delete = True
    can_create = True


class ProgressLogAdminView(SecureModelView):
    """Админ-представление для логирования прогресса."""
    column_list = ("id", "user", "goal", "log_date", "value", "created_at")
    column_searchable_list = ()
    form_columns = ("user", "goal", "log_date", "value", "notes")
    column_labels = {
        "user": "Пользователь",
        "goal": "Цель",
        "log_date": "Дата логирования",
        "value": "Значение",
        "notes": "Заметки",
        "created_at": "Создано"
    }
    form_widget_args = {
        "log_date": {"placeholder": "2026-06-08"},
        "value": {"placeholder": "80.5"},
    }
    form_args = {
        "notes": {
            "description": "Пример: замер утром натощак.",
            "render_kw": {"placeholder": "Например: замер утром натощак"}
        },
    }
    can_delete = True
    can_create = True


def init_admin(app):
    admin = Admin(app, name="Админ-панель", template_mode="bootstrap4", url="/admin")

    admin.add_view(UserAdminView(User, db.session, name="Пользователи", endpoint="admin_users"))
    admin.add_view(
        UserProfileAdminView(UserProfile, db.session, name="Профили", endpoint="admin_profiles")
    )
    admin.add_view(
        ExerciseAdminView(Exercise, db.session, name="Упражнения", endpoint="admin_exercises")
    )
    admin.add_view(
        TrainingProgramAdminView(TrainingProgram, db.session, name="Программы тренировок", endpoint="admin_programs")
    )
    admin.add_view(
        ProgramExerciseAdminView(
            ProgramExercise, db.session, name="Упражнения в программах", endpoint="admin_program_exercises"
        )
    )
    admin.add_view(
        GoalAdminView(Goal, db.session, name="Цели", endpoint="admin_goals")
    )
    admin.add_view(
        ProgressLogAdminView(ProgressLog, db.session, name="Логирование прогресса", endpoint="admin_progress_logs")
    )

