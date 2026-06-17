"""OCR识别模块 — 腾讯云OCR（身份证/学历证/通用）"""
from __future__ import annotations
import base64, hashlib, hmac, json, re, time
from datetime import datetime, timezone
from pathlib import Path

import requests


# ── 腾讯云签名 v3 ─────────────────────────────────────────────────

def _sign_v3(secret_id: str, secret_key: str, service: str,
             action: str, payload: dict, region: str = "ap-guangzhou") -> dict:
    """Generate Tencent Cloud API v3 signed request headers."""
    host    = f"{service}.tencentcloudapi.com"
    payload_str = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    payload_bytes = payload_str.encode("utf-8")

    timestamp = int(time.time())
    date      = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")

    # Canonical request
    canonical_headers = f"content-type:application/json\nhost:{host}\n"
    signed_headers    = "content-type;host"
    hashed_payload    = hashlib.sha256(payload_bytes).hexdigest()
    canonical_request = "\n".join([
        "POST", "/", "",
        canonical_headers, signed_headers, hashed_payload,
    ])

    # String to sign
    algorithm    = "TC3-HMAC-SHA256"
    cred_scope   = f"{date}/{service}/tc3_request"
    hashed_cr    = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = "\n".join([algorithm, str(timestamp), cred_scope, hashed_cr])

    # Signing key
    def _hmac(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    secret_date    = _hmac(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = _hmac(secret_date, service)
    secret_signing = _hmac(secret_service, "tc3_request")
    signature      = hmac.new(secret_signing, string_to_sign.encode("utf-8"),
                               hashlib.sha256).hexdigest()

    authorization = (
        f"{algorithm} Credential={secret_id}/{cred_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    return {
        "Authorization":   authorization,
        "Content-Type":    "application/json",
        "Host":            host,
        "X-TC-Action":     action,
        "X-TC-Timestamp":  str(timestamp),
        "X-TC-Version":    "2018-11-19",
        "X-TC-Region":     region,
    }


def _call(secret_id: str, secret_key: str, action: str, payload: dict) -> dict:
    """Call Tencent OCR API and return parsed JSON response."""
    headers = _sign_v3(secret_id, secret_key, "ocr", action, payload)
    resp = requests.post(
        "https://ocr.tencentcloudapi.com",
        headers=headers,
        data=json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
        timeout=15,
    )
    resp.raise_for_status()
    body = resp.json()
    if "Response" not in body:
        raise RuntimeError(f"腾讯云OCR响应异常：{body}")
    if "Error" in body["Response"]:
        err = body["Response"]["Error"]
        raise RuntimeError(f"腾讯云OCR错误 [{err['Code']}]：{err['Message']}")
    return body["Response"]


def _img_b64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ── 公开接口 ──────────────────────────────────────────────────────

def recognize_id_card(image_path: str, secret_id: str, secret_key: str,
                      card_side: str = "FRONT") -> dict:
    """
    身份证识别（IDCardOCR）。
    card_side: "FRONT"=正面（含姓名身份证号）, "BACK"=背面
    返回结构化字段 dict。
    """
    payload = {
        "ImageBase64": _img_b64(image_path),
        "CardSide": card_side,
        "Config": json.dumps({"CropIdCard": False, "CropPortrait": False}),
    }
    data = _call(secret_id, secret_key, "IDCardOCR", payload)

    if card_side == "FRONT":
        return {
            "name":       data.get("Name", ""),
            "gender":     data.get("Sex", ""),
            "nation":     data.get("Nation", ""),
            "birth_date": data.get("Birth", "").replace("/", "-"),
            "address":    data.get("Address", ""),
            "id_card":    data.get("IdNum", ""),
        }
    else:
        return {
            "authority":  data.get("Authority", ""),
            "valid_date": data.get("ValidDate", ""),
        }


def recognize_degree_cert(image_path: str, secret_id: str, secret_key: str) -> dict:
    """
    学历证书识别（通用精准OCR + 结构化解析）。
    腾讯云无专用学历接口，使用 GeneralAccurateOCR 后正则解析。
    """
    payload = {"ImageBase64": _img_b64(image_path)}
    data = _call(secret_id, secret_key, "GeneralAccurateOCR", payload)

    lines = [item["DetectedText"] for item in data.get("TextDetections", [])]
    full  = " ".join(lines)
    return _parse_degree_text(full)


def recognize_general(image_path: str, secret_id: str, secret_key: str) -> dict:
    """通用文字识别，返回 {text: str, lines: list}"""
    payload = {"ImageBase64": _img_b64(image_path)}
    data = _call(secret_id, secret_key, "GeneralAccurateOCR", payload)
    lines = [item["DetectedText"] for item in data.get("TextDetections", [])]
    return {"text": "\n".join(lines), "lines": lines}


# ── 本地解析辅助 ─────────────────────────────────────────────────

def _parse_degree_text(full: str) -> dict:
    result: dict = {}

    for edu in ["博士研究生", "硕士研究生", "本科", "大专", "专科"]:
        if edu in full:
            result["education"] = edu.replace("研究生", "")
            break

    m = re.search(r"专业[名称：:\s]*([^\s，。,、]{2,16})", full)
    if m:
        result["major"] = m.group(1).strip()

    m = re.search(r"([一-龥]{2,15}(?:大学|学院|学校|职业技术))", full)
    if m:
        result["school"] = m.group(1)

    m = re.search(r"(\d{4})\s*年", full)
    if m:
        result["grad_year"] = m.group(1)

    return result


# ── 兼容旧接口（供 routes/ocr.py 调用）──────────────────────────

def get_credentials() -> tuple[str, str]:
    """Load SecretId/SecretKey from config."""
    from config import CONFIG
    return CONFIG.get("tencent_secret_id", ""), CONFIG.get("tencent_secret_key", "")


def is_available() -> bool:
    sid, skey = get_credentials()
    return bool(sid and skey)


def recognize(image_path: str) -> str:
    """通用识别，返回纯文本（向后兼容）。"""
    sid, skey = get_credentials()
    if not sid or not skey:
        raise RuntimeError("腾讯云OCR未配置，请在系统设置中填写 SecretId 和 SecretKey")
    result = recognize_general(image_path, sid, skey)
    return result["text"]


def parse_id_card(text: str) -> dict:
    """从纯文本解析身份证字段（fallback，正常走 recognize_id_card）。"""
    result: dict = {}
    full = " ".join(text.splitlines())
    m = re.search(r"\b(\d{17}[\dXx])\b", full)
    if m:
        result["id_card"] = m.group(1).upper()
    m = re.search(r"姓名[：:\s]*([^\s]{2,5})", full)
    if m:
        result["name"] = m.group(1)
    if "男" in full:
        result["gender"] = "男"
    elif "女" in full:
        result["gender"] = "女"
    m = re.search(r"(\d{4})[年/](\d{1,2})[月/](\d{1,2})", full)
    if m:
        result["birth_date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return result


def parse_degree_cert(text: str) -> dict:
    return _parse_degree_text(" ".join(text.splitlines()))


def parse_title_cert(text: str) -> dict:
    full = " ".join(text.splitlines())
    result: dict = {}
    for level in ["正高级工程师", "高级工程师", "工程师", "助理工程师"]:
        if level in full:
            result["title_level"] = level
            break
    m = re.search(r"(\d{4})\s*年", full)
    if m:
        result["title_year"] = m.group(1)
    return result
