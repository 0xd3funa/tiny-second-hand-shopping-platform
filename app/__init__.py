from pathlib import Path

from flask import Flask

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
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY 환경변수가 설정되지 않았습니다.")

    # SQLite 데이터베이스가 저장될 폴더를 생성한다.
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(
    parents=True,
    exist_ok=True,
)
    # Flask 확장 기능을 현재 앱에 연결한다.
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "로그인이 필요한 기능입니다."
    login_manager.login_message_category = "error"
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    socketio.init_app(app)

    # 메인 페이지 Blueprint를 등록한다.
    from app.auth import auth_bp
    from app.main import main_bp
    from app.products import products_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
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