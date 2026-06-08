"""
Персонализированные ориентиры по питанию (на базе TDEE) и ИМТ.
Не заменяют консультацию врача/диетолога — для учебного проекта.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def bmi(weight_kg: float, height_cm: float) -> float:
    h_m = height_cm / 100.0
    if h_m <= 0:
        raise ValueError("Некорректный рост")
    return round(weight_kg / (h_m * h_m), 1)


def bmi_category_ru(bmi_value: float) -> str:
    if bmi_value < 18.5:
        return "Недостаточная масса тела"
    if bmi_value < 25:
        return "Нормальный вес"
    if bmi_value < 30:
        return "Избыточная масса тела"
    return "Ожирение"


@dataclass
class CaloriePlan:
    target_min_kcal: int
    target_max_kcal: int
    headline: str
    bullets: list[str]


def calorie_plan_for_goal(tdee: float, goal_code: str | None) -> CaloriePlan:
    code = (goal_code or "maintain").strip().lower()
    if code == "lose_weight":
        return CaloriePlan(
            target_min_kcal=int(round(tdee * 0.75)),
            target_max_kcal=int(round(tdee * 0.85)),
            headline="Снижение веса: умеренный дефицит калорий",
            bullets=[
                "Ориентир: примерно −15…25% от TDEE (без крайностей).",
                "Белок держите достаточным (продукты с высоким содержанием белка в каждом приёме пищи).",
                "Сочетайте дефицит с силовыми тренировками, чтобы сохранять мышечную массу.",
            ],
        )
    if code == "recomp":
        return CaloriePlan(
            target_min_kcal=int(round(tdee * 0.90)),
            target_max_kcal=int(round(tdee * 0.98)),
            headline="Рекомпозиция: лёгкий дефицит при упоре на силу",
            bullets=[
                "Небольшой дефицит + прогрессия нагрузок в зале.",
                "Контролируйте восстановление и сон — они влияют на голод и прогресс.",
            ],
        )
    if code == "gain_muscle":
        return CaloriePlan(
            target_min_kcal=int(round(tdee * 1.08)),
            target_max_kcal=int(round(tdee * 1.15)),
            headline="Набор массы: небольшой профицит",
            bullets=[
                "Профицит около +8…15% к TDEE — типичный ориентир для набора с минимумом жира.",
                "Прогрессируйте рабочие веса/объём, следите за техникой.",
            ],
        )
    return CaloriePlan(
        target_min_kcal=int(round(tdee - 100)),
        target_max_kcal=int(round(tdee + 100)),
        headline="Поддержание веса: калорийность около TDEE",
        bullets=[
            "Держитесь в узком коридоре вокруг расчётной нормы, корректируя по динамике веса 2–4 недели.",
            "Поддерживайте регулярность тренировок под ваш уровень активности.",
        ],
    )


def build_summary(
    *,
    bmi_value: float,
    bmr: float,
    tdee: float,
    goal_code: str | None,
) -> dict[str, Any]:
    plan = calorie_plan_for_goal(tdee, goal_code)
    return {
        "bmi": bmi_value,
        "bmi_category": bmi_category_ru(bmi_value),
        "bmr": bmr,
        "tdee": tdee,
        "plan": plan,
    }
