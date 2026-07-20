from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class TransferForm(FlaskForm):
    recipient_username = StringField(
        "받는 사람 아이디",
        validators=[
            DataRequired(
                message="받는 사람의 아이디를 입력해 주세요."
            ),
            Length(
                min=3,
                max=24,
                message="올바른 아이디를 입력해 주세요.",
            ),
        ],
    )

    amount = IntegerField(
        "보낼 금액",
        validators=[
            DataRequired(message="보낼 금액을 입력해 주세요."),
            NumberRange(
                min=1,
                max=1_000_000,
                message="송금액은 1원 이상 100만원 이하여야 합니다.",
            ),
        ],
    )

    memo = StringField(
        "메모",
        validators=[
            Length(
                max=100,
                message="메모는 100자 이하로 입력해 주세요.",
            ),
        ],
    )

    submit = SubmitField("안전하게 보내기")