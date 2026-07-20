from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def admin_required(view_function):
    """로그인한 관리자만 접근하도록 제한한다."""

    @wraps(view_function)
    @login_required
    def wrapped_view(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)

        return view_function(*args, **kwargs)

    return wrapped_view