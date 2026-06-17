import os, tempfile
from flask import Blueprint, render_template, request, jsonify
from core.ocr_reader import is_available, recognize, parse_id_card, parse_degree_cert, parse_title_cert

bp = Blueprint("ocr", __name__, url_prefix="/ocr")

@bp.route("/")
def index_page():
    available = is_available()
    return render_template("ocr/index.html", ocr_available=available)

@bp.route("/recognize", methods=["POST"])
def recognize_file():
    if "file" not in request.files:
        return jsonify({"error": "未上传文件"}), 400
    f    = request.files["file"]
    mode = request.form.get("mode", "id_card")
    suffix = os.path.splitext(f.filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name
    try:
        text = recognize(tmp_path)
        if mode == "id_card":
            parsed = parse_id_card(text)
        elif mode == "degree":
            parsed = parse_degree_cert(text)
        elif mode == "title":
            parsed = parse_title_cert(text)
        else:
            parsed = {}
        return jsonify({"text": text, "parsed": parsed})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try: os.unlink(tmp_path)
        except: pass
