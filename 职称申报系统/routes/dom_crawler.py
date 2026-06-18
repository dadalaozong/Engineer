from flask import Blueprint, render_template, Response, request, stream_with_context, jsonify
import json, os

bp = Blueprint("dom_crawler", __name__, url_prefix="/dom-crawler")

RESULT_PATH = os.path.join(os.path.dirname(__file__), "..", "automation", "dom_structure.json")


@bp.route("/")
def index_page():
    from config import CONFIG
    username = CONFIG.get("username", "")
    return render_template("dom_crawler/index.html", username=username)


@bp.route("/run", methods=["POST"])
def run():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    headless = request.form.get("headless", "true") == "true"

    def generate():
        from automation.dom_crawler import crawl_with_log
        for line in crawl_with_log(username, password, headless=headless):
            yield f"data: {line}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@bp.route("/result")
def result():
    if os.path.exists(RESULT_PATH):
        with open(RESULT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"ok": True, "data": data})
    return jsonify({"ok": False, "error": "尚未抓取，请先运行DOM抓取"})
