from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from config import CONFIG, save_config

bp = Blueprint("settings", __name__, url_prefix="/settings")

@bp.route("/")
def index_page():
    return render_template("settings/index.html", config=CONFIG)

@bp.route("/website", methods=["POST"])
def save_website():
    CONFIG["website_url"] = request.form.get("website_url", "")
    CONFIG["username"]    = request.form.get("username", "")
    pw = request.form.get("password", "")
    if pw:
        CONFIG["password"] = pw
    save_config(CONFIG)
    flash("网站账号已保存", "success")
    return redirect(url_for("settings.index_page"))

@bp.route("/ai", methods=["POST"])
def save_ai():
    CONFIG["ai_api_key"] = request.form.get("ai_api_key", "")
    CONFIG["ai_model"]   = request.form.get("ai_model", "deepseek-chat")
    CONFIG["ai_base_url"]= request.form.get("ai_base_url", "https://api.deepseek.com")
    save_config(CONFIG)
    flash("AI设置已保存", "success")
    return redirect(url_for("settings.index_page"))

@bp.route("/ocr", methods=["POST"])
def save_ocr():
    CONFIG["tencent_secret_id"]  = request.form.get("tencent_secret_id", "").strip()
    CONFIG["tencent_secret_key"] = request.form.get("tencent_secret_key", "").strip()
    CONFIG["tencent_ocr_region"] = request.form.get("tencent_ocr_region", "ap-guangzhou")
    save_config(CONFIG)
    flash("腾讯云OCR配置已保存", "success")
    return redirect(url_for("settings.index_page"))

@bp.route("/test-ocr", methods=["POST"])
def test_ocr():
    sid  = CONFIG.get("tencent_secret_id", "")
    skey = CONFIG.get("tencent_secret_key", "")
    if not sid or not skey:
        return jsonify({"ok": False, "msg": "SecretId / SecretKey 未配置"})
    try:
        # 用一张1x1白色PNG测试签名是否正确
        import base64
        from core.ocr_reader import _call
        tiny_png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
            "z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
        )
        _call(sid, skey, "GeneralBasicOCR", {"ImageBase64": tiny_png})
        return jsonify({"ok": True, "msg": "连接成功，凭证有效"})
    except Exception as e:
        msg = str(e)
        # 签名正确但图片无效也算连接成功
        if "ImageSizeTooSmall" in msg or "image" in msg.lower():
            return jsonify({"ok": True, "msg": "连接成功，凭证有效"})
        return jsonify({"ok": False, "msg": msg})

@bp.route("/test-ai", methods=["POST"])
def test_ai():
    try:
        import requests as req
        api_key  = CONFIG.get("ai_api_key", "")
        base_url = CONFIG.get("ai_base_url", "https://api.deepseek.com")
        model    = CONFIG.get("ai_model", "deepseek-chat")
        if not api_key:
            return jsonify({"ok": False, "msg": "API Key 未设置"})
        resp = req.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": "你好"}], "max_tokens": 5},
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify({"ok": True, "msg": "连接成功"})
        return jsonify({"ok": False, "msg": f"HTTP {resp.status_code}"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})
