from datetime import datetime, timezone

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

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
    """플랫폼의 주요 현황을 관리자에게 보여준다."""
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
        "pending_reports": db.session.scalar(
            db.select(db.func.count(Report.id)).where(
                Report.status == "pending"
            )
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


@admin_bp.get("/users")
@admin_required
def users():
    """전체 사용자 목록을 보여준다."""
    user_list = db.session.scalars(
        db.select(User).order_by(
            User.created_at.desc(),
            User.id.desc(),
        )
    ).all()

    return render_template(
        "admin/users.html",
        users=user_list,
    )


@admin_bp.post("/users/<int:user_id>/status")
@admin_required
def update_user_status(user_id):
    """일반 사용자의 정상·휴면 상태를 변경한다."""
    target_user = db.get_or_404(User, user_id)
    new_status = request.form.get("status", "")

    if new_status not in {"active", "dormant"}:
        abort(400)

    # 관리자가 자기 계정을 휴면 처리하는 사고를 방지한다.
    if target_user.id == current_user.id:
        flash(
            "현재 로그인한 관리자 계정의 상태는 "
            "직접 변경할 수 없습니다.",
            "error",
        )
        return redirect(url_for("admin.users"))

    # 다른 관리자 계정도 이 화면에서 변경하지 못하게 한다.
    if target_user.is_admin:
        flash(
            "관리자 계정 상태는 이 화면에서 변경할 수 없습니다.",
            "error",
        )
        return redirect(url_for("admin.users"))

    try:
        target_user.status = new_status
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(
            "사용자 상태 변경 중 오류가 발생했습니다.",
            "error",
        )
    else:
        flash(
            f"{target_user.display_name}님의 계정 상태를 "
            f"{'정상' if new_status == 'active' else '휴면'}으로 "
            "변경했습니다.",
            "success",
        )

    return redirect(url_for("admin.users"))


@admin_bp.get("/products")
@admin_required
def products():
    """전체 상품 목록을 보여준다."""
    product_list = db.session.scalars(
        db.select(Product)
        .options(joinedload(Product.seller))
        .order_by(
            Product.created_at.desc(),
            Product.id.desc(),
        )
    ).all()

    return render_template(
        "admin/products.html",
        products=product_list,
    )


@admin_bp.post("/products/<int:product_id>/status")
@admin_required
def update_product_status(product_id):
    """관리자가 상품을 차단하거나 복구한다."""
    product = db.get_or_404(Product, product_id)
    new_status = request.form.get("status", "")

    # 관리자 화면에서는 차단 또는 판매 중 복구만 허용한다.
    if new_status not in {"available", "blocked"}:
        abort(400)

    try:
        product.status = new_status
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(
            "상품 상태 변경 중 오류가 발생했습니다.",
            "error",
        )
    else:
        flash(
            f"상품을 "
            f"{'판매 중으로 복구' if new_status == 'available' else '차단'}"
            "했습니다.",
            "success",
        )

    return redirect(url_for("admin.products"))


@admin_bp.get("/reports")
@admin_required
def reports():
    """신고 기록을 최신순으로 보여준다."""
    report_list = db.session.scalars(
        db.select(Report)
        .options(
            joinedload(Report.reporter),
            joinedload(Report.target_user),
            joinedload(Report.target_product),
        )
        .order_by(
            Report.created_at.desc(),
            Report.id.desc(),
        )
    ).unique().all()

    return render_template(
        "admin/reports.html",
        reports=report_list,
    )


@admin_bp.post("/reports/<int:report_id>/review")
@admin_required
def review_report(report_id):
    """신고를 처리 완료 또는 기각 상태로 변경한다."""
    report = db.get_or_404(Report, report_id)
    new_status = request.form.get("status", "")

    if new_status not in {"resolved", "dismissed"}:
        abort(400)

    if report.status != "pending":
        flash(
            "이미 검토가 끝난 신고입니다.",
            "error",
        )
        return redirect(url_for("admin.reports"))

    try:
        report.status = new_status
        report.reviewed_at = datetime.now(timezone.utc)

        # 조치 완료한 신고 대상은 확실하게 차단 상태로 둔다.
        if new_status == "resolved":
            if report.target_user is not None:
                # 관리자 계정은 신고 처리로 휴면 전환하지 않는다.
                if not report.target_user.is_admin:
                    report.target_user.status = "dormant"

            if report.target_product is not None:
                report.target_product.status = "blocked"

        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(
            "신고 검토 처리 중 오류가 발생했습니다.",
            "error",
        )
    else:
        flash(
            "신고를 "
            f"{'처리 완료' if new_status == 'resolved' else '기각'}"
            " 상태로 변경했습니다.",
            "success",
        )

    return redirect(url_for("admin.reports"))


@admin_bp.get("/activity")
@admin_required
def activity():
    """송금 내역과 채팅 기록을 관리자에게 보여준다."""
    transfers = db.session.scalars(
        db.select(Transfer)
        .options(
            joinedload(Transfer.sender),
            joinedload(Transfer.recipient),
        )
        .order_by(
            Transfer.created_at.desc(),
            Transfer.id.desc(),
        )
        .limit(200)
    ).all()

    messages = db.session.scalars(
        db.select(ChatMessage)
        .options(
            joinedload(ChatMessage.sender),
            joinedload(ChatMessage.recipient),
        )
        .order_by(
            ChatMessage.created_at.desc(),
            ChatMessage.id.desc(),
        )
        .limit(200)
    ).all()

    return render_template(
        "admin/activity.html",
        transfers=transfers,
        messages=messages,
    )


@admin_bp.post("/messages/<int:message_id>/delete")
@admin_required
def delete_message(message_id):
    """관리자가 부적절한 채팅 메시지를 삭제한다."""
    message = db.get_or_404(ChatMessage, message_id)

    try:
        db.session.delete(message)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(
            "메시지 삭제 중 오류가 발생했습니다.",
            "error",
        )
    else:
        flash(
            "채팅 메시지를 삭제했습니다.",
            "success",
        )

    return redirect(url_for("admin.activity"))