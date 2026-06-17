from pathlib import Path
import json

APP_NAME = "职称申报系统"
APP_VERSION = "1.0.0"

DATA_DIR = Path.home() / ".zcsbxt"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "data.db"
KEY_PATH = DATA_DIR / "secret.key"
CONFIG_PATH = DATA_DIR / "config.json"

_DEFAULT_CONFIG = {
    "ai": {
        "deepseek_api_key": "",
        "model": "deepseek-chat"
    },
    "img_apis": {
        "remove_bg_key": "",
        "clipdrop_key": "",
        "aliyun_key": "",
        "tencent_key": ""
    },
    "website": {
        "url": "https://www.gxrczc.com",
        "username": "",
        "password_cipher": ""
    }
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        save_config(_DEFAULT_CONFIG)
        return _DEFAULT_CONFIG
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # merge missing keys from defaults
    for k, v in _DEFAULT_CONFIG.items():
        if k not in data:
            data[k] = v
        elif isinstance(v, dict):
            for kk, vv in v.items():
                if kk not in data[k]:
                    data[k][kk] = vv
    return data


def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
