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
        except Exception as e:
            import json
            yield f"data: {json.dumps({'level':'error','msg':str(e)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream(), mimetype="text/event-stream")

@bp.route("/stop", methods=["POST"])
def stop_fill():
    return jsonify({"ok": True})
