from flask import Blueprint, render_template
from database.models import dashboard_stats, list_batches

bp = Blueprint("dashboard", __name__)

@bp.route("/")
def index():
    stats = dashboard_stats()
    batches = list_batches()[:3]
    return render_template("dashboard.html", stats=stats, batches=batches)
