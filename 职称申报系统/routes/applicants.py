from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.models import (
    list_applicants, get_applicant, insert_applicant, update_applicant, delete_applicant,
    list_achievements, get_achievement, insert_achievement, update_achievement, delete_achievement,
    list_awards, insert_award, update_award, delete_award,
    list_papers, insert_paper, update_paper, delete_paper,
    list_contact_logs, insert_contact_log, delete_contact_log,
    list_work_experiences, insert_work_experience, update_work_experience, delete_work_experience,
    list_social_insurance, insert_social_insurance, update_social_insurance, delete_social_insurance,
    total_insure_months,
    list_edu_trainings, insert_edu_training, update_edu_training, delete_edu_training,
    edu_hours_by_year,
    list_pro_certificates, insert_pro_certificate, update_pro_certificate, delete_pro_certificate,
)

bp = Blueprint("applicants", __name__, url_prefix="/applicants")

_A_COLS = [
    "name","id_card","gender","birth_date","phone","email","ethnicity",
    "education","major","school","graduation_year","grad_month","study_mode","degree",
    "work_unit","work_unit_type","work_start_year","work_unit_addr","work_unit_phone",
    "current_position","current_specialty",
    "title_level","title_year","title_month","title_specialty","title_cert_no","title_issuer",
    "politics","address","photo_path","folder_path","notes"
]

def _form(cols):
    return {c: (request.form.get(c) or "").strip() for c in cols}

# ── 列表 / 新增 / 编辑 / 删除 ────────────────────────────────────

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
    insert_applicant(**_form(_A_COLS))
    flash("申报人已添加", "success")
    return redirect(url_for("applicants.list_page"))

@bp.route("/new-json", methods=["POST"])
def create_json():
    """AJAX接口 — OCR弹窗保存申报人。"""
    d    = request.get_json(silent=True) or {}
    name = (d.get("name") or "").strip()
    if not name:
        return jsonify({"success": False, "error": "姓名不能为空"})
    fields = {c: (d.get(c) or "") for c in _A_COLS}
    new_id = insert_applicant(**fields)
    return jsonify({"success": True, "id": new_id})

@bp.route("/<int:aid>/edit", methods=["GET"])
def edit_page(aid):
    applicant = get_applicant(aid)
    if not applicant:
        flash("申报人不存在", "danger")
        return redirect(url_for("applicants.list_page"))
    return render_template("applicants/form.html", applicant=applicant)

@bp.route("/<int:aid>/edit", methods=["POST"])
def update(aid):
    update_applicant(aid, **_form(_A_COLS))
    flash("申报人信息已更新", "success")
    return redirect(url_for("applicants.detail", aid=aid))

@bp.route("/<int:aid>/delete", methods=["POST"])
def delete(aid):
    delete_applicant(aid)
    flash("申报人已删除", "success")
    return redirect(url_for("applicants.list_page"))

# ── 详情页（业绩/获奖/论文/沟通记录汇总）───────────────────────

@bp.route("/<int:aid>")
def detail(aid):
    applicant    = get_applicant(aid)
    if not applicant:
        flash("申报人不存在", "danger")
        return redirect(url_for("applicants.list_page"))
    achievements  = list_achievements(aid)
    awards        = list_awards(aid)
    papers        = list_papers(aid)
    logs          = list_contact_logs(aid)
    work_exps     = list_work_experiences(aid)
    insurances    = list_social_insurance(aid)
    edu_trainings = list_edu_trainings(aid)
    pro_certs     = list_pro_certificates(aid)
    from datetime import date
    return render_template("applicants/detail.html",
                           applicant=applicant,
                           achievements=achievements,
                           awards=awards,
                           papers=papers,
                           logs=logs,
                           work_exps=work_exps,
                           insurances=insurances,
                           insure_total=total_insure_months(aid),
                           edu_trainings=edu_trainings,
                           edu_by_year=edu_hours_by_year(aid),
                           pro_certs=pro_certs,
                           today=date.today().isoformat())

# ── 工程业绩 CRUD ─────────────────────────────────────────────────

_ACH_COLS = [
    "project_name","project_type","scale","role","start_date","end_date",
    "location","owner","contractor","investment","area","description","is_representative"
]

@bp.route("/<int:aid>/achievements/new", methods=["POST"])
def achievement_create(aid):
    d = _form(_ACH_COLS)
    d["applicant_id"] = aid
    d["is_representative"] = 1 if request.form.get("is_representative") else 0
    insert_achievement(**d)
    flash("工程业绩已添加", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#achievements")

@bp.route("/<int:aid>/achievements/<int:rid>/edit", methods=["POST"])
def achievement_update(aid, rid):
    d = _form(_ACH_COLS)
    d["is_representative"] = 1 if request.form.get("is_representative") else 0
    update_achievement(rid, **d)
    flash("已保存", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#achievements")

@bp.route("/<int:aid>/achievements/<int:rid>/delete", methods=["POST"])
def achievement_delete(aid, rid):
    delete_achievement(rid)
    flash("已删除", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#achievements")

# ── 获奖 CRUD ─────────────────────────────────────────────────────

_AWD_COLS = ["award_name","award_level","award_year","award_org","rank","certificate_no","notes"]

@bp.route("/<int:aid>/awards/new", methods=["POST"])
def award_create(aid):
    d = _form(_AWD_COLS); d["applicant_id"] = aid
    insert_award(**d)
    flash("获奖信息已添加", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#awards")

@bp.route("/<int:aid>/awards/<int:wid>/edit", methods=["POST"])
def award_update(aid, wid):
    update_award(wid, **_form(_AWD_COLS))
    flash("已保存", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#awards")

@bp.route("/<int:aid>/awards/<int:wid>/delete", methods=["POST"])
def award_delete(aid, wid):
    delete_award(wid)
    flash("已删除", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#awards")

# ── 论文 CRUD ─────────────────────────────────────────────────────

_PAP_COLS = ["title","paper_type","journal","pub_date","author_rank","cn_issn","notes"]

@bp.route("/<int:aid>/papers/new", methods=["POST"])
def paper_create(aid):
    d = _form(_PAP_COLS); d["applicant_id"] = aid
    insert_paper(**d)
    flash("论文/著作已添加", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#papers")

@bp.route("/<int:aid>/papers/<int:pid>/edit", methods=["POST"])
def paper_update(aid, pid):
    update_paper(pid, **_form(_PAP_COLS))
    flash("已保存", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#papers")

@bp.route("/<int:aid>/papers/<int:pid>/delete", methods=["POST"])
def paper_delete(aid, pid):
    delete_paper(pid)
    flash("已删除", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#papers")

# ── 沟通记录 ──────────────────────────────────────────────────────

_LOG_COLS = ["contact_date","contact_type","content","follow_up","follow_up_date","operator"]

@bp.route("/<int:aid>/logs/new", methods=["POST"])
def log_create(aid):
    d = _form(_LOG_COLS); d["applicant_id"] = aid
    insert_contact_log(**d)
    flash("沟通记录已添加", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#logs")

@bp.route("/<int:aid>/logs/<int:lid>/delete", methods=["POST"])
def log_delete(aid, lid):
    delete_contact_log(lid)
    flash("已删除", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#logs")

# ── 工作经历 CRUD ─────────────────────────────────────────────────

_WE_COLS = ["start_date","end_date","work_unit","position","witness"]

@bp.route("/<int:aid>/work_exps/new", methods=["POST"])
def work_exp_create(aid):
    d = _form(_WE_COLS); d["applicant_id"] = aid
    insert_work_experience(**d)
    flash("工作经历已添加", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#work_exps")

@bp.route("/<int:aid>/work_exps/<int:wid>/edit", methods=["POST"])
def work_exp_update(aid, wid):
    update_work_experience(wid, **_form(_WE_COLS))
    flash("已保存", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#work_exps")

@bp.route("/<int:aid>/work_exps/<int:wid>/delete", methods=["POST"])
def work_exp_delete(aid, wid):
    delete_work_experience(wid)
    flash("已删除", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#work_exps")

# ── 社保记录 CRUD ─────────────────────────────────────────────────

_INS_COLS = ["insure_location","insure_unit","insure_start","insure_end","insure_months"]

@bp.route("/<int:aid>/insurances/new", methods=["POST"])
def insurance_create(aid):
    d = _form(_INS_COLS); d["applicant_id"] = aid
    insert_social_insurance(**d)
    flash("社保记录已添加", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#insurances")

@bp.route("/<int:aid>/insurances/<int:sid>/edit", methods=["POST"])
def insurance_update(aid, sid):
    update_social_insurance(sid, **_form(_INS_COLS))
    flash("已保存", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#insurances")

@bp.route("/<int:aid>/insurances/<int:sid>/delete", methods=["POST"])
def insurance_delete(aid, sid):
    delete_social_insurance(sid)
    flash("已删除", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#insurances")

# ── 继续教育 CRUD ─────────────────────────────────────────────────

_EDU_COLS = ["year","hours","institution","course_name"]

@bp.route("/<int:aid>/edu_trainings/new", methods=["POST"])
def edu_training_create(aid):
    d = _form(_EDU_COLS); d["applicant_id"] = aid
    insert_edu_training(**d)
    flash("继续教育记录已添加", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#edu_trainings")

@bp.route("/<int:aid>/edu_trainings/<int:eid>/edit", methods=["POST"])
def edu_training_update(aid, eid):
    update_edu_training(eid, **_form(_EDU_COLS))
    flash("已保存", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#edu_trainings")

@bp.route("/<int:aid>/edu_trainings/<int:eid>/delete", methods=["POST"])
def edu_training_delete(aid, eid):
    delete_edu_training(eid)
    flash("已删除", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#edu_trainings")

# ── 执业资格 CRUD ─────────────────────────────────────────────────

_CERT_COLS = ["cert_type","cert_no","reg_no","specialty","valid_until"]

@bp.route("/<int:aid>/pro_certs/new", methods=["POST"])
def pro_cert_create(aid):
    d = _form(_CERT_COLS); d["applicant_id"] = aid
    insert_pro_certificate(**d)
    flash("执业资格已添加", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#pro_certs")

@bp.route("/<int:aid>/pro_certs/<int:cid>/edit", methods=["POST"])
def pro_cert_update(aid, cid):
    update_pro_certificate(cid, **_form(_CERT_COLS))
    flash("已保存", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#pro_certs")

@bp.route("/<int:aid>/pro_certs/<int:cid>/delete", methods=["POST"])
def pro_cert_delete(aid, cid):
    delete_pro_certificate(cid)
    flash("已删除", "success")
    return redirect(url_for("applicants.detail", aid=aid) + "#pro_certs")

@bp.route("/<int:aid>/json")
def applicant_json(aid):
    applicant = get_applicant(aid)
    if not applicant:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(applicant))


# ── 资料目录 & 批量OCR ────────────────────────────────────────────

@bp.route("/<int:aid>/folder/create", methods=["POST"])
def folder_create(aid):
    applicant = get_applicant(aid)
    if not applicant:
        return jsonify({"success": False, "error": "申报人不存在"})
    from config import CONFIG
    docs_folder = CONFIG.get("docs_folder", "")
    if not docs_folder:
        return jsonify({"success": False, "error": "请先在系统设置中配置【资料根目录】"})
    from core.folder_manager import create_applicant_folder
    folder_path = create_applicant_folder(applicant, docs_folder)
    merged = dict(applicant)
    merged["folder_path"] = folder_path
    update_applicant(aid, **{c: merged.get(c, "") for c in _A_COLS})
    return jsonify({"success": True, "path": folder_path})

@bp.route("/<int:aid>/folder/scan")
def folder_scan(aid):
    applicant = get_applicant(aid)
    if not applicant:
        flash("申报人不存在", "danger")
        return redirect(url_for("applicants.list_page"))
    folder_path = applicant.get("folder_path", "")
    from core.folder_manager import scan_folder, folder_exists, SUBFOLDERS
    files = scan_folder(folder_path) if folder_exists(folder_path) else []
    return render_template("applicants/folder_scan.html",
                           applicant=applicant,
                           folder_path=folder_path,
                           files=files,
                           subfolders=SUBFOLDERS)

@bp.route("/<int:aid>/folder/batch-ocr", methods=["POST"])
def batch_ocr_run(aid):
    """AJAX — 批量OCR扫描目录，返回汇总结果。"""
    applicant = get_applicant(aid)
    if not applicant:
        return jsonify({"success": False, "error": "申报人不存在"})
    folder_path = applicant.get("folder_path", "")
    from core.folder_manager import scan_folder, folder_exists
    if not folder_exists(folder_path):
        return jsonify({"success": False, "error": "资料目录不存在，请先创建"})
    files = scan_folder(folder_path)
    if not files:
        return jsonify({"success": False, "error": "目录中未找到任何图片文件"})
    from config import CONFIG
    sid  = CONFIG.get("tencent_secret_id", "")
    skey = CONFIG.get("tencent_secret_key", "")
    if not sid or not skey:
        return jsonify({"success": False, "error": "腾讯云OCR未配置"})
    from core.batch_ocr import batch_scan
    result = batch_scan(files, sid, skey)
    return jsonify({"success": True, **result})

@bp.route("/<int:aid>/folder/apply", methods=["POST"])
def batch_apply(aid):
    """一次性将批量OCR结果写入申报人档案。"""
    applicant = get_applicant(aid)
    if not applicant:
        return jsonify({"success": False, "error": "申报人不存在"})
    import json as _json
    # 申报人字段
    merged = dict(applicant)
    for c in _A_COLS:
        v = (request.form.get(c) or "").strip()
        if v:
            merged[c] = v
    update_applicant(aid, **{c: merged.get(c, "") for c in _A_COLS})
    # 执业资格证
    pro_certs_json = request.form.get("pro_certs_json", "[]")
    try:
        for pc in _json.loads(pro_certs_json):
            if pc.get("cert_type"):
                pc["applicant_id"] = aid
                insert_pro_certificate(**pc)
    except Exception:
        pass
    # 社保时段
    ins_json = request.form.get("insurance_json", "[]")
    try:
        for seg in _json.loads(ins_json):
            if seg.get("insure_start"):
                seg["applicant_id"] = aid
                insert_social_insurance(**seg)
    except Exception:
        pass
    flash("OCR识别结果已写入档案", "success")
    return redirect(url_for("applicants.detail", aid=aid))

# ── Excel 导出 ─────────────────────────────────────────────────────

@bp.route("/export/excel")
def export_excel():
    from io import BytesIO
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from flask import make_response

    q = request.args.get("q", "")
    rows = list_applicants(q)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "申报人列表"

    headers = ["姓名","身份证号","性别","出生日期","电话","邮箱","工作单位",
               "学历","专业","毕业院校","毕业年份","参加工作年份",
               "现职称等级","取得年月","备注"]
    keys    = ["name","id_card","gender","birth_date","phone","email","work_unit",
               "education","major","school","graduation_year","work_start_year",
               "title_level","title_month","notes"]

    hdr_fill = PatternFill("solid", fgColor="2563EB")
    hdr_font = Font(color="FFFFFF", bold=True, size=11)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[cell.column_letter].width = max(12, len(h) * 2 + 2)

    for r, row in enumerate(rows, 2):
        for col, key in enumerate(keys, 1):
            ws.cell(row=r, column=col, value=row.get(key) or "")

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    resp.headers["Content-Disposition"] = "attachment; filename=applicants.xlsx"
    return resp
