"""
Создание первого администратора (пользователи в админке не создаются без пароля — только через этот скрипт или регистрацию).

Пример:
  python create_admin.py admin@example.com ваш_надежный_пароль
"""
import sys

from app import create_app, db
from app.models import User


def main():
    if len(sys.argv) < 3:
        print("Использование: python create_admin.py <email> <пароль>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    password = sys.argv[2]

    app = create_app()
    with app.app_context():
        if User.query.filter_by(email=email).first():
            print("Пользователь с таким email уже существует.")
            sys.exit(1)

        user = User(email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Администратор {email} создан. Войдите и откройте /admin")


if __name__ == "__main__":
    main()
