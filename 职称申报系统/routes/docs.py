from flask import Blueprint, render_template, request, jsonify
from database.models import list_projects
from core.folder_builder import get_material_list, build_folder, scan_folder

bp = Blueprint("docs", __name__, url_prefix="/docs")

LEVELS = ["工程师", "高级工程师", "正高级工程师"]

@bp.route("/")
def manager_page():
    projects = list_projects()
    return render_template("docs/manager.html", projects=projects, levels=LEVELS)

@bp.route("/materials")
def get_materials():
    level = request.args.get("level", "")
    return jsonify(get_material_list(level))

@bp.route("/build", methods=["POST"])
def build():
    d = request.get_json()
    base_dir = d.get("base_dir", "")
    name     = d.get("name", "")
    level    = d.get("level", "")
    if not all([base_dir, name, level]):
        return jsonify({"error": "参数不完整"}), 400
    try:
        path = build_folder(base_dir, name, level)
        return jsonify({"ok": True, "path": str(path)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/scan", methods=["POST"])
def scan():
    d = request.get_json()
    folder = d.get("folder", "")
    level  = d.get("level", "")
    if not folder:
        return jsonify({"error": "未提供路径"}), 400
    result = scan_folder(folder, level)
    return jsonify(result)
