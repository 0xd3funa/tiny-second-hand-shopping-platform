from flask import Blueprint


transfers_bp = Blueprint(
    "transfers",
    __name__,
    url_prefix="/transfers",
)


from app.transfers import routes