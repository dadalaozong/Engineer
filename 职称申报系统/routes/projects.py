from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.models import (list_projects, get_project, insert_project,
                              update_project, delete_project, list_applicants, list_batches)
from core.scale_engine import SPECIALTY_NAMES, judge
from core.folder_builder import get_material_list, scan_folder

bp = Blueprint("projects", __name__, url_prefix="/projects")

P_FIELDS = ["applicant_id","batch_id","industry","committee","apply_level",
            "scale","folder_path","note"]

def _form_data():
    return {f: request.form.get(f, "").strip() for f in P_FIELDS}

@bp.route("/")
def list_page():
    aid = request.args.get("applicant_id", type=int)
    rows = list_projects(applicant_id=aid)
    applicants = list_applicants()
    return render_template("projects/list.html", rows=rows,
                           applicants=applicants, filter_aid=aid)

@bp.route("/new", methods=["GET"])
def new_page():
    applicants = list_applicants()
    batches    = list_batches()
    return render_template("projects/form.html", project=None,
                           applicants=applicants, batches=batches)

@bp.route("/new", methods=["POST"])
def create():
    data = _form_data()
    if not data["applicant_id"]:
        flash("请选择申报人", "danger")
        return render_template("projects/form.html", project=data,
                               applicants=list_applicants(), batches=list_batches())
    insert_project(**data)
    flash("已新增项目", "success")
    return redirect(url_for("projects.list_page"))

@bp.route("/<int:pid>/edit", methods=["GET"])
def edit_page(pid):
    p = get_project(pid)
    if not p:
        flash("项目不存在", "danger")
        return redirect(url_for("projects.list_page"))
    return render_template("projects/form.html", project=p,
                           applicants=list_applicants(), batches=list_batches())

@bp.route("/<int:pid>/edit", methods=["POST"])
def update(pid):
    data = _form_data()
    update_project(pid, **data)
    flash("已保存", "success")
    return redirect(url_for("projects.list_page"))

@bp.route("/<int:pid>/delete", methods=["POST"])
def delete(pid):
    delete_project(pid)
    flash("已删除", "success")
    return redirect(url_for("projects.list_page"))

@bp.route("/scale")
def scale_page():
    return render_template("projects/scale.html", specialties=SPECIALTY_NAMES)

@bp.route("/scale/judge", methods=["POST"])
def scale_judge():
    data = request.get_json()
    specialty = data.get("specialty", "")
    indicators = data.get("indicators", {})
    parsed = {}
    for k, v in indicators.items():
        try:
            parsed[k] = float(v)
        except (ValueError, TypeError):
            pass
    result = judge(specialty, parsed)
    if result:
        return jsonify({"level": result.level, "color": result.color,
                        "matched": result.matched_indicator,
                        "message": result.message})
    return jsonify({"level": "无法判断", "color": "#64748b",
                    "matched": "", "message": "专业不存在或指标不足"})

@bp.route("/checker")
def checker_page():
    projects = list_projects()
    return render_template("projects/checker.html", projects=projects)

@bp.route("/checker/scan", methods=["POST"])
def checker_scan():
    data = request.get_json()
    pid = data.get("project_id")
    p   = get_project(pid) if pid else None
    if not p:
        return jsonify({"error": "项目不存在"}), 404
    level  = p.get("apply_level", "")
    folder = p.get("folder_path", "")
    materials = get_material_list(level)
    if folder:
        scan = scan_folder(folder, level)
        return jsonify({"materials": materials, "scan": scan, "folder": folder})
    return jsonify({"materials": materials, "scan": {}, "folder": ""})
