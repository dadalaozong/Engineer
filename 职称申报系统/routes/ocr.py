import os, tempfile
from flask import Blueprint, render_template, request, jsonify

bp = Blueprint("ocr", __name__, url_prefix="/ocr")

@bp.route("/")
def index_page():
    return render_template("ocr/index.html")

@bp.route("/recognize", methods=["POST"])
def recognize():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未上传文件"})
    f = request.files["file"]
    suffix = os.path.splitext(f.filename)[1] if f.filename else ".png"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.save(tmp.name)
    tmp.close()
    try:
        from core.ocr_reader import extract_text
        text = extract_text(tmp.name)
        return jsonify({"success": True, "text": text})
    except ImportError:
        return jsonify({"success": False, "error": "OCR模块未安装，请安装 pytesseract 或配置 OCR 服务"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
