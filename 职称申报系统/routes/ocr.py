import os, tempfile
from flask import Blueprint, render_template, request, jsonify
from config import CONFIG

bp = Blueprint("ocr", __name__, url_prefix="/ocr")

def _creds():
    return CONFIG.get("tencent_secret_id", ""), CONFIG.get("tencent_secret_key", "")

@bp.route("/")
def index_page():
    configured = bool(CONFIG.get("tencent_secret_id") and CONFIG.get("tencent_secret_key"))
    return render_template("ocr/index.html", configured=configured)

def _save_upload(f) -> str:
    suffix = os.path.splitext(f.filename)[1] if f.filename else ".jpg"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.save(tmp.name)
    tmp.close()
    return tmp.name

@bp.route("/id-card", methods=["POST"])
def ocr_id_card():
    """身份证识别 — 返回结构化字段，供新增申报人弹窗使用。"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未上传文件"})
    sid, skey = _creds()
    if not sid or not skey:
        return jsonify({"success": False, "error": "腾讯云OCR未配置，请先在系统设置中填写凭证"})
    tmp_path = _save_upload(request.files["file"])
    side = request.form.get("side", "FRONT")
    try:
        from core.ocr_reader import recognize_id_card
        fields = recognize_id_card(tmp_path, sid, skey, card_side=side)
        return jsonify({"success": True, "fields": fields})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        try: os.unlink(tmp_path)
        except: pass

@bp.route("/degree", methods=["POST"])
def ocr_degree():
    """学历证书识别 — 通用OCR + 结构化解析。"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未上传文件"})
    sid, skey = _creds()
    if not sid or not skey:
        return jsonify({"success": False, "error": "腾讯云OCR未配置"})
    tmp_path = _save_upload(request.files["file"])
    try:
        from core.ocr_reader import recognize_degree_cert
        fields = recognize_degree_cert(tmp_path, sid, skey)
        return jsonify({"success": True, "fields": fields})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        try: os.unlink(tmp_path)
        except: pass

@bp.route("/recognize", methods=["POST"])
def recognize():
    """通用识别（原有接口兼容）。"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未上传文件"})
    sid, skey = _creds()
    if not sid or not skey:
        return jsonify({"success": False, "error": "腾讯云OCR未配置"})
    tmp_path = _save_upload(request.files["file"])
    try:
        from core.ocr_reader import recognize_general
        result = recognize_general(tmp_path, sid, skey)
        return jsonify({"success": True, "text": result["text"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    finally:
        try: os.unlink(tmp_path)
        except: pass
