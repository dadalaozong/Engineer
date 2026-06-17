import os
from flask import Blueprint, render_template, request, jsonify
from config import CONFIG

bp = Blueprint("docs", __name__, url_prefix="/docs")

LEVELS = ["工程师", "高级工程师", "正高级工程师"]

_MATERIALS = {
    "工程师": [
        {"name": "职称申报表",          "required": True},
        {"name": "身份证复印件",         "required": True},
        {"name": "学历证书复印件",       "required": True},
        {"name": "学位证书复印件",       "required": False},
        {"name": "现职称证书复印件",     "required": True},
        {"name": "工程技术工作总结",     "required": True},
        {"name": "代表性工程业绩证明",   "required": True},
        {"name": "继续教育证明",         "required": True},
        {"name": "专业技术人员年度考核表","required": True},
    ],
    "高级工程师": [
        {"name": "职称申报表",           "required": True},
        {"name": "身份证复印件",         "required": True},
        {"name": "学历证书复印件",       "required": True},
        {"name": "学位证书复印件",       "required": False},
        {"name": "现职称证书复印件",     "required": True},
        {"name": "工程技术工作总结",     "required": True},
        {"name": "代表性工程业绩证明",   "required": True},
        {"name": "业绩工程施工合同",     "required": True},
        {"name": "业绩工程竣工验收报告", "required": True},
        {"name": "论文或著作证明",       "required": False},
        {"name": "获奖证书复印件",       "required": False},
        {"name": "继续教育证明",         "required": True},
        {"name": "专业技术人员年度考核表","required": True},
    ],
    "正高级工程师": [
        {"name": "职称申报表",           "required": True},
        {"name": "身份证复印件",         "required": True},
        {"name": "学历证书复印件",       "required": True},
        {"name": "学位证书复印件",       "required": True},
        {"name": "现职称证书复印件",     "required": True},
        {"name": "工程技术工作总结",     "required": True},
        {"name": "代表性工程业绩证明",   "required": True},
        {"name": "业绩工程施工合同",     "required": True},
        {"name": "业绩工程竣工验收报告", "required": True},
        {"name": "核心期刊论文",         "required": True},
        {"name": "获奖证书复印件",       "required": True},
        {"name": "继续教育证明",         "required": True},
        {"name": "专业技术人员年度考核表","required": True},
        {"name": "专家推荐信",           "required": False},
    ],
}

_FOLDER_STRUCTURE = {
    "工程师": [
        "01_申报表",
        "02_身份证",
        "03_学历证书",
        "04_职称证书",
        "05_工作总结",
        "06_业绩证明",
        "07_继续教育",
        "08_年度考核",
        "09_其他材料",
    ],
    "高级工程师": [
        "01_申报表",
        "02_身份证",
        "03_学历证书",
        "04_职称证书",
        "05_工作总结",
        "06_业绩证明",
        "07_施工合同",
        "08_竣工验收报告",
        "09_论文著作",
        "10_获奖证书",
        "11_继续教育",
        "12_年度考核",
        "13_其他材料",
    ],
    "正高级工程师": [
        "01_申报表",
        "02_身份证",
        "03_学历证书",
        "04_职称证书",
        "05_工作总结",
        "06_业绩证明",
        "07_施工合同",
        "08_竣工验收报告",
        "09_核心期刊论文",
        "10_获奖证书",
        "11_继续教育",
        "12_年度考核",
        "13_专家推荐信",
        "14_其他材料",
    ],
}


@bp.route("/")
def manager_page():
    return render_template("docs/manager.html", config=CONFIG, levels=LEVELS)


@bp.route("/materials")
def materials():
    level = request.args.get("level", "")
    mats = _MATERIALS.get(level, [])
    return jsonify(mats)


@bp.route("/build", methods=["POST"])
def build_folder():
    data = request.get_json(silent=True) or {}
    base_dir = (data.get("base_dir") or "").strip()
    name     = (data.get("name") or "").strip()
    level    = (data.get("level") or "").strip()

    if not base_dir:
        return jsonify({"ok": False, "error": "请填写基础目录"})
    if not name:
        return jsonify({"ok": False, "error": "请填写姓名"})
    if level not in _FOLDER_STRUCTURE:
        return jsonify({"ok": False, "error": "请选择申报级别"})

    safe_name = name.replace("/", "").replace("\\", "").replace("..", "")
    folder_name = f"{safe_name}_{level}"
    root = os.path.join(base_dir, folder_name)

    try:
        os.makedirs(root, exist_ok=True)
        for sub in _FOLDER_STRUCTURE[level]:
            os.makedirs(os.path.join(root, sub), exist_ok=True)
        return jsonify({"ok": True, "path": root})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
