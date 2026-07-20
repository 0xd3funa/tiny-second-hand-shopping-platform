from urllib.parse import urlsplit

from flask import (
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy.exc import IntegrityError

from app.auth import auth_bp
from app.auth.forms import (
    ChangePasswordForm,
    LoginForm,
    LogoutForm,
    ProfileForm,
    RegistrationForm,
)
from app.extensions import db, limiter
from app.models import User


def is_safe_redirect_target(target):
    """외부 사이트로 이동시키는 Open Redirect를 방지한다."""
    if not target:
        return False

    parsed = urlsplit(target)

    return (
        not parsed.scheme
        and not parsed.netloc
        and target.startswith("/")
        and not target.startswith("//")
        and "\\" not in target
    )


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
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
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/register.html",
        form=form,
    )


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data.strip().lower()

        user = db.session.scalar(
            db.select(User).where(
                User.username == username
            )
        )

        valid_login = (
            user is not None
            and user.check_password(form.password.data)
            and user.status == "active"
        )

        if not valid_login:
            flash(
                "아이디 또는 비밀번호가 올바르지 않거나 "
                "이용할 수 없는 계정입니다.",
                "error",
            )
            return render_template(
                "auth/login.html",
                form=form,
            )

        # 기존 세션 데이터를 제거한 후 새로운 로그인 상태를 만든다.
        session.clear()
        login_user(user, fresh=True)
        session.permanent = True

        next_url = request.args.get("next")

        flash(
            f"{user.display_name}님, 환영합니다.",
            "success",
        )

        if is_safe_redirect_target(next_url):
            return redirect(next_url)

        return redirect(url_for("main.index"))

    return render_template(
        "auth/login.html",
        form=form,
    )


@auth_bp.post("/logout")
@login_required
def logout():
    form = LogoutForm()

    if not form.validate_on_submit():
        flash(
            "올바르지 않은 요청입니다.",
            "error",
        )
        return redirect(url_for("main.index"))

    logout_user()
    session.clear()

    flash(
        "안전하게 로그아웃되었습니다.",
        "success",
    )
    return redirect(url_for("main.index"))
@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.display_name = form.display_name.data.strip()
        current_user.bio = (form.bio.data or "").strip()

        db.session.commit()

        flash(
            "프로필이 수정되었습니다.",
            "success",
        )
        return redirect(url_for("auth.profile"))

    return render_template(
        "auth/profile.html",
        form=form,
    )


@auth_bp.route("/password", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per hour", methods=["POST"])
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(
            form.current_password.data
        ):
            flash(
                "현재 비밀번호가 올바르지 않습니다.",
                "error",
            )
            return render_template(
                "auth/change_password.html",
                form=form,
            )

        if current_user.check_password(form.new_password.data):
            flash(
                "새 비밀번호는 현재 비밀번호와 달라야 합니다.",
                "error",
            )
            return render_template(
                "auth/change_password.html",
                form=form,
            )

        current_user.set_password(form.new_password.data)
        db.session.commit()

        # 비밀번호 변경 후 기존 로그인 상태를 종료하고 재인증한다.
        logout_user()
        session.clear()

        flash(
            "비밀번호가 변경되었습니다. 새 비밀번호로 로그인해 주세요.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/change_password.html",
        form=form,
    )