from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.models import list_batches, insert_batch, update_batch, delete_batch

bp = Blueprint("batches", __name__, url_prefix="/batches")

FIELDS = ["year","industry","committee","level","deadline","note"]

@bp.route("/")
def list_page():
    rows = list_batches()
    return render_template("batches/list.html", rows=rows)

@bp.route("/new", methods=["POST"])
def create():
    d = {f: request.form.get(f, "").strip() for f in FIELDS}
    if not d["year"]:
        flash("年度不能为空", "danger")
        return redirect(url_for("batches.list_page"))
    insert_batch(**d)
    flash("已新增批次", "success")
    return redirect(url_for("batches.list_page"))

@bp.route("/<int:bid>/edit", methods=["POST"])
def update(bid):
    d = {f: request.form.get(f, "").strip() for f in FIELDS}
    update_batch(bid, **d)
    flash("已保存", "success")
    return redirect(url_for("batches.list_page"))

@bp.route("/<int:bid>/delete", methods=["POST"])
def delete(bid):
    delete_batch(bid)
    flash("已删除", "success")
    return redirect(url_for("batches.list_page"))
