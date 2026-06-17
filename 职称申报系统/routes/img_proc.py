import os, tempfile
from flask import Blueprint, render_template, request, jsonify

bp = Blueprint("img_proc", __name__, url_prefix="/img")

@bp.route("/")
def index_page():
    return render_template("img/index.html")

@bp.route("/process", methods=["POST"])
def process():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未上传文件"})
    f = request.files["file"]
    operation = request.form.get("operation", "compress")
    suffix = os.path.splitext(f.filename)[1] if f.filename else ".jpg"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.save(tmp.name)
    tmp.close()
    try:
        from core.img_processor import process as img_process
        result = img_process(tmp.name, operation)
        return jsonify({"success": True, **result})
    except ImportError:
        return jsonify({"success": False, "error": "图像处理模块未安装，请安装 Pillow"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
