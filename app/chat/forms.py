from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class MessageForm(FlaskForm):
    content = TextAreaField(
        "메시지",
        validators=[
            DataRequired(
                message="메시지를 입력해 주세요."
            ),
            Length(
                min=1,
                max=500,
                message="메시지는 500자 이하로 입력해 주세요.",
            ),
        ],
    )

    submit = SubmitField("기록 남기기")