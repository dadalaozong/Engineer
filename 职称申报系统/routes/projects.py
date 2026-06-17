from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.models import list_projects, get_project, insert_project, update_project, delete_project, list_applicants, list_batches

bp = Blueprint("projects", __name__, url_prefix="/projects")

SPECIALTY_NAMES = ["房屋建筑工程", "市政公用工程", "装饰装修工程", "机电安装工程", "公路工程"]

def _form_data():
    return dict(
        applicant_id=request.form.get("applicant_id", ""),
        batch_id=request.form.get("batch_id", ""),
        industry=request.form.get("industry", ""),
        committee=request.form.get("committee", ""),
        apply_level=request.form.get("apply_level", ""),
        specialty=request.form.get("specialty", ""),
        project_name=request.form.get("project_name", ""),
        project_type=request.form.get("project_type", ""),
        scale=request.form.get("scale", ""),
        role=request.form.get("role", ""),
        folder_path=request.form.get("folder_path", ""),
        status=request.form.get("status", ""),
        notes=request.form.get("notes", ""),
    )

@bp.route("/")
def list_page():
    applicant_id = request.args.get("applicant_id", type=int)
    rows = list_projects(applicant_id=applicant_id)
    return render_template("projects/list.html",
                           rows=rows,
                           applicants=list_applicants(),
                           filter_aid=applicant_id)

@bp.route("/new", methods=["GET"])
def new_page():
    return render_template("projects/form.html", project=None, applicants=list_applicants(), batches=list_batches())

@bp.route("/new", methods=["POST"])
def create():
    insert_project(**_form_data())
    flash("项目已添加", "success")
    return redirect(url_for("projects.list_page"))

@bp.route("/<int:pid>/edit", methods=["GET"])
def edit_page(pid):
    project = get_project(pid)
    return render_template("projects/form.html", project=project, applicants=list_applicants(), batches=list_batches())

@bp.route("/<int:pid>/edit", methods=["POST"])
def update(pid):
    update_project(pid, **_form_data())
    flash("项目已更新", "success")
    return redirect(url_for("projects.list_page"))

@bp.route("/<int:pid>/delete", methods=["POST"])
def delete(pid):
    delete_project(pid)
    flash("项目已删除", "success")
    return redirect(url_for("projects.list_page"))

@bp.route("/scale", methods=["GET"])
def scale_page():
    return render_template("projects/scale.html", SPECIALTY_NAMES=SPECIALTY_NAMES)

def judge(specialty, indicators):
    cost = float(indicators.get("cost") or 0)
    area = float(indicators.get("area") or 0)
    height = float(indicators.get("height") or 0)
    floors = float(indicators.get("floors") or 0)
    road_len = float(indicators.get("road_len") or 0)
    pipe_dia = float(indicators.get("pipe_dia") or 0)
    bridge_span = float(indicators.get("bridge_span") or 0)
    deco_area = float(indicators.get("deco_area") or 0)
    transformer = float(indicators.get("transformer") or 0)
    chiller = float(indicators.get("chiller") or 0)
    speed = float(indicators.get("speed") or 0)

    scale = "小型"
    color = "#6b7280"
    detail = ""

    if specialty == "房屋建筑工程":
        if cost >= 10000 or area >= 10 or height >= 100 or floors >= 3:
            scale, color = "大型", "#dc2626"
            detail = f"造价{cost}万元/面积{area}万㎡/高度{height}m/地下{floors}层"
        elif cost >= 3000 or area >= 3 or height >= 50 or floors >= 2:
            scale, color = "中型", "#d97706"
            detail = f"造价{cost}万元/面积{area}万㎡/高度{height}m/地下{floors}层"
        else:
            detail = f"造价{cost}万元/面积{area}万㎡"
    elif specialty == "市政公用工程":
        if cost >= 5000 or road_len >= 10 or pipe_dia >= 1000 or bridge_span >= 150:
            scale, color = "大型", "#dc2626"
        elif cost >= 1000 or road_len >= 3 or pipe_dia >= 500 or bridge_span >= 50:
            scale, color = "中型", "#d97706"
        detail = f"造价{cost}万元/道路{road_len}km"
    elif specialty == "装饰装修工程":
        if cost >= 2000 or deco_area >= 20000:
            scale, color = "大型", "#dc2626"
        elif cost >= 500 or deco_area >= 5000:
            scale, color = "中型", "#d97706"
        detail = f"造价{cost}万元/面积{deco_area}㎡"
    elif specialty == "机电安装工程":
        if cost >= 3000 or transformer >= 10000 or chiller >= 1000:
            scale, color = "大型", "#dc2626"
        elif cost >= 1000 or transformer >= 3000 or chiller >= 300:
            scale, color = "中型", "#d97706"
        detail = f"造价{cost}万元/变压器{transformer}kVA"
    elif specialty == "公路工程":
        if cost >= 5000 or road_len >= 20 or speed >= 120:
            scale, color = "大型", "#dc2626"
        elif cost >= 1000 or road_len >= 5 or speed >= 80:
            scale, color = "中型", "#d97706"
        detail = f"造价{cost}万元/长度{road_len}km/速度{speed}km/h"

    return scale, color, detail

@bp.route("/scale", methods=["POST"])
def scale_judge():
    data = request.json or {}
    specialty = data.get("specialty", "")
    indicators = data.get("indicators", {})
    scale, color, detail = judge(specialty, indicators)
    return jsonify({"scale": scale, "color": color, "detail": detail})

@bp.route("/checker")
def checker_page():
    projects = list_projects()
    return render_template("projects/checker.html", projects=projects)

# Material checklists per apply level
_MATERIALS = {
    "工程师": [
        {"name": "职称申报表", "required": True},
        {"name": "身份证复印件", "required": True},
        {"name": "学历证书复印件", "required": True},
        {"name": "学位证书复印件", "required": False},
        {"name": "现职称证书复印件", "required": True},
        {"name": "工程技术工作总结", "required": True},
        {"name": "代表性工程业绩证明", "required": True},
        {"name": "继续教育证明", "required": True},
        {"name": "专业技术人员年度考核表", "required": True},
    ],
    "高级工程师": [
        {"name": "职称申报表", "required": True},
        {"name": "身份证复印件", "required": True},
        {"name": "学历证书复印件", "required": True},
        {"name": "学位证书复印件", "required": False},
        {"name": "现职称证书复印件", "required": True},
        {"name": "工程技术工作总结", "required": True},
        {"name": "代表性工程业绩证明", "required": True},
        {"name": "业绩工程施工合同", "required": True},
        {"name": "业绩工程竣工验收报告", "required": True},
        {"name": "论文或著作证明", "required": False},
        {"name": "获奖证书复印件", "required": False},
        {"name": "继续教育证明", "required": True},
        {"name": "专业技术人员年度考核表", "required": True},
    ],
    "正高级工程师": [
        {"name": "职称申报表", "required": True},
        {"name": "身份证复印件", "required": True},
        {"name": "学历证书复印件", "required": True},
        {"name": "学位证书复印件", "required": True},
        {"name": "现职称证书复印件", "required": True},
        {"name": "工程技术工作总结", "required": True},
        {"name": "代表性工程业绩证明", "required": True},
        {"name": "业绩工程施工合同", "required": True},
        {"name": "业绩工程竣工验收报告", "required": True},
        {"name": "核心期刊论文", "required": True},
        {"name": "获奖证书复印件", "required": True},
        {"name": "继续教育证明", "required": True},
        {"name": "专业技术人员年度考核表", "required": True},
        {"name": "专家推荐信", "required": False},
    ],
}

@bp.route("/checker/scan", methods=["POST"])
def checker_scan():
    import os
    data = request.get_json(silent=True) or {}
    pid = data.get("project_id")
    if not pid:
        return jsonify({"materials": [], "scan": {}, "folder": None})
    project = get_project(pid)
    if not project:
        return jsonify({"materials": [], "scan": {}, "folder": None})

    level = project.get("apply_level", "")
    materials = _MATERIALS.get(level, _MATERIALS.get("工程师", []))
    folder = project.get("folder_path", "")
    scan = {}

    if folder and os.path.isdir(folder):
        try:
            files = os.listdir(folder)
            files_lower = [f.lower() for f in files]
            for m in materials:
                name = m["name"]
                scan[name] = any(name in f or name.replace("复印件","") in f for f in files)
        except Exception:
            pass

    return jsonify({"materials": materials, "scan": scan, "folder": folder})
