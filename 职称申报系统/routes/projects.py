from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.models import (
    list_projects, get_project, insert_project, update_project, delete_project,
    list_applicants, list_batches, update_project_stage,
    get_applicant, list_achievements, list_awards, list_papers,
    list_social_insurance, list_edu_trainings,
)

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

@bp.route("/<int:pid>/stage", methods=["POST"])
def set_stage(pid):
    d = request.get_json(silent=True) or {}
    stage = int(d.get("stage", 0))
    update_project_stage(pid, stage)
    return jsonify({"ok": True, "stage": stage})

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

@bp.route("/<int:pid>/prescreen")
def prescreen_page(pid):
    project   = get_project(pid)
    if not project:
        flash("项目不存在", "danger")
        return redirect(url_for("projects.list_page"))
    aid       = project.get("applicant_id")
    applicant = get_applicant(aid) if aid else {}
    if not applicant:
        flash("申报人不存在", "danger")
        return redirect(url_for("projects.list_page"))

    from core.prescreen import prescreen, summary as ps_summary
    achievements  = list_achievements(aid)
    awards        = list_awards(aid)
    papers        = list_papers(aid)
    insurances    = list_social_insurance(aid)
    edu_trainings = list_edu_trainings(aid)

    items = prescreen(applicant, project, achievements, awards, papers, insurances, edu_trainings)
    stat  = ps_summary(items)
    return render_template("projects/prescreen.html",
                           project=project, applicant=applicant,
                           items=items, stat=stat)

@bp.route("/<int:pid>/checklist")
def checklist_page(pid):
    project   = get_project(pid)
    if not project:
        flash("项目不存在", "danger")
        return redirect(url_for("projects.list_page"))
    aid       = project.get("applicant_id")
    applicant = get_applicant(aid) if aid else {}
    level     = project.get("apply_level", "")
    materials = _MATERIALS.get(level, _MATERIALS.get("工程师", []))

    # 检查哪些文件已存在于资料目录
    folder = applicant.get("folder_path", "") if applicant else ""
    file_status = _scan_material_files(folder, materials)

    return render_template("projects/checklist.html",
                           project=project, applicant=applicant or {},
                           materials=materials, file_status=file_status)

@bp.route("/<int:pid>/checklist/download")
def checklist_download(pid):
    project   = get_project(pid)
    if not project:
        flash("项目不存在", "danger")
        return redirect(url_for("projects.list_page"))
    aid       = project.get("applicant_id")
    applicant = get_applicant(aid) if aid else {}
    level     = project.get("apply_level", "")
    materials = _MATERIALS.get(level, _MATERIALS.get("工程师", []))
    folder    = applicant.get("folder_path", "") if applicant else ""
    file_status = _scan_material_files(folder, materials)

    from io import BytesIO
    from flask import make_response
    buf = _build_checklist_word(applicant or {}, project, materials, file_status)
    name = (applicant.get("name") or "申报人") if applicant else "申报人"
    resp = make_response(buf.read())
    resp.headers["Content-Type"] = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    resp.headers["Content-Disposition"] = (
        f"attachment; filename=材料清单_{name}.docx")
    return resp


@bp.route("/<int:pid>/fill-preview")
def fill_preview_page(pid):
    project   = get_project(pid)
    if not project:
        flash("项目不存在", "danger")
        return redirect(url_for("projects.list_page"))
    aid       = project.get("applicant_id")
    applicant = get_applicant(aid) if aid else {}

    # Build field mapping: website label → DB value
    a = applicant or {}
    p = dict(project)
    edu_map = {"大专": "专科", "本科": "本科", "硕士研究生": "硕士", "博士研究生": "博士"}
    edu_display = edu_map.get(a.get("education",""), a.get("education",""))

    from datetime import date
    cur_year = date.today().year
    work_age = ""
    if a.get("work_start_year"):
        try: work_age = f"{cur_year - int(a['work_start_year'])} 年"
        except Exception: pass

    fields = [
        {"section": "基本信息", "items": [
            {"label": "姓名",       "value": a.get("name",""),       "status": "ok" if a.get("name") else "missing"},
            {"label": "身份证号",   "value": a.get("id_card",""),    "status": "ok" if a.get("id_card") else "missing"},
            {"label": "性别",       "value": a.get("gender",""),     "status": "ok" if a.get("gender") else "missing"},
            {"label": "出生日期",   "value": a.get("birth_date",""), "status": "ok" if a.get("birth_date") else "missing"},
            {"label": "民族",       "value": a.get("ethnicity",""),  "status": "ok" if a.get("ethnicity") else "warn"},
            {"label": "政治面貌",   "value": a.get("politics",""),   "status": "ok" if a.get("politics") else "warn"},
            {"label": "手机号",     "value": a.get("phone",""),      "status": "ok" if a.get("phone") else "warn"},
            {"label": "联系地址",   "value": a.get("address",""),    "status": "ok" if a.get("address") else "warn"},
        ]},
        {"section": "学历信息", "items": [
            {"label": "最高学历",   "value": edu_display,           "status": "ok" if a.get("education") else "missing"},
            {"label": "学位",       "value": a.get("degree",""),    "status": "ok" if a.get("degree") else "warn"},
            {"label": "毕业院校",   "value": a.get("school",""),    "status": "ok" if a.get("school") else "missing"},
            {"label": "所学专业",   "value": a.get("major",""),     "status": "ok" if a.get("major") else "missing"},
            {"label": "毕业年月",   "value": f"{a.get('graduation_year','')} 年 {a.get('grad_month','') or ''} 月".strip(" 年 月"),
             "status": "ok" if a.get("graduation_year") else "missing"},
            {"label": "学习方式",   "value": a.get("study_mode",""), "status": "ok" if a.get("study_mode") else "warn"},
        ]},
        {"section": "工作单位", "items": [
            {"label": "工作单位",   "value": a.get("work_unit",""),       "status": "ok" if a.get("work_unit") else "missing"},
            {"label": "单位类型",   "value": a.get("work_unit_type",""),  "status": "ok" if a.get("work_unit_type") else "warn"},
            {"label": "单位地址",   "value": a.get("work_unit_addr",""),  "status": "ok" if a.get("work_unit_addr") else "warn"},
            {"label": "单位电话",   "value": a.get("work_unit_phone",""), "status": "ok" if a.get("work_unit_phone") else "warn"},
            {"label": "参加工作年份", "value": str(a.get("work_start_year","") or ""),
             "status": "ok" if a.get("work_start_year") else "missing"},
            {"label": "工作年限",   "value": work_age,               "status": "ok" if work_age else "missing"},
            {"label": "现任职务",   "value": a.get("current_position",""),"status": "ok" if a.get("current_position") else "warn"},
            {"label": "现从事专业", "value": a.get("current_specialty",""),"status": "ok" if a.get("current_specialty") else "warn"},
        ]},
        {"section": "现职称信息", "items": [
            {"label": "现职称级别", "value": a.get("title_level",""),     "status": "ok" if a.get("title_level") else "missing"},
            {"label": "取得年月",   "value": f"{a.get('title_year','')} 年 {a.get('title_month','') or ''} 月".strip(" 年 月"),
             "status": "ok" if a.get("title_level") else "missing"},
            {"label": "职称专业",   "value": a.get("title_specialty",""), "status": "ok" if a.get("title_specialty") else "warn"},
            {"label": "证书编号",   "value": a.get("title_cert_no",""),   "status": "ok" if a.get("title_cert_no") else "warn"},
            {"label": "发证机关",   "value": a.get("title_issuer",""),    "status": "ok" if a.get("title_issuer") else "warn"},
        ]},
        {"section": "申报项目", "items": [
            {"label": "申报级别",   "value": p.get("apply_level",""),  "status": "ok" if p.get("apply_level") else "missing"},
            {"label": "申报专业",   "value": p.get("specialty",""),    "status": "ok" if p.get("specialty") else "warn"},
            {"label": "评委会",     "value": p.get("committee",""),    "status": "ok" if p.get("committee") else "warn"},
            {"label": "行业",       "value": p.get("industry",""),     "status": "ok" if p.get("industry") else "warn"},
            {"label": "申报年度",   "value": str(p.get("batch_year","") or ""), "status": "ok" if p.get("batch_year") else "warn"},
        ]},
    ]

    missing = sum(1 for sec in fields for it in sec["items"] if it["status"]=="missing")
    warn    = sum(1 for sec in fields for it in sec["items"] if it["status"]=="warn")
    ok      = sum(1 for sec in fields for it in sec["items"] if it["status"]=="ok")

    return render_template("projects/fill_preview.html",
                           project=project, applicant=a,
                           fields=fields, missing=missing, warn=warn, ok=ok)


def _scan_material_files(folder: str, materials: list) -> dict:
    """检查资料目录中各材料是否已有文件，返回 {材料名: True/False}"""
    import os, re
    status = {m["name"]: False for m in materials}
    if not folder or not os.path.isdir(folder):
        return status
    # 收集所有子目录下的文件名
    all_files = []
    for root, _, files in os.walk(folder):
        all_files.extend(files)
    all_lower = " ".join(all_files).lower()
    keywords = {
        "身份证":       ["身份证"],
        "学历证书":     ["学历"],
        "学位证书":     ["学位"],
        "职称证书":     ["职称"],
        "工程技术工作总结": ["工作总结","总结"],
        "代表性工程业绩证明": ["业绩"],
        "业绩工程施工合同": ["合同"],
        "业绩工程竣工验收报告": ["竣工","验收"],
        "论文":         ["论文","著作"],
        "获奖证书":     ["获奖","奖励"],
        "继续教育证明": ["继续教育","培训"],
        "年度考核":     ["考核"],
        "专家推荐信":   ["推荐"],
        "申报表":       ["申报表"],
    }
    for mat_name in status:
        for key, kws in keywords.items():
            if key in mat_name:
                if any(kw in all_lower for kw in kws):
                    status[mat_name] = True
                break
    return status


def _build_checklist_word(applicant: dict, project: dict,
                           materials: list, file_status: dict):
    """生成材料清单 Word 文档，返回 BytesIO。"""
    from io import BytesIO
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from datetime import date

    doc = Document()

    # 页边距
    for sec in doc.sections:
        sec.top_margin = sec.bottom_margin = Cm(2)
        sec.left_margin = sec.right_margin = Cm(2.5)

    def _heading(text, size=16, bold=True, center=False):
        p = doc.add_paragraph()
        if center:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.font.size = Pt(size)
        run.font.bold = bold
        return p

    def _para(text, size=11, bold=False, color=None):
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.font.size = Pt(size)
        run.font.bold = bold
        if color:
            run.font.color.rgb = RGBColor(*color)
        return p

    # 标题
    _heading("职称申报材料清单", 16, True, True)
    doc.add_paragraph()

    # 申报人信息表
    info_table = doc.add_table(rows=3, cols=4)
    info_table.style = "Table Grid"
    cells = [
        ("姓    名", applicant.get("name","") or ""),
        ("工作单位", applicant.get("work_unit","") or ""),
        ("申报级别", project.get("apply_level","") or ""),
        ("申报专业", project.get("specialty","") or ""),
        ("现职称",   applicant.get("title_level","") or ""),
        ("截止日期", project.get("deadline","") or ""),
    ]
    for i, (label, val) in enumerate(cells):
        row, col = divmod(i, 2)
        info_table.rows[row].cells[col*2].text     = label
        info_table.rows[row].cells[col*2+1].text   = val
    doc.add_paragraph()

    # 清单标题
    _para(f"请按以下清单准备材料（共 {len(materials)} 项），将文件扫描后放入对应目录：",
          size=11, color=(80,80,80))
    doc.add_paragraph()

    # 材料表格
    tbl = doc.add_table(rows=1, cols=4)
    tbl.style = "Table Grid"
    hdr = tbl.rows[0].cells
    for i, h in enumerate(["序号","材料名称","是否必须","状态"]):
        hdr[i].text = h
        hdr[i].paragraphs[0].runs[0].font.bold = True

    received = sum(1 for v in file_status.values() if v)
    for idx, m in enumerate(materials, 1):
        row = tbl.add_row().cells
        name   = m["name"]
        found  = file_status.get(name, False)
        row[0].text = str(idx)
        row[1].text = name
        row[2].text = "必须" if m["required"] else "建议"
        row[3].text = "✅ 已收到" if found else "⬜ 待提交"
        if not found and m["required"]:
            for cell in row:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.color.rgb = RGBColor(180,0,0)

    doc.add_paragraph()
    _para(f"已收到 {received}/{len(materials)} 项材料", bold=True,
          color=(22,163,74) if received == len(materials) else (180,0,0))
    _para(f"生成时间：{date.today()}", size=10, color=(120,120,120))

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

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
