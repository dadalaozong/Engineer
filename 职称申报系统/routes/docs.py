from flask import Blueprint, render_template
from config import CONFIG

bp = Blueprint("docs", __name__, url_prefix="/docs")

@bp.route("/")
def manager_page():
    return render_template("docs/manager.html", config=CONFIG)
