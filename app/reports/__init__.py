from flask import Blueprint


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/safety-reports",
)

from app.reports import routes