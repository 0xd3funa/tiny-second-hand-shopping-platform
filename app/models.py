from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    __table_args__ = (
        db.CheckConstraint(
            "role IN ('user', 'admin')",
            name="ck_users_role",
        ),
        db.CheckConstraint(
            "status IN ('active', 'dormant')",
            name="ck_users_status",
        ),
        db.CheckConstraint(
            "balance >= 0",
            name="ck_users_balance_nonnegative",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    # NOCASE를 적용하여 Euna와 euna를 같은 아이디로 취급한다.
    username = db.Column(
        db.String(24, collation="NOCASE"),
        unique=True,
        nullable=False,
        index=True,
    )

    display_name = db.Column(
        db.String(40),
        nullable=False,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    bio = db.Column(
        db.String(300),
        nullable=False,
        default="",
    )

    role = db.Column(
        db.String(10),
        nullable=False,
        default="user",
    )

    status = db.Column(
        db.String(10),
        nullable=False,
        default="active",
    )

    balance = db.Column(
        db.Integer,
        nullable=False,
        default=100_000,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def set_password(self, password):
        """비밀번호 원문 대신 scrypt 해시를 저장한다."""
        if not isinstance(password, str):
            raise TypeError("비밀번호는 문자열이어야 합니다.")

        if not 10 <= len(password) <= 128:
            raise ValueError("비밀번호는 10자 이상 128자 이하여야 합니다.")

        self.password_hash = generate_password_hash(
            password,
            method="scrypt",
        )

    def check_password(self, password):
        """입력한 비밀번호가 저장된 해시와 일치하는지 확인한다."""
        if not isinstance(password, str):
            return False

        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        """휴면 사용자는 Flask-Login에서 활성 사용자로 처리하지 않는다."""
        return self.status == "active"

    @property
    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User id={self.id} username={self.username!r}>"