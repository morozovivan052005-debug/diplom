"""
Формула Миффлина — Сан Жеора (Mifflin–St Jeor) для базового метаболизма (BMR).

BMR (ккал/сутки):
- мужчины:  10×масса(кг) + 6.25×рост(см) − 5×возраст(лет) + 5
- женщины:  10×масса(кг) + 6.25×рост(см) − 5×возраст(лет) − 161

Источник: Mifflin MD et al., Am J Clin Nutr, 1990.
"""


def bmr_mifflin_st_jeor(
    weight_kg: float,
    height_cm: float,
    age_years: int,
    is_male: bool,
) -> float:
    if weight_kg <= 0 or height_cm <= 0 or age_years <= 0:
        raise ValueError("Вес, рост и возраст должны быть положительными")
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age_years
    return base + (5 if is_male else -161)


# Коэффициенты активности для оценки суточной энергии (TDEE) поверх BMR
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,  # малоподвижный
    "light": 1.375,  # лёгкая активность 1–3 дня
    "moderate": 1.55,  # умеренная 3–5 дней
    "high": 1.725,  # высокая 6–7 дней
    "very_high": 1.9,  # очень высокая / физ. труд
}


def tdee_from_bmr(bmr: float, activity_key: str) -> float:
    mult = ACTIVITY_MULTIPLIERS.get(activity_key)
    if mult is None:
        raise ValueError("Неизвестный уровень активности")
    return bmr * mult
