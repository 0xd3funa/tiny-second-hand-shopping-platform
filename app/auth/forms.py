import re

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    EqualTo,
    Length,
    Regexp,
    ValidationError,
)

from app.extensions import db
from app.models import User


class RegistrationForm(FlaskForm):
    username = StringField(
        "아이디",
        validators=[
            DataRequired(message="아이디를 입력해 주세요."),
            Length(
                min=3,
                max=24,
                message="아이디는 3자 이상 24자 이하여야 합니다.",
            ),
            Regexp(
                r"^[A-Za-z0-9_]+$",
                message="아이디에는 영문, 숫자, 밑줄만 사용할 수 있습니다.",
            ),
        ],
    )

    display_name = StringField(
        "표시 이름",
        validators=[
            DataRequired(message="표시 이름을 입력해 주세요."),
            Length(
                min=2,
                max=40,
                message="표시 이름은 2자 이상 40자 이하여야 합니다.",
            ),
        ],
    )

    password = PasswordField(
        "비밀번호",
        validators=[
            DataRequired(message="비밀번호를 입력해 주세요."),
            Length(
                min=10,
                max=128,
                message="비밀번호는 10자 이상 128자 이하여야 합니다.",
            ),
        ],
    )

    password_confirm = PasswordField(
        "비밀번호 확인",
        validators=[
            DataRequired(message="비밀번호를 다시 입력해 주세요."),
            EqualTo(
                "password",
                message="비밀번호가 일치하지 않습니다.",
            ),
        ],
    )

    submit = SubmitField("회원가입")

    def validate_username(self, field):
        normalized_username = field.data.strip().lower()

        existing_user = db.session.scalar(
            db.select(User).where(
                User.username == normalized_username
            )
        )

        if existing_user:
            raise ValidationError("이미 사용 중인 아이디입니다.")

    def validate_password(self, field):
        password = field.data

        if not re.search(r"[A-Za-z]", password):
            raise ValidationError(
                "비밀번호에는 영문자가 하나 이상 필요합니다."
            )

        if not re.search(r"\d", password):
            raise ValidationError(
                "비밀번호에는 숫자가 하나 이상 필요합니다."
            )