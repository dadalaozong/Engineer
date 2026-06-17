from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.models import list_batches, insert_batch, update_batch, delete_batch

bp = Blueprint("batches", __name__, url_prefix="/batches")

@bp.route("/")
def list_page():
    batches = list_batches()
    return render_template("batches/list.html", batches=batches)

@bp.route("/new", methods=["POST"])
def create():
    insert_batch(
        year=request.form.get("year", ""),
        industry=request.form.get("industry", ""),
        committee=request.form.get("committee", ""),
        level=request.form.get("level", ""),
        deadline=request.form.get("deadline", ""),
        note=request.form.get("note", ""),
    )
    flash("批次已添加", "success")
    return redirect(url_for("batches.list_page"))

@bp.route("/<int:bid>/edit", methods=["POST"])
def update(bid):
    update_batch(
        bid,
        year=request.form.get("year", ""),
        industry=request.form.get("industry", ""),
        committee=request.form.get("committee", ""),
        level=request.form.get("level", ""),
        deadline=request.form.get("deadline", ""),
        note=request.form.get("note", ""),
    )
    flash("批次已更新", "success")
    return redirect(url_for("batches.list_page"))

@bp.route("/<int:bid>/delete", methods=["POST"])
def delete(bid):
    delete_batch(bid)
    flash("批次已删除", "success")
    return redirect(url_for("batches.list_page"))
