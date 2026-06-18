"""文件到达监控路由。"""
import json
import time
from flask import Blueprint, render_template, request, jsonify, Response
from database.models import list_applicants, get_applicant

bp = Blueprint("monitor", __name__, url_prefix="/monitor")


@bp.route("/")
def index_page():
    applicants = list_applicants()
    from core.folder_monitor import list_monitors
    active = {m["applicant_id"]: m for m in list_monitors()}
    return render_template("monitor/index.html",
                           applicants=applicants, active=active)


@bp.route("/start", methods=["POST"])
def start():
    data = request.json or {}
    aid  = data.get("applicant_id")
    if not aid:
        return jsonify({"ok": False, "error": "缺少 applicant_id"})
    applicant = get_applicant(aid)
    if not applicant:
        return jsonify({"ok": False, "error": "申报人不存在"})
    folder = applicant.get("folder_path", "")
    if not folder:
        return jsonify({"ok": False, "error": "该申报人尚未设置资料目录"})

    import os
    if not os.path.isdir(folder):
        return jsonify({"ok": False, "error": f"目录不存在：{folder}"})

    from core.folder_monitor import start_monitor
    m = start_monitor(int(aid), folder)
    return jsonify({"ok": True, "folder": folder, "running": m.running})


@bp.route("/stop", methods=["POST"])
def stop():
    data = request.json or {}
    aid  = data.get("applicant_id")
    if aid:
        from core.folder_monitor import stop_monitor
        stop_monitor(int(aid))
    return jsonify({"ok": True})


@bp.route("/status")
def status():
    from core.folder_monitor import list_monitors
    return jsonify(list_monitors())


@bp.route("/events")
def events_stream():
    """SSE 流：推送指定申报人资料目录的文件变更事件。"""
    aid = request.args.get("applicant_id", type=int)

    def generate():
        last_idx = 0
        timeout  = 300  # 5 minutes max
        start_t  = time.time()

        yield "data: {\"type\":\"connected\"}\n\n"

        from core.folder_monitor import get_monitor
        while time.time() - start_t < timeout:
            m = get_monitor(aid) if aid else None
            if m:
                evs = m.events[last_idx:]
                for ev in evs:
                    yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
                last_idx += len(evs)
            time.sleep(1)

        yield "data: {\"type\":\"timeout\"}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})
