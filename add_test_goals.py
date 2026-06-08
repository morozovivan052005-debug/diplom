"""
Скрипт для создания тестовых целей и логирования прогресса
Используется как: flask shell < add_test_goals.py
"""

from datetime import datetime, timedelta, date
from app import db
from app.models import User, Goal, ProgressLog

def create_test_goals():
    """Создаёт тестовые цели для первого пользователя."""
    
    # Получаем первого пользователя (обычно admin)
    user = User.query.first()
    
    if not user:
        print("❌ Пользователей не найдено. Сначала создайте пользователя.")
        return
    
    print(f"✓ Найден пользователь: {user.email}")
    
    # Удаляем старые цели и логирование этого пользователя
    Goal.query.filter_by(user_id=user.id).delete()
    ProgressLog.query.filter_by(user_id=user.id).delete()
    print("✓ Удалены старые цели и логирование")
    
    # Создаём цели
    goals = [
        Goal(
            user_id=user.id,
            goal_type="weight",
            current_value=80.0,
            target_value=75.0,
            unit="кг",
            deadline=datetime.now() + timedelta(days=60),
            notes="Снижение веса для улучшения здоровья"
        ),
        Goal(
            user_id=user.id,
            goal_type="body_fat",
            current_value=25.0,
            target_value=20.0,
            unit="%",
            deadline=datetime.now() + timedelta(days=90),
            notes="Снижение процента жира в организме"
        ),
        Goal(
            user_id=user.id,
            goal_type="muscle",
            current_value=65.0,
            target_value=70.0,
            unit="кг",
            deadline=datetime.now() + timedelta(days=120),
            notes="Набор мышечной массы"
        ),
    ]
    
    db.session.add_all(goals)
    db.session.commit()
    
    print(f"✓ Созданы {len(goals)} целей")
    
    # Создаём тестовое логирование (последние 30 дней)
    logs = []
    today = date.today()
    
    for goal in goals:
        for days_ago in range(0, 30, 3):  # Каждые 3 дня
            log_date = today - timedelta(days=days_ago)
            
            # Генерируем прогрессивное значение
            progress_ratio = (30 - days_ago) / 30
            if goal.goal_type == "weight":
                value = goal.target_value + (goal.current_value - goal.target_value) * (1 - progress_ratio * 0.7)
            else:
                value = goal.current_value + (goal.target_value - goal.current_value) * (progress_ratio * 0.7)
            
            log = ProgressLog(
                user_id=user.id,
                goal_id=goal.id,
                log_date=log_date,
                value=round(value, 1),
                notes=f"Запись от {log_date.strftime('%d.%m.%Y')}"
            )
            logs.append(log)
    
    db.session.add_all(logs)
    db.session.commit()
    
    print(f"✓ Добавлено {len(logs)} записей логирования")
    print("\n✅ Готово! Теперь перейдите в календарь для просмотра прогресса:")
    print("   http://localhost:5000/calendar")

if __name__ == "__main__":
    create_test_goals()
