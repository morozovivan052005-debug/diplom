from flask_wtf import FlaskForm
from wtforms import FloatField, HiddenField, IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange


class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6, max=128)])
    password2 = PasswordField(
        "Повтор пароля", validators=[DataRequired(), EqualTo("password", message="Пароли должны совпадать")]
    )
    submit = SubmitField("Зарегистрироваться")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class ProfileForm(FlaskForm):
    height_cm = FloatField("Рост (см)", validators=[DataRequired(), NumberRange(min=50, max=250)])
    weight_kg = FloatField("Вес (кг)", validators=[DataRequired(), NumberRange(min=20, max=400)])
    age_years = IntegerField("Возраст (лет)", validators=[DataRequired(), NumberRange(min=14, max=120)])
    gender = SelectField(
        "Пол",
        choices=[
            ("male", "Мужчина"),
            ("female", "Женщина"),
        ],
        validators=[DataRequired()],
    )
    activity_level = SelectField(
        "Уровень активности",
        choices=[
            ("sedentary", "Малоподвижный"),
            ("light", "Лёгкая нагрузка"),
            ("moderate", "Умеренная"),
            ("high", "Высокая"),
            ("very_high", "Очень высокая"),
        ],
        validators=[DataRequired()],
    )
    goal_code = SelectField(
        "Цель по весу / телу",
        choices=[
            ("lose_weight", "Снижение веса"),
            ("maintain", "Поддержание веса"),
            ("recomp", "Рекомпозиция (сила + лёгкий дефицит)"),
            ("gain_muscle", "Набор мышечной массы"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Сохранить профиль")


class ProgramSelectForm(FlaskForm):
    program_id = HiddenField("Программа", validators=[DataRequired()])
    submit = SubmitField("Выбрать программу")
