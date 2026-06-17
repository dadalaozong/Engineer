import json, os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

_defaults = {
    "website_url": "",
    "username": "",
    "password": "",
    "ai_api_key": "",
    "ai_model": "deepseek-chat",
    "ai_base_url": "https://api.deepseek.com",
    "image_api_key": "",
    "image_api_url": "",
    "docs_folder": "",
    "tencent_secret_id": "",
    "tencent_secret_key": "",
    "tencent_ocr_region": "ap-guangzhou",
}

def _load():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = dict(_defaults)
                merged.update(data)
                return merged
        except Exception:
            pass
    return dict(_defaults)

CONFIG = _load()

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
