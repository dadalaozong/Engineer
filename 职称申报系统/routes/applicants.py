from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.models import (list_applicants, get_applicant,
                              insert_applicant, update_applicant, delete_applicant)

bp = Blueprint("applicants", __name__, url_prefix="/applicants")

FIELDS = ["name","id_card","phone","email","education","major",
          "work_unit","title_level","title_year","notes"]

def _form_data():
    return {f: request.form.get(f, "").strip() for f in FIELDS}

@bp.route("/")
def list_page():
    q = request.args.get("q", "").strip()
    rows = list_applicants(search=q if q else None)
    return render_template("applicants/list.html", rows=rows, q=q)

@bp.route("/new", methods=["GET"])
def new_page():
    return render_template("applicants/form.html", applicant=None)

@bp.route("/new", methods=["POST"])
def create():
    data = _form_data()
    if not data["name"]:
        flash("姓名不能为空", "danger")
        return render_template("applicants/form.html", applicant=data)
    insert_applicant(**data)
    flash(f"已新增申报人：{data['name']}", "success")
    return redirect(url_for("applicants.list_page"))

@bp.route("/<int:aid>/edit", methods=["GET"])
def edit_page(aid):
    a = get_applicant(aid)
    if not a:
        flash("申报人不存在", "danger")
        return redirect(url_for("applicants.list_page"))
    return render_template("applicants/form.html", applicant=a)

@bp.route("/<int:aid>/edit", methods=["POST"])
def update(aid):
    data = _form_data()
    if not data["name"]:
        flash("姓名不能为空", "danger")
        a = get_applicant(aid)
        return render_template("applicants/form.html", applicant=a)
    update_applicant(aid, **data)
    flash("已保存", "success")
    return redirect(url_for("applicants.list_page"))

@bp.route("/<int:aid>/delete", methods=["POST"])
def delete(aid):
    a = get_applicant(aid)
    if a:
        delete_applicant(aid)
        flash(f"已删除：{a['name']}", "success")
    return redirect(url_for("applicants.list_page"))
