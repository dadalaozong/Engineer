from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from config import CONFIG
try:
    from config import save_config
except ImportError:
    save_config = None

bp = Blueprint("settings", __name__, url_prefix="/settings")

@bp.route("/")
def index_page():
    return render_template("settings/index.html", config=CONFIG)

@bp.route("/website", methods=["POST"])
def save_website():
    CONFIG["website_url"] = request.form.get("website_url", "")
    CONFIG["username"] = request.form.get("username", "")
    CONFIG["password"] = request.form.get("password", "")
    if save_config:
        save_config(CONFIG)
    flash("网站账号已保存", "success")
    return redirect(url_for("settings.index_page"))

@bp.route("/ai", methods=["POST"])
def save_ai():
    CONFIG["ai_api_key"] = request.form.get("ai_api_key", "")
    CONFIG["ai_model"] = request.form.get("ai_model", "deepseek-chat")
    CONFIG["ai_base_url"] = request.form.get("ai_base_url", "")
    if save_config:
        save_config(CONFIG)
    flash("AI设置已保存", "success")
    return redirect(url_for("settings.index_page"))

@bp.route("/image-api", methods=["POST"])
def save_image_api():
    CONFIG["image_api_key"] = request.form.get("image_api_key", "")
    CONFIG["image_api_url"] = request.form.get("image_api_url", "")
    if save_config:
        save_config(CONFIG)
    flash("图像API设置已保存", "success")
    return redirect(url_for("settings.index_page"))

@bp.route("/test-ai", methods=["POST"])
def test_ai():
    try:
        import httpx
        api_key = CONFIG.get("ai_api_key", "")
        base_url = CONFIG.get("ai_base_url", "https://api.deepseek.com")
        model = CONFIG.get("ai_model", "deepseek-chat")
        if not api_key:
            return jsonify({"ok": False, "msg": "API Key 未设置"})
        resp = httpx.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": "你好"}], "max_tokens": 10},
            timeout=10,
        )
        if resp.status_code == 200:
            return jsonify({"ok": True, "msg": "连接成功"})
        else:
            return jsonify({"ok": False, "msg": f"HTTP {resp.status_code}: {resp.text[:200]}"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})
