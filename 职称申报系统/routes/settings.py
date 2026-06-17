from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from config import load_config, save_config
from core.crypto import encrypt, decrypt

bp = Blueprint("settings", __name__, url_prefix="/settings")

@bp.route("/")
def index_page():
    cfg = load_config()
    return render_template("settings/index.html", cfg=cfg)

@bp.route("/website", methods=["POST"])
def save_website():
    cfg = load_config()
    cfg["website"]["username"] = request.form.get("username", "").strip()
    pw = request.form.get("password", "").strip()
    if pw:
        cfg["website"]["password_cipher"] = encrypt(pw)
    save_config(cfg)
    flash("网站账号已保存", "success")
    return redirect(url_for("settings.index_page"))

@bp.route("/ai", methods=["POST"])
def save_ai():
    cfg = load_config()
    cfg["ai"]["model"]    = request.form.get("model", "deepseek-chat").strip()
    cfg["ai"]["base_url"] = request.form.get("base_url", "https://api.deepseek.com").strip()
    key = request.form.get("api_key", "").strip()
    if key:
        cfg["ai"]["api_key_cipher"] = encrypt(key)
    save_config(cfg)
    flash("AI配置已保存", "success")
    return redirect(url_for("settings.index_page"))

@bp.route("/image-api", methods=["POST"])
def save_image_api():
    cfg = load_config()
    if "img_apis" not in cfg:
        cfg["img_apis"] = {}
    for field in ["remove_bg_key", "clipdrop_key", "aliyun_key"]:
        val = request.form.get(field, "").strip()
        if val:
            cfg["img_apis"][field + "_cipher"] = encrypt(val)
    save_config(cfg)
    flash("图像API配置已保存", "success")
    return redirect(url_for("settings.index_page"))

@bp.route("/test-ai", methods=["POST"])
def test_ai():
    cfg = load_config()
    key      = decrypt(cfg["ai"].get("api_key_cipher", "")) or cfg["ai"].get("deepseek_api_key", "")
    model    = cfg["ai"].get("model", "deepseek-chat")
    base_url = cfg["ai"].get("base_url", "https://api.deepseek.com")
    if not key:
        return jsonify({"ok": False, "msg": "未配置API Key"})
    try:
        from core.ai_writer import AIWriter
        writer = AIWriter(api_key=key, model=model, base_url=base_url)
        result = writer.generate("work_summary", {"test": True,
                                  "prompt": "请回复'连接成功'三个字。"})
        return jsonify({"ok": True, "msg": result[:50]})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})
