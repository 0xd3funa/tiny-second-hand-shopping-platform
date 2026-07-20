from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db, limiter
from app.models import Product
from app.products import products_bp
from app.products.forms import ProductCreateForm
from app.products.utils import (
    InvalidImageError,
    delete_product_image,
    save_product_image,
)


def can_view_product(product):
    """차단 상품은 판매자와 관리자만 조회할 수 있다."""
    if product.status != "blocked":
        return True

    return (
        current_user.is_authenticated
        and (
            current_user.id == product.seller_id
            or current_user.is_admin
        )
    )


@products_bp.route("/new", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per hour", methods=["POST"])
def create():
    form = ProductCreateForm()

    if form.validate_on_submit():
        try:
            image_filename = save_product_image(
                form.image.data,
                current_app.config["UPLOAD_FOLDER"],
            )
        except InvalidImageError as error:
            form.image.errors.append(str(error))

            return render_template(
                "products/create.html",
                form=form,
            )

        product = Product(
            seller_id=current_user.id,
            name=form.name.data.strip(),
            description=form.description.data.strip(),
            price=form.price.data,
            image_filename=image_filename,
            status="available",
        )

        try:
            db.session.add(product)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()

            # DB 저장 실패 시 먼저 저장한 고아 이미지도 삭제한다.
            delete_product_image(
                image_filename,
                current_app.config["UPLOAD_FOLDER"],
            )

            flash(
                "상품 저장 중 오류가 발생했습니다.",
                "error",
            )
            return render_template(
                "products/create.html",
                form=form,
            )

        flash(
            "상품이 등록되었습니다.",
            "success",
        )
        return redirect(
            url_for(
                "products.detail",
                product_id=product.id,
            )
        )

    return render_template(
        "products/create.html",
        form=form,
    )


@products_bp.get("/<int:product_id>")
def detail(product_id):
    product = db.get_or_404(Product, product_id)

    if not can_view_product(product):
        abort(404)

    return render_template(
        "products/detail.html",
        product=product,
    )


@products_bp.get("/images/<string:filename>")
def image(filename):
    product = db.session.scalar(
        db.select(Product).where(
            Product.image_filename == filename
        )
    )

    if product is None or not can_view_product(product):
        abort(404)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        filename,
        mimetype="image/jpeg",
        max_age=86_400,
    )