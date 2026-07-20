from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError


ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_PIXELS = 20_000_000
OUTPUT_MAX_SIZE = (1600, 1600)


class InvalidImageError(ValueError):
    """유효하지 않거나 허용되지 않은 이미지 오류."""


def save_product_image(file_storage, upload_folder):
    """
    업로드된 이미지를 검사하고 메타데이터를 제거한 JPEG로 저장한다.

    반환값은 서버가 생성한 파일명이다.
    """
    upload_path = Path(upload_folder)
    upload_path.mkdir(parents=True, exist_ok=True)

    previous_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

    try:
        file_storage.stream.seek(0)

        with Image.open(file_storage.stream) as image:
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise InvalidImageError(
                    "허용되지 않은 이미지 형식입니다."
                )

            # 픽셀 데이터 전체를 읽어 손상 여부를 확인한다.
            image.load()

            # 휴대전화 EXIF 방향 정보를 실제 이미지 방향에 반영한다.
            image = ImageOps.exif_transpose(image)

            # 위치정보 등 기존 메타데이터가 복사되지 않도록 새 이미지로 만든다.
            if image.mode in ("RGBA", "LA"):
                background = Image.new(
                    "RGB",
                    image.size,
                    color="white",
                )
                alpha = image.getchannel("A")
                background.paste(image, mask=alpha)
                image = background
            else:
                image = image.convert("RGB")

            image.thumbnail(OUTPUT_MAX_SIZE)

            clean_image = Image.new(
                "RGB",
                image.size,
                color="white",
            )
            clean_image.paste(image)

            filename = f"{uuid4().hex}.jpg"
            destination = upload_path / filename

            clean_image.save(
                destination,
                format="JPEG",
                quality=85,
                optimize=True,
            )

            return filename

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ) as error:
        raise InvalidImageError(
            "정상적인 이미지 파일이 아닙니다."
        ) from error

    finally:
        Image.MAX_IMAGE_PIXELS = previous_limit
        file_storage.stream.seek(0)


def delete_product_image(filename, upload_folder):
    """서버에서 생성한 상품 이미지 파일을 삭제한다."""
    if not filename:
        return

    # DB에는 UUID 기반의 파일명만 저장하지만 한 번 더 형식을 검사한다.
    path = Path(filename)

    if (
        path.name != filename
        or path.suffix.lower() != ".jpg"
        or len(path.stem) != 32
        or not all(character in "0123456789abcdef" for character in path.stem)
    ):
        return

    image_path = Path(upload_folder) / filename

    try:
        image_path.unlink()
    except FileNotFoundError:
        pass