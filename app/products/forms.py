from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange,
    Optional,
)


IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
IMAGE_ERROR_MESSAGE = (
    "JPG, PNG 또는 WebP 이미지만 업로드할 수 있습니다."
)


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
            InputRequired(message="가격을 입력해 주세요."),
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
                IMAGE_EXTENSIONS,
                message=IMAGE_ERROR_MESSAGE,
            ),
        ],
    )

    submit = SubmitField("상품 등록")


class ProductEditForm(FlaskForm):
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
            InputRequired(message="가격을 입력해 주세요."),
            NumberRange(
                min=0,
                max=100_000_000,
                message="가격은 0원 이상 1억원 이하여야 합니다.",
            ),
        ],
    )

    status = SelectField(
        "판매 상태",
        choices=[
            ("available", "판매 중"),
            ("reserved", "예약 중"),
            ("sold", "판매 완료"),
        ],
        validators=[
            DataRequired(message="판매 상태를 선택해 주세요."),
        ],
    )

    image = FileField(
        "새 상품 사진",
        validators=[
            Optional(),
            FileAllowed(
                IMAGE_EXTENSIONS,
                message=IMAGE_ERROR_MESSAGE,
            ),
        ],
    )

    submit = SubmitField("상품 수정")


class ProductDeleteForm(FlaskForm):
    submit = SubmitField("상품 삭제")