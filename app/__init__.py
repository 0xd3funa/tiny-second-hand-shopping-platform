from datetime import timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, flash, redirect, session, url_for
from flask_login import current_user, logout_user

from app.extensions import (
    csrf,
    db,
    limiter,
    login_manager,
    migrate,
    socketio,
)
from app.models import User
from config import Config


@login_manager.user_loader
def load_user(user_id):
    """세션에 저장된 사용자 ID로 사용자를 조회한다."""
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


def create_app(test_config=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY 환경변수가 설정되지 않았습니다."
        )

    # SQLite 데이터베이스가 저장될 폴더를 생성한다.
    Path(app.instance_path).mkdir(
        parents=True,
        exist_ok=True,
    )

    # 상품 이미지가 저장될 폴더를 생성한다.
    Path(app.config["UPLOAD_FOLDER"]).mkdir(
        parents=True,
        exist_ok=True,
    )

    # Flask 확장 기능을 현재 앱에 연결한다.
    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = (
        "로그인이 필요한 기능입니다."
    )
    login_manager.login_message_category = "error"

    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

    # 각 기능의 Blueprint를 등록한다.
    from app.admin import admin_bp
    from app.auth import auth_bp
    from app.chat import chat_bp
    from app.main import main_bp
    from app.products import products_bp
    from app.reports import reports_bp
    from app.transfers import transfers_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(transfers_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    
    @app.before_request
    def enforce_active_account():
        """휴면 계정의 기존 로그인 세션도 강제로 종료한다."""
        if (
            current_user.is_authenticated
            and current_user.status != "active"
        ):
            logout_user()
            session.clear()

            flash(
                "안전 조치로 계정 이용이 중지되었습니다.",
                "error",
            )
            return redirect(url_for("auth.login"))

        return None

    @app.template_filter("kst_datetime")
    def kst_datetime(
        value,
        format_string="%Y-%m-%d %H:%M",
    ):
        """DB에 저장된 UTC 시간을 한국 시간으로 표시한다."""
        if value is None:
            return ""

        # SQLite가 시간대 정보 없이 반환한 값은 UTC로 해석한다.
        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc,
            )

        korea_time = value.astimezone(
            ZoneInfo("Asia/Seoul")
        )

        return korea_time.strftime(format_string)

    @app.after_request
    def add_security_headers(response):
        """브라우저의 기본적인 보안 정책을 응답에 추가한다."""
        response.headers["X-Content-Type-Options"] = (
            "nosniff"
        )
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = (
            "strict-origin-when-cross-origin"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self'; "
            "script-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )

        return response

    return app