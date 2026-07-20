from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db, limiter
from app.models import Product, Report, User
from app.reports import reports_bp
from app.reports.forms import ReportForm


def product_report_count(product_id):
    return db.session.scalar(
        db.select(func.count(Report.id)).where(
            Report.target_product_id == product_id
        )
    ) or 0


def user_report_count(user_id):
    return db.session.scalar(
        db.select(func.count(Report.id)).where(
            Report.target_user_id == user_id
        )
    ) or 0


@reports_bp.route(
    "/products/<int:product_id>",
    methods=["GET", "POST"],
)
@login_required
@limiter.limit("10 per day", methods=["POST"])
def report_product(product_id):
    product = db.get_or_404(Product, product_id)

    if product.seller_id == current_user.id:
        flash(
            "자신이 등록한 상품은 신고할 수 없습니다.",
            "error",
        )
        return redirect(
            url_for(
                "products.detail",
                product_id=product.id,
            )
        )

    if product.status == "blocked":
        flash(
            "이미 안전 조치가 완료된 상품입니다.",
            "error",
        )
        return redirect(url_for("main.index"))

    existing_report = db.session.scalar(
        db.select(Report).where(
            Report.reporter_id == current_user.id,
            Report.target_product_id == product.id,
        )
    )

    if existing_report:
        flash(
            "이미 이 상품에 대한 안전 기록을 접수했습니다.",
            "error",
        )
        return redirect(
            url_for(
                "products.detail",
                product_id=product.id,
            )
        )

    form = ReportForm()

    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            target_product_id=product.id,
            reason=form.reason.data.strip(),
        )

        try:
            db.session.add(report)
            db.session.flush()

            count = product_report_count(product.id)

            if count >= current_app.config["REPORT_THRESHOLD"]:
                product.status = "blocked"

            db.session.commit()

        except IntegrityError:
            db.session.rollback()

            flash(
                "이미 접수된 신고이거나 처리할 수 없는 요청입니다.",
                "error",
            )
            return redirect(
                url_for(
                    "products.detail",
                    product_id=product.id,
                )
            )

        if product.status == "blocked":
            flash(
                "신고가 접수되었으며 해당 상품이 자동 차단되었습니다.",
                "success",
            )
            return redirect(url_for("main.index"))

        flash(
            "상품 안전 기록이 접수되었습니다.",
            "success",
        )
        return redirect(
            url_for(
                "products.detail",
                product_id=product.id,
            )
        )

    return render_template(
        "reports/create.html",
        form=form,
        target_type="상품",
        target_name=product.name,
        cancel_url=url_for(
            "products.detail",
            product_id=product.id,
        ),
    )


@reports_bp.route(
    "/users/<int:user_id>",
    methods=["GET", "POST"],
)
@login_required
@limiter.limit("10 per day", methods=["POST"])
def report_user(user_id):
    target_user = db.get_or_404(User, user_id)

    if target_user.id == current_user.id:
        flash(
            "자기 자신은 신고할 수 없습니다.",
            "error",
        )
        return redirect(
            url_for(
                "main.user_profile",
                user_id=target_user.id,
            )
        )

    if target_user.is_admin:
        flash(
            "관리자 계정은 이 신고 절차의 대상이 아닙니다.",
            "error",
        )
        return redirect(url_for("main.index"))

    if target_user.status == "dormant":
        flash(
            "이미 안전 조치가 완료된 사용자입니다.",
            "error",
        )
        return redirect(url_for("main.index"))

    existing_report = db.session.scalar(
        db.select(Report).where(
            Report.reporter_id == current_user.id,
            Report.target_user_id == target_user.id,
        )
    )

    if existing_report:
        flash(
            "이미 이 사용자에 대한 안전 기록을 접수했습니다.",
            "error",
        )
        return redirect(
            url_for(
                "main.user_profile",
                user_id=target_user.id,
            )
        )

    form = ReportForm()

    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            target_user_id=target_user.id,
            reason=form.reason.data.strip(),
        )

        try:
            db.session.add(report)
            db.session.flush()

            count = user_report_count(target_user.id)

            if count >= current_app.config["REPORT_THRESHOLD"]:
                target_user.status = "dormant"

            db.session.commit()

        except IntegrityError:
            db.session.rollback()

            flash(
                "이미 접수된 신고이거나 처리할 수 없는 요청입니다.",
                "error",
            )
            return redirect(
                url_for(
                    "main.user_profile",
                    user_id=target_user.id,
                )
            )

        if target_user.status == "dormant":
            flash(
                "신고가 접수되었으며 해당 계정이 자동 휴면 처리되었습니다.",
                "success",
            )
            return redirect(url_for("main.index"))

        flash(
            "사용자 안전 기록이 접수되었습니다.",
            "success",
        )
        return redirect(
            url_for(
                "main.user_profile",
                user_id=target_user.id,
            )
        )

    return render_template(
        "reports/create.html",
        form=form,
        target_type="사용자",
        target_name=target_user.display_name,
        cancel_url=url_for(
            "main.user_profile",
            user_id=target_user.id,
        ),
    )