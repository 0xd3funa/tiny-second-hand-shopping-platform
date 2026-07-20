from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_, update
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db, limiter
from app.models import Transfer, User
from app.transfers import transfers_bp
from app.transfers.forms import TransferForm


@transfers_bp.route("/new", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per hour", methods=["POST"])
def create():
    form = TransferForm()

    if form.validate_on_submit():
        recipient_username = (
            form.recipient_username.data.strip().lower()
        )
        amount = form.amount.data
        memo = (form.memo.data or "").strip()

        recipient = db.session.scalar(
            db.select(User).where(
                User.username == recipient_username,
                User.status == "active",
            )
        )

        # 존재 여부와 휴면 여부를 구분해서 노출하지 않는다.
        if recipient is None:
            form.recipient_username.errors.append(
                "송금할 수 없는 사용자입니다."
            )
            return render_template(
                "transfers/create.html",
                form=form,
            )

        if recipient.id == current_user.id:
            form.recipient_username.errors.append(
                "자기 자신에게는 송금할 수 없습니다."
            )
            return render_template(
                "transfers/create.html",
                form=form,
            )

        try:
            # 잔액이 충분할 때만 한 번의 UPDATE로 차감한다.
            debit_result = db.session.execute(
                update(User)
                .where(
                    User.id == current_user.id,
                    User.status == "active",
                    User.balance >= amount,
                )
                .values(
                    balance=User.balance - amount,
                )
                .execution_options(
                    synchronize_session=False,
                )
            )

            if debit_result.rowcount != 1:
                db.session.rollback()
                form.amount.errors.append(
                    "잔액이 부족하거나 송금할 수 없는 상태입니다."
                )
                return render_template(
                    "transfers/create.html",
                    form=form,
                )

            # 받는 사용자가 처리 도중 휴면 상태가 된 경우도 막는다.
            credit_result = db.session.execute(
                update(User)
                .where(
                    User.id == recipient.id,
                    User.status == "active",
                )
                .values(
                    balance=User.balance + amount,
                )
                .execution_options(
                    synchronize_session=False,
                )
            )

            if credit_result.rowcount != 1:
                db.session.rollback()
                form.recipient_username.errors.append(
                    "송금할 수 없는 사용자입니다."
                )
                return render_template(
                    "transfers/create.html",
                    form=form,
                )

            transfer = Transfer(
                sender_id=current_user.id,
                recipient_id=recipient.id,
                amount=amount,
                memo=memo,
            )

            db.session.add(transfer)
            db.session.commit()

        except SQLAlchemyError:
            db.session.rollback()
            flash(
                "송금 처리 중 오류가 발생했습니다. "
                "잔액은 변경되지 않았습니다.",
                "error",
            )
            return render_template(
                "transfers/create.html",
                form=form,
            )

        flash(
            f"{recipient.display_name}님에게 "
            f"{amount:,}원을 보냈습니다.",
            "success",
        )
        return redirect(url_for("transfers.history"))

    return render_template(
        "transfers/create.html",
        form=form,
    )


@transfers_bp.get("/history")
@login_required
def history():
    transfers = db.session.scalars(
        db.select(Transfer)
        .where(
            or_(
                Transfer.sender_id == current_user.id,
                Transfer.recipient_id == current_user.id,
            )
        )
        .order_by(Transfer.created_at.desc())
        .limit(100)
    ).all()

    return render_template(
        "transfers/history.html",
        transfers=transfers,
    )