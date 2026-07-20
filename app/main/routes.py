from flask import render_template, request

from app.extensions import db
from app.main import main_bp
from app.models import Product


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