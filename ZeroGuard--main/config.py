import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:

    SECRET_KEY = os.getenv("SECRET_KEY", "crimeshield-dev-secret-change-in-prod")

    # JWT settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "crimeshield-jwt-secret-change-in-prod")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///cybercrime.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "session_uploads")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024