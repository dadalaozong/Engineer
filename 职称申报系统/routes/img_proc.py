import os, tempfile, base64
from flask import Blueprint, render_template, request, jsonify
from config import load_config
from core.crypto import decrypt
from core.img_processor import enhance_scan, deskew, remove_background, upscale_image, aliyun_enhance

bp = Blueprint("img_proc", __name__, url_prefix="/img")

OPERATIONS = [
    ("enhance",    "扫描件增强"),
    ("deskew",     "图像纠偏"),
    ("remove_bg",  "背景移除"),
    ("upscale",    "图像超分"),
    ("aliyun",     "阿里云增强"),
]

@bp.route("/")
def index_page():
    return render_template("img/index.html", operations=OPERATIONS)

@bp.route("/process", methods=["POST"])
def process():
    if "file" not in request.files:
        return jsonify({"error": "未上传文件"}), 400
    f   = request.files["file"]
    op  = request.form.get("op", "enhance")
    suffix = os.path.splitext(f.filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        f.save(tmp.name)
        inp = tmp.name
    out = inp + "_out" + suffix
    try:
        cfg = load_config()
        img_cfg = cfg.get("img_apis", cfg.get("image_api", {}))
        if op == "enhance":
            enhance_scan(inp, out)
        elif op == "deskew":
            deskew(inp, out)
        elif op == "remove_bg":
            key = decrypt(img_cfg.get("remove_bg_key_cipher", "")) or img_cfg.get("remove_bg_key", "")
            remove_background(inp, out, api_key=key)
        elif op == "upscale":
            key = decrypt(img_cfg.get("clipdrop_key_cipher", "")) or img_cfg.get("clipdrop_key", "")
            upscale_image(inp, out, api_key=key)
        elif op == "aliyun":
            key = decrypt(img_cfg.get("aliyun_key_cipher", "")) or img_cfg.get("aliyun_key", "")
            aliyun_enhance(inp, out, api_key=key)
        with open(out, "rb") as img_f:
            b64 = base64.b64encode(img_f.read()).decode()
        mime = "image/png" if suffix.lower() == ".png" else "image/jpeg"
        return jsonify({"image": f"data:{mime};base64,{b64}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for p in [inp, out]:
            try: os.unlink(p)
            except: pass
