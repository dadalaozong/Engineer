from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.models import list_applicants, get_applicant, insert_applicant, update_applicant, delete_applicant

bp = Blueprint("applicants", __name__, url_prefix="/applicants")

def _form_data():
    return dict(
        name=request.form.get("name", ""),
        id_card=request.form.get("id_card", ""),
        phone=request.form.get("phone", ""),
        email=request.form.get("email", ""),
        education=request.form.get("education", ""),
        major=request.form.get("major", ""),
        work_unit=request.form.get("work_unit", ""),
        title_level=request.form.get("title_level", ""),
        title_year=request.form.get("title_year", ""),
        notes=request.form.get("notes", ""),
    )

@bp.route("/")
def list_page():
    q = request.args.get("q", "")
    applicants = list_applicants(q)
    return render_template("applicants/list.html", applicants=applicants)

@bp.route("/new", methods=["GET"])
def new_page():
    return render_template("applicants/form.html", applicant=None)

@bp.route("/new", methods=["POST"])
def create():
    insert_applicant(**_form_data())
    flash("申报人已添加", "success")
    return redirect(url_for("applicants.list_page"))

@bp.route("/<int:aid>/edit", methods=["GET"])
def edit_page(aid):
    applicant = get_applicant(aid)
    return render_template("applicants/form.html", applicant=applicant)

@bp.route("/<int:aid>/edit", methods=["POST"])
def update(aid):
    update_applicant(aid, **_form_data())
    flash("申报人信息已更新", "success")
    return redirect(url_for("applicants.list_page"))

@bp.route("/<int:aid>/delete", methods=["POST"])
def delete(aid):
    delete_applicant(aid)
    flash("申报人已删除", "success")
    return redirect(url_for("applicants.list_page"))

@bp.route("/new-json", methods=["POST"])
def create_json():
    """AJAX接口 — OCR弹窗保存申报人，返回JSON含新记录ID。"""
    d = request.get_json(silent=True) or {}
    name = (d.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "error": "姓名不能为空"})
    fields = {k: (d.get(k) or "") for k in [
        "name","id_card","phone","email","education","major",
        "work_unit","title_level","title_year","notes"
    ]}
    new_id = insert_applicant(**fields)
    return jsonify({"success": True, "id": new_id})
