from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange


class ProductCreateForm(FlaskForm):
    name = StringField(
        "상품명",
        validators=[
            DataRequired(message="상품명을 입력해 주세요."),
            Length(
                min=2,
                max=100,
                message="상품명은 2자 이상 100자 이하여야 합니다.",
            ),
        ],
    )

    description = TextAreaField(
        "상품 설명",
        validators=[
            DataRequired(message="상품 설명을 입력해 주세요."),
            Length(
                min=5,
                max=1000,
                message="상품 설명은 5자 이상 1000자 이하여야 합니다.",
            ),
        ],
    )

    price = IntegerField(
        "가격",
        validators=[
            DataRequired(message="가격을 입력해 주세요."),
            NumberRange(
                min=0,
                max=100_000_000,
                message="가격은 0원 이상 1억원 이하여야 합니다.",
            ),
        ],
    )

    image = FileField(
        "상품 사진",
        validators=[
            FileRequired(message="상품 사진을 선택해 주세요."),
            FileAllowed(
                ["jpg", "jpeg", "png", "webp"],
                message="JPG, PNG 또는 WebP 이미지만 업로드할 수 있습니다.",
            ),
        ],
    )

    submit = SubmitField("상품 등록")