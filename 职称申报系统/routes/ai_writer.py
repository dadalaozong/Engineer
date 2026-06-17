import json, io
from flask import Blueprint, render_template, request, jsonify, Response, send_file, flash
from config import load_config
from core.crypto import decrypt
from core.ai_writer import AIWriter, build_work_summary_info, build_masterwork_info, build_achievement_info

bp = Blueprint("ai_writer", __name__, url_prefix="/ai")

DOC_TYPES = [
    ("work_summary",  "个人工作总结"),
    ("masterwork",    "代表性工程业绩"),
    ("achievement",   "科技成果说明"),
]

def _get_writer():
    cfg = load_config()
    key = decrypt(cfg["ai"].get("api_key_cipher", "")) or cfg["ai"].get("deepseek_api_key", "")
    model = cfg["ai"].get("model", "deepseek-chat")
    base_url = cfg["ai"].get("base_url", "https://api.deepseek.com")
    return AIWriter(api_key=key, model=model, base_url=base_url)

@bp.route("/")
def index_page():
    return render_template("ai/writer.html", doc_types=DOC_TYPES)

@bp.route("/generate", methods=["POST"])
def generate():
    d = request.get_json()
    doc_type = d.get("doc_type", "work_summary")
    info     = d.get("info", {})
    try:
        writer = _get_writer()
    except Exception as e:
        return jsonify({"error": f"AI配置错误：{e}"}), 500

    def event_stream():
        try:
            for chunk in writer.generate_stream(doc_type, info):
                yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(event_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@bp.route("/export", methods=["POST"])
def export_doc():
    d = request.get_json()
    content  = d.get("content", "")
    doc_type = d.get("doc_type", "文档")
    filename = f"{doc_type}.docx"
    try:
        from docx import Document
        doc = Document()
        doc.add_heading(doc_type, level=1)
        for para in content.split("\n"):
            doc.add_paragraph(para)
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name=filename,
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
