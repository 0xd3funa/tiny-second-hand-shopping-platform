from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class ReportForm(FlaskForm):
    reason = TextAreaField(
        "신고 사유",
        validators=[
            DataRequired(message="신고 사유를 입력해 주세요."),
            Length(
                min=10,
                max=500,
                message="신고 사유는 10자 이상 500자 이하여야 합니다.",
            ),
        ],
    )

    submit = SubmitField("안전 기록 접수")