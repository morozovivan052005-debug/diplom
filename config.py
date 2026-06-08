import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-change-in-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        "postgresql://postgres:postgres@localhost:5432/fit_recommendations"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
