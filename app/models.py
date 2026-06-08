from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    profile = db.relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __str__(self) -> str:
        return self.email


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class UserProfile(db.Model):
    """Антропометрия и цели — для персонализации рекомендаций и расчёта BMR."""

    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    height_cm = db.Column(db.Float, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    age_years = db.Column(db.Integer, nullable=False)
    is_male = db.Column(db.Boolean, nullable=False)
    activity_level = db.Column(db.String(32), nullable=False, default="moderate")
    goal = db.Column(db.String(64), nullable=True)
    goal_code = db.Column(db.String(32), nullable=True)
    assigned_program_id = db.Column(
        db.Integer, db.ForeignKey("training_programs.id", ondelete="SET NULL"), nullable=True
    )

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")
    assigned_program = db.relationship("TrainingProgram", foreign_keys=[assigned_program_id])


class Exercise(db.Model):
    """Упражнение для справочника и программ."""

    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    muscle_group = db.Column(db.String(100), nullable=True)
    equipment = db.Column(db.String(100), nullable=True)
    difficulty = db.Column(db.String(50), nullable=True)

    program_links = db.relationship("ProgramExercise", back_populates="exercise", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return self.name


class TrainingProgram(db.Model):
    """Шаблон тренировочной программы (админ создаёт, пользователь может быть привязан опционально)."""

    __tablename__ = "training_programs"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    goal_type = db.Column(db.String(64), nullable=True)
    difficulty = db.Column(db.String(50), nullable=True)
    duration_weeks = db.Column(db.Integer, nullable=True)

    exercises = db.relationship("ProgramExercise", back_populates="program", cascade="all, delete-orphan")

    def __str__(self) -> str:
        return self.name


class ProgramExercise(db.Model):
    """Связь программы и упражнения (день недели, порядок, подходы)."""

    __tablename__ = "program_exercises"

    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey("training_programs.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.id"), nullable=False)
    day_number = db.Column(db.Integer, nullable=False, default=1)
    order_in_day = db.Column(db.Integer, nullable=False, default=1)
    sets = db.Column(db.Integer, nullable=True)
    reps = db.Column(db.String(32), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    program = db.relationship("TrainingProgram", back_populates="exercises")
    exercise = db.relationship("Exercise", back_populates="program_links")

    def __str__(self) -> str:
        program_name = self.program.name if self.program else f"Программа #{self.program_id}"
        exercise_name = self.exercise.name if self.exercise else f"Упражнение #{self.exercise_id}"
        return f"{program_name}: день {self.day_number} — {exercise_name}"


class Goal(db.Model):
    """Цель по весу/телу, зависит от профиля пользователя."""

    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    goal_type = db.Column(db.String(64), nullable=False)  # "weight", "body_fat", "muscle", etc.
    current_value = db.Column(db.Float, nullable=False)
    target_value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(32), nullable=False)  # "кг", "%", etc.
    deadline = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    user = db.relationship("User", backref="goals")

    def __str__(self) -> str:
        return f"{self.goal_type}: {self.target_value} {self.unit}"


class ProgressLog(db.Model):
    """Логирование прогресса по целям (для календаря)."""

    __tablename__ = "progress_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey("goals.id"), nullable=True)
    log_date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref="progress_logs")
    goal = db.relationship("Goal", backref="logs")
