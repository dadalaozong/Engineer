from flask import Blueprint, render_template, request, jsonify, Response
from database.models import list_applicants, list_projects

bp = Blueprint("auto_fill", __name__, url_prefix="/autofill")

@bp.route("/")
def index_page():
    return render_template("auto_fill/index.html")

@bp.route("/applicants")
def get_applicants():
    applicants = list_applicants()
    return jsonify([dict(a) for a in applicants])

@bp.route("/projects")
def get_projects():
    applicant_id = request.args.get("applicant_id")
    projects = list_projects(applicant_id=applicant_id)
    return jsonify([dict(p) for p in projects])

@bp.route("/start", methods=["POST"])
def start_fill():
    data = request.json or {}
    applicant_id = data.get("applicant_id")
    project_id = data.get("project_id")
    headless = data.get("headless", True)

    def stream():
        try:
            from automation.form_filler import AutoFiller
            filler = AutoFiller(headless=headless)
            for line in filler.run(applicant_id, project_id):
                yield f"data: {line}\n\n"
        except ImportError:
            import json
            logs = [
                {"level": "warn",  "msg": "自动填报模块未安装（需要 selenium）"},
                {"level": "info",  "msg": "pip install selenium webdriver-manager"},
                {"level": "info",  "msg": "模拟运行中..."},
                {"level": "info",  "msg": f"申报人ID: {applicant_id} / 项目ID: {project_id}"},
                {"level": "info",  "msg": f"无头模式: {headless}"},
                {"level": "ok",    "msg": "模拟完成"},
            ]
            for log in logs:
                yield f"data: {json.dumps(log, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {e}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream(), mimetype="text/event-stream")

@bp.route("/stop", methods=["POST"])
def stop_fill():
    return jsonify({"ok": True})
