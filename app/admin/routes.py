from flask import render_template

from app.admin import admin_bp
from app.admin.decorators import admin_required
from app.extensions import db
from app.models import (
    ChatMessage,
    Product,
    Report,
    Transfer,
    User,
)


@admin_bp.get("/")
@admin_required
def dashboard():
    """플랫폼의 주요 현황을 관리자에게만 보여준다."""
    statistics = {
        "users": db.session.scalar(
            db.select(db.func.count(User.id))
        ),
        "active_users": db.session.scalar(
            db.select(db.func.count(User.id)).where(
                User.status == "active"
            )
        ),
        "dormant_users": db.session.scalar(
            db.select(db.func.count(User.id)).where(
                User.status == "dormant"
            )
        ),
        "products": db.session.scalar(
            db.select(db.func.count(Product.id))
        ),
        "blocked_products": db.session.scalar(
            db.select(db.func.count(Product.id)).where(
                Product.status == "blocked"
            )
        ),
        "reports": db.session.scalar(
            db.select(db.func.count(Report.id))
        ),
        "transfers": db.session.scalar(
            db.select(db.func.count(Transfer.id))
        ),
        "chat_messages": db.session.scalar(
            db.select(db.func.count(ChatMessage.id))
        ),
    }

    return render_template(
        "admin/dashboard.html",
        statistics=statistics,
    )