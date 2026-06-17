from flask import Blueprint, render_template, request, Response, jsonify

bp = Blueprint("ai_writer", __name__, url_prefix="/ai")

@bp.route("/")
def index_page():
    return render_template("ai/writer.html")

@bp.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}
    doc_type = data.get("doc_type", "个人工作总结")
    fields = data.get("fields", {})

    def stream():
        try:
            from core.ai_writer import stream_write
            for chunk in stream_write(doc_type, fields):
                yield f"data: {chunk}\n\n"
        except ImportError:
            mock = f"正在生成《{doc_type}》...\n\n根据您提供的信息，本文将从以下几个方面进行阐述：\n\n一、工作概况\n\n在过去的工作中，认真履行岗位职责，积极完成各项任务。\n\n二、主要成绩\n\n严格按照规范要求开展工作，取得了一定成效。\n\n三、存在不足\n\n工作中仍存在一些不足，需要继续学习提高。\n\n四、下一步计划\n\n继续加强业务学习，提升专业技术水平。"
            for ch in mock:
                yield f"data: {ch}\n\n"
        except Exception as e:
            yield f"data: [错误] {e}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream(), mimetype="text/event-stream")

@bp.route("/export", methods=["POST"])
def export_doc():
    data = request.json or {}
    content = data.get("content", "")
    doc_type = data.get("doc_type", "文档")
    from flask import make_response
    resp = make_response(content)
    resp.headers["Content-Type"] = "text/plain; charset=utf-8"
    resp.headers["Content-Disposition"] = f'attachment; filename="{doc_type}.txt"'
    return resp
