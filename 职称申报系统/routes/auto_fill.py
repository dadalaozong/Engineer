import json, threading
from flask import Blueprint, render_template, request, jsonify, Response
from database.models import list_applicants, list_projects, get_applicant, get_project

bp = Blueprint("auto_fill", __name__, url_prefix="/autofill")

_workers: dict[str, object] = {}

@bp.route("/")
def index_page():
    return render_template("auto_fill/index.html")

@bp.route("/applicants")
def get_applicants():
    rows = list_applicants()
    return jsonify([{"id": r["id"], "name": r["name"]} for r in rows])

@bp.route("/projects")
def get_projects():
    aid = request.args.get("applicant_id", type=int)
    rows = list_projects(applicant_id=aid) if aid else []
    return jsonify([{
        "id": r["id"],
        "label": f"{r.get('apply_level','')} · {r.get('industry','')} · {r.get('committee','')}",
        "industry":   r.get("industry", ""),
        "committee":  r.get("committee", ""),
        "apply_level": r.get("apply_level", ""),
        "scale":      r.get("scale", ""),
        "folder_path": r.get("folder_path", ""),
    } for r in rows])

@bp.route("/start", methods=["POST"])
def start_fill():
    d         = request.get_json()
    aid       = d.get("applicant_id")
    pid       = d.get("project_id")
    headless  = bool(d.get("headless", False))
    applicant = get_applicant(aid)
    project   = get_project(pid)
    if not applicant or not project:
        return jsonify({"error": "数据不存在"}), 404

    log_queue: list[str] = []
    done_event = threading.Event()

    def log_cb(name, ok, msg):
        icon = "✅" if ok else "❌"
        log_queue.append(json.dumps({"step": name, "ok": ok,
                                     "msg": msg, "icon": icon}, ensure_ascii=False))

    def run_fill():
        try:
            from automation.browser import BrowserManager
            from automation.form_filler import FormFiller
            bm = BrowserManager()
            bm.start(headless=headless)
            _workers["browser"] = bm
            filler = FormFiller(bm)
            report = filler.run(applicant, project, log_callback=log_cb)
            log_queue.append(json.dumps({"done": True, "summary": report.summary()},
                                        ensure_ascii=False))
        except Exception as e:
            log_queue.append(json.dumps({"error": str(e)}, ensure_ascii=False))
        finally:
            done_event.set()

    t = threading.Thread(target=run_fill, daemon=True)
    t.start()
    _workers["thread"] = t

    def event_stream():
        import time
        sent = 0
        while not done_event.is_set() or sent < len(log_queue):
            while sent < len(log_queue):
                yield f"data: {log_queue[sent]}\n\n"
                sent += 1
            time.sleep(0.2)

    return Response(event_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@bp.route("/stop", methods=["POST"])
def stop_fill():
    bm = _workers.get("browser")
    if bm:
        try: bm.stop()
        except: pass
        _workers.pop("browser", None)
    return jsonify({"ok": True})
