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
from app.products.forms import (
    ProductCreateForm,
    ProductDeleteForm,
    ProductEditForm,
)
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


def get_manageable_product_or_404(product_id):
    """상품을 조회하고 수정·삭제 권한을 확인한다."""
    product = db.get_or_404(Product, product_id)

    if (
        current_user.id != product.seller_id
        and not current_user.is_admin
    ):
        abort(403)

    # 신고로 차단된 상품은 판매자가 임의로 다시 활성화할 수 없다.
    if product.status == "blocked" and not current_user.is_admin:
        abort(403)

    return product


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


@products_bp.get("/mine")
@login_required
def mine():
    products = db.session.scalars(
        db.select(Product)
        .where(Product.seller_id == current_user.id)
        .order_by(Product.created_at.desc())
    ).all()

    return render_template(
        "products/mine.html",
        products=products,
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


@products_bp.route(
    "/<int:product_id>/edit",
    methods=["GET", "POST"],
)
@login_required
def edit(product_id):
    product = get_manageable_product_or_404(product_id)
    form = ProductEditForm(obj=product)

    if form.validate_on_submit():
        old_image_filename = product.image_filename
        new_image_filename = None

        if form.image.data:
            try:
                new_image_filename = save_product_image(
                    form.image.data,
                    current_app.config["UPLOAD_FOLDER"],
                )
            except InvalidImageError as error:
                form.image.errors.append(str(error))

                return render_template(
                    "products/edit.html",
                    form=form,
                    product=product,
                )

        product.name = form.name.data.strip()
        product.description = form.description.data.strip()
        product.price = form.price.data
        product.status = form.status.data

        if new_image_filename:
            product.image_filename = new_image_filename

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()

            # DB 수정 실패 시 새로 만든 이미지만 제거한다.
            if new_image_filename:
                delete_product_image(
                    new_image_filename,
                    current_app.config["UPLOAD_FOLDER"],
                )

            flash(
                "상품 수정 중 오류가 발생했습니다.",
                "error",
            )
            return render_template(
                "products/edit.html",
                form=form,
                product=product,
            )

        # DB 수정 성공 후 이전 이미지를 제거한다.
        if new_image_filename:
            delete_product_image(
                old_image_filename,
                current_app.config["UPLOAD_FOLDER"],
            )

        flash(
            "상품이 수정되었습니다.",
            "success",
        )
        return redirect(
            url_for(
                "products.detail",
                product_id=product.id,
            )
        )

    return render_template(
        "products/edit.html",
        form=form,
        product=product,
    )


@products_bp.post("/<int:product_id>/delete")
@login_required
def delete(product_id):
    product = get_manageable_product_or_404(product_id)
    form = ProductDeleteForm()

    if not form.validate_on_submit():
        abort(400)

    product_id_for_redirect = product.id
    image_filename = product.image_filename

    try:
        db.session.delete(product)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()

        flash(
            "상품 삭제 중 오류가 발생했습니다.",
            "error",
        )
        return redirect(
            url_for(
                "products.detail",
                product_id=product_id_for_redirect,
            )
        )

    # DB에서 상품을 삭제한 후 이미지 파일을 제거한다.
    delete_product_image(
        image_filename,
        current_app.config["UPLOAD_FOLDER"],
    )

    flash(
        "상품이 삭제되었습니다.",
        "success",
    )
    return redirect(url_for("products.mine"))