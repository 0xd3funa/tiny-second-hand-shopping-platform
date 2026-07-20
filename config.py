import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{BASE_DIR / 'instance' / 'tinyshop.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = BASE_DIR / "uploads"

    # 요청 전체 크기를 5MB로 제한한다.
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # JavaScript에서 세션 쿠키를 읽지 못하게 한다.
    SESSION_COOKIE_HTTPONLY = True

    # 외부 사이트에서 시작된 요청의 쿠키 전송을 제한한다.
    SESSION_COOKIE_SAMESITE = "Lax"

    REPORT_THRESHOLD = 3
    
    # HTTPS 배포환경에서는 반드시 true로 변경한다.
    SESSION_COOKIE_SECURE = (
        os.environ.get("COOKIE_SECURE", "false").lower() == "true"
    )
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)