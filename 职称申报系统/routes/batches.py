from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.models import list_batches, insert_batch, update_batch, delete_batch
from datetime import date

bp = Blueprint("batches", __name__, url_prefix="/batches")

def _deadline_info(d):
    """Return (days_left, css_class) for a date string."""
    if not d:
        return None, ""
    try:
        dd = date.fromisoformat(d)
        days = (dd - date.today()).days
        if days < 0:
            return days, "text-danger"
        elif days <= 7:
            return days, "text-danger"
        elif days <= 30:
            return days, "text-warning"
        return days, ""
    except ValueError:
        return None, ""

@bp.route("/")
def list_page():
    batches = list_batches()
    for b in batches:
        b["_dl_days"],  b["_dl_cls"]  = _deadline_info(b.get("deadline"))
        b["_sdl_days"], b["_sdl_cls"] = _deadline_info(b.get("submit_deadline"))
    return render_template("batches/list.html", batches=batches)

def _form():
    return dict(
        year=request.form.get("year", ""),
        industry=request.form.get("industry", ""),
        committee=request.form.get("committee", ""),
        level=request.form.get("level", ""),
        deadline=request.form.get("deadline", ""),
        submit_deadline=request.form.get("submit_deadline", ""),
        status=request.form.get("status", "进行中"),
        note=request.form.get("note", ""),
    )

@bp.route("/new", methods=["POST"])
def create():
    insert_batch(**_form())
    flash("批次已添加", "success")
    return redirect(url_for("batches.list_page"))

@bp.route("/<int:bid>/edit", methods=["POST"])
def update(bid):
    update_batch(bid, **_form())
    flash("批次已更新", "success")
    return redirect(url_for("batches.list_page"))

@bp.route("/<int:bid>/delete", methods=["POST"])
def delete(bid):
    delete_batch(bid)
    flash("批次已删除", "success")
    return redirect(url_for("batches.list_page"))
