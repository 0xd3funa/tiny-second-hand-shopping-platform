from flask import flash, redirect, render_template, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app.auth import auth_bp
from app.auth.forms import RegistrationForm
from app.extensions import db, limiter
from app.models import User


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip().lower(),
            display_name=form.display_name.data.strip(),
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash(
                "이미 사용 중인 아이디입니다.",
                "error",
            )
            return render_template(
                "auth/register.html",
                form=form,
            )

        flash(
            "회원가입이 완료되었습니다. 로그인해 주세요.",
            "success",
        )
        return redirect(url_for("main.index"))

    return render_template(
        "auth/register.html",
        form=form,
    )