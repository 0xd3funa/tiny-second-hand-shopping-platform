from flask import abort, render_template, request
from flask_login import current_user

from app.extensions import db
from app.main import main_bp
from app.models import Product, User


@main_bp.get("/")
def index():
    query = request.args.get("q", "").strip()[:100]
    page = request.args.get("page", 1, type=int) or 1
    page = max(page, 1)

    statement = (
        db.select(Product)
        .where(Product.status != "blocked")
        .order_by(Product.created_at.desc())
    )

    if query:
        statement = statement.where(
            Product.name.contains(
                query,
                autoescape=True,
            )
        )

    pagination = db.paginate(
        statement,
        page=page,
        per_page=12,
        max_per_page=24,
        error_out=False,
    )

    return render_template(
        "index.html",
        products=pagination.items,
        pagination=pagination,
        query=query,
    )

@main_bp.get("/users/<int:user_id>")
def user_profile(user_id):
    user = db.get_or_404(User, user_id)

    can_view_dormant_user = (
        current_user.is_authenticated
        and (
            current_user.id == user.id
            or current_user.is_admin
        )
    )

    if user.status == "dormant" and not can_view_dormant_user:
        abort(404)

    products = db.session.scalars(
        db.select(Product)
        .where(
            Product.seller_id == user.id,
            Product.status != "blocked",
        )
        .order_by(Product.created_at.desc())
    ).all()

    return render_template(
        "users/profile.html",
        profile_user=user,
        products=products,
    )