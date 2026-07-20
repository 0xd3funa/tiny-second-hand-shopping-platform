from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.chat import chat_bp
from app.chat.forms import MessageForm
from app.extensions import db, limiter
from app.models import ChatMessage, User


def recent_messages(statement):
    """최근 메시지 100개를 오래된 순서로 반환한다."""
    messages = db.session.scalars(
        statement
        .options(
            joinedload(ChatMessage.sender),
            joinedload(ChatMessage.recipient),
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(100)
    ).all()

    messages.reverse()
    return messages


@chat_bp.route("/public", methods=["GET", "POST"])
@login_required
@limiter.limit("30 per minute", methods=["POST"])
def public():
    form = MessageForm()

    if form.validate_on_submit():
        content = form.content.data.strip()

        if not content:
            form.content.errors.append(
                "공백만으로 된 메시지는 보낼 수 없습니다."
            )
        else:
            message = ChatMessage(
                sender_id=current_user.id,
                recipient_id=None,
                scope="public",
                content=content,
            )

            try:
                db.session.add(message)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash(
                    "메시지 저장 중 오류가 발생했습니다.",
                    "error",
                )
            else:
                return redirect(url_for("chat.public"))

    messages = recent_messages(
        db.select(ChatMessage).where(
            ChatMessage.scope == "public"
        )
    )

    return render_template(
        "chat/public.html",
        form=form,
        messages=messages,
    )


@chat_bp.route(
    "/direct/<int:user_id>",
    methods=["GET", "POST"],
)
@login_required
@limiter.limit("30 per minute", methods=["POST"])
def direct(user_id):
    other_user = db.session.scalar(
        db.select(User).where(
            User.id == user_id,
            User.status == "active",
        )
    )

    # 존재하지 않거나 휴면 상태인 사용자를 구분해 노출하지 않는다.
    if other_user is None:
        abort(404)

    if other_user.id == current_user.id:
        flash(
            "자기 자신과는 1:1 대화를 시작할 수 없습니다.",
            "error",
        )
        return redirect(url_for("chat.public"))

    form = MessageForm()

    if form.validate_on_submit():
        content = form.content.data.strip()

        if not content:
            form.content.errors.append(
                "공백만으로 된 메시지는 보낼 수 없습니다."
            )
        else:
            message = ChatMessage(
                sender_id=current_user.id,
                recipient_id=other_user.id,
                scope="direct",
                content=content,
            )

            try:
                db.session.add(message)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash(
                    "메시지 저장 중 오류가 발생했습니다.",
                    "error",
                )
            else:
                return redirect(
                    url_for(
                        "chat.direct",
                        user_id=other_user.id,
                    )
                )

    messages = recent_messages(
        db.select(ChatMessage).where(
            ChatMessage.scope == "direct",
            or_(
                and_(
                    ChatMessage.sender_id == current_user.id,
                    ChatMessage.recipient_id == other_user.id,
                ),
                and_(
                    ChatMessage.sender_id == other_user.id,
                    ChatMessage.recipient_id == current_user.id,
                ),
            ),
        )
    )

    return render_template(
        "chat/direct.html",
        form=form,
        messages=messages,
        other_user=other_user,
    )