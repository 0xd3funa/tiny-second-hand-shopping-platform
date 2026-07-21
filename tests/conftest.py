import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app(tmp_path):
    database_path = tmp_path / "test.db"
    upload_path = tmp_path / "uploads"

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "SQLALCHEMY_DATABASE_URI": (
                f"sqlite:///{database_path}"
            ),
            "UPLOAD_FOLDER": str(upload_path),
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        }
    )

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()