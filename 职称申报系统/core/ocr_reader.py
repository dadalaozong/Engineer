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


def recognize_title_cert(image_path: str, secret_id: str, secret_key: str) -> dict:
    """职称证书识别（通用OCR + 结构化解析）。"""
    payload = {"ImageBase64": _img_b64(image_path)}
    data = _call(secret_id, secret_key, "GeneralAccurateOCR", payload)
    lines = [item["DetectedText"] for item in data.get("TextDetections", [])]
    full = " ".join(lines)
    return _parse_title_text(full)


def recognize_pro_cert(image_path: str, secret_id: str, secret_key: str) -> dict:
    """执业资格证书识别（通用OCR + 结构化解析）。"""
    payload = {"ImageBase64": _img_b64(image_path)}
    data = _call(secret_id, secret_key, "GeneralAccurateOCR", payload)
    lines = [item["DetectedText"] for item in data.get("TextDetections", [])]
    full = " ".join(lines)
    return _parse_pro_cert_text(full)


def recognize_social_insurance(image_path: str, secret_id: str, secret_key: str) -> dict:
    """社保记录截图识别 — 返回参保段落列表。"""
    payload = {"ImageBase64": _img_b64(image_path)}
    data = _call(secret_id, secret_key, "GeneralAccurateOCR", payload)
    lines = [item["DetectedText"] for item in data.get("TextDetections", [])]
    full = "\n".join(lines)
    return {"raw": full, "segments": _parse_insurance_segments(full)}


def _parse_title_text(full: str) -> dict:
    result: dict = {}
    for level in ["正高级工程师", "高级工程师", "工程师", "助理工程师"]:
        if level in full:
            result["title_level"] = level
            break
    m = re.search(r"专业[名称：:\s]*([^\s，。,、]{2,20})", full)
    if m:
        result["title_specialty"] = m.group(1).strip()
    m = re.search(r"证书编号[：:\s]*([A-Za-z0-9\-]{4,30})", full)
    if m:
        result["title_cert_no"] = m.group(1).strip()
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", full)
    if m:
        result["title_year"]  = m.group(1)
        result["title_month"] = f"{m.group(1)}-{int(m.group(2)):02d}"
    elif re.search(r"\d{4}", full):
        result["title_year"] = re.search(r"(\d{4})", full).group(1)
    m = re.search(r"发证机关[：:\s]*([^\s，。]{3,20})", full)
    if m:
        result["title_issuer"] = m.group(1).strip()
    return result


def _parse_pro_cert_text(full: str) -> dict:
    result: dict = {}
    for ct in ["注册建造师", "注册结构工程师", "注册建筑师", "注册监理工程师",
               "注册造价工程师", "注册安全工程师", "注册岩土工程师"]:
        if ct in full:
            result["cert_type"] = ct
            break
    m = re.search(r"注册号[：:\s]*([A-Za-z0-9\-]{4,30})", full)
    if m:
        result["reg_no"] = m.group(1).strip()
    m = re.search(r"证书编号[：:\s]*([A-Za-z0-9\-]{4,30})", full)
    if m:
        result["cert_no"] = m.group(1).strip()
    m = re.search(r"专业[：:\s]*([^\s，。,、]{2,20})", full)
    if m:
        result["specialty"] = m.group(1).strip()
    m = re.search(r"有效期[至到：:\s]*(\d{4}[-年]\d{1,2}[-月]\d{0,2})", full)
    if m:
        raw = m.group(1)
        raw = re.sub(r"[年月]", "-", raw).rstrip("-")
        parts = raw.split("-")
        if len(parts) >= 2:
            result["valid_until"] = f"{parts[0]}-{int(parts[1]):02d}-{'01' if len(parts)<3 else f'{int(parts[2]):02d}'}"
    return result


def _parse_insurance_segments(full: str) -> list:
    """尝试从社保截图中解析参保段落，返回 [{insure_start, insure_end, insure_unit}]"""
    segments = []
    pattern = re.compile(
        r"(\d{4}[-年/]\d{1,2}[-月/]?\d{0,2})\s*[~至—-]+\s*(\d{4}[-年/]\d{1,2}[-月/]?\d{0,2})"
    )
    for m in pattern.finditer(full):
        def norm(s):
            s = re.sub(r"[年月/]", "-", s).rstrip("-")
            parts = s.split("-")
            if len(parts) >= 2:
                return f"{parts[0]}-{int(parts[1]):02d}"
            return s
        segments.append({
            "insure_start": norm(m.group(1)),
            "insure_end":   norm(m.group(2)),
        })
    return segments


def parse_title_cert(text: str) -> dict:
    full = " ".join(text.splitlines())
    return _parse_title_text(full)


# ── 继续教育证明 ───────────────────────────────────────────────────

def recognize_edu_training(image_path: str, secret_id: str, secret_key: str) -> dict:
    """继续教育/培训证明识别。"""
    payload = {"ImageBase64": _img_b64(image_path)}
    data = _call(secret_id, secret_key, "GeneralAccurateOCR", payload)
    lines = [item["DetectedText"] for item in data.get("TextDetections", [])]
    full = " ".join(lines)
    return _parse_edu_training_text(full)


def _parse_edu_training_text(full: str) -> dict:
    result: dict = {}

    # 课程/培训名称
    m = re.search(r"(?:培训|课程|学习)名称[：:\s]*([^，。\n]{4,40})", full)
    if m:
        result["course_name"] = m.group(1).strip()
    else:
        m = re.search(r"《([^》]{3,40})》", full)
        if m:
            result["course_name"] = m.group(1)
        else:
            for token in full.split():
                if len(token) >= 6 and re.search(r"[一-鿿]{4,}", token):
                    result["course_name"] = token[:40]
                    break

    # 学时/学分
    m = re.search(r"(\d+)\s*(?:学时|课时|小时)", full)
    if m:
        result["hours"] = int(m.group(1))

    # 起止日期
    dates = re.findall(r"(\d{4}[-年/]\d{1,2}[-月/]?\d{0,2})", full)
    if len(dates) >= 2:
        result["train_start"] = _norm_date(dates[0])
        result["train_end"]   = _norm_date(dates[1])
    elif len(dates) == 1:
        result["train_start"] = _norm_date(dates[0])

    # 发证/培训机构
    m = re.search(r"(?:主办单位|培训单位|发证机关|颁发单位|组织单位)[：:\s]*([^\s，。]{3,30})", full)
    if m:
        result["issuer"] = m.group(1).strip()

    return result


# ── 工程业绩证明 ───────────────────────────────────────────────────

def recognize_achievement(image_path: str, secret_id: str, secret_key: str) -> dict:
    """工程业绩证明/施工合同识别。"""
    payload = {"ImageBase64": _img_b64(image_path)}
    data = _call(secret_id, secret_key, "GeneralAccurateOCR", payload)
    lines = [item["DetectedText"] for item in data.get("TextDetections", [])]
    full = " ".join(lines)
    return _parse_achievement_text(full)


def _parse_achievement_text(full: str) -> dict:
    result: dict = {}

    # 工程名称
    m = re.search(r"(?:工程名称|项目名称)[：:\s]*([^\s，。]{4,40})", full)
    if m:
        result["project_name"] = m.group(1).strip()
    else:
        # 找含"工程"/"项目"的名词短语
        m = re.search(r"([一-龥]{2,20}(?:工程|项目|大厦|楼|路|桥|隧道|管道))", full)
        if m:
            result["project_name"] = m.group(1)

    # 工程类型
    for pt in ["房屋建筑", "市政公用", "公路工程", "装饰装修", "机电安装",
               "桥梁", "隧道", "给排水", "电力", "通信"]:
        if pt in full:
            result["project_type"] = pt
            break

    # 担任职务/角色
    m = re.search(r"(?:担任|职务|岗位)[：:\s]*([^\s，。]{2,15})", full)
    if m:
        result["role"] = m.group(1).strip()
    else:
        for role in ["项目经理", "技术负责人", "项目总工", "施工员", "监理工程师"]:
            if role in full:
                result["role"] = role
                break

    # 建设规模/合同金额
    m = re.search(r"(?:规模|建筑面积|合同金额|造价)[：:\s]*([^\s，。]{2,20})", full)
    if m:
        result["scale"] = m.group(1).strip()

    # 起止年份
    dates = re.findall(r"(\d{4}[-年/]\d{1,2}[-月/]?\d{0,2})", full)
    if len(dates) >= 2:
        result["start_date"] = _norm_date(dates[0])
        result["end_date"]   = _norm_date(dates[1])
    elif len(dates) == 1:
        result["start_date"] = _norm_date(dates[0])

    # 证明单位
    m = re.search(r"(?:建设单位|发证单位|合同甲方)[：:\s]*([^\s，。]{3,30})", full)
    if m:
        result["issuer"] = m.group(1).strip()

    return result


# ── 获奖证书 ────────────────────────────────────────────────────────

def recognize_award(image_path: str, secret_id: str, secret_key: str) -> dict:
    """获奖证书识别。"""
    payload = {"ImageBase64": _img_b64(image_path)}
    data = _call(secret_id, secret_key, "GeneralAccurateOCR", payload)
    lines = [item["DetectedText"] for item in data.get("TextDetections", [])]
    full = " ".join(lines)
    return _parse_award_text(full)


def _parse_award_text(full: str) -> dict:
    result: dict = {}

    # 奖项名称
    m = re.search(r"(?:荣获|获得|授予)[：:\s]*([^\s，。]{3,30})", full)
    if m:
        result["award_name"] = m.group(1).strip()
    else:
        m = re.search(r"([一-龥]{2,20}(?:奖|荣誉|称号))", full)
        if m:
            result["award_name"] = m.group(1)

    # 奖励级别
    for lvl in ["国家级", "省部级", "厅局级", "市级", "县级", "企业级"]:
        if lvl in full:
            result["award_level"] = lvl
            break
    if "award_level" not in result:
        for lvl in ["一等奖", "二等奖", "三等奖", "特等奖", "优秀奖"]:
            if lvl in full:
                result["award_level"] = lvl
                break

    # 颁奖时间
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", full)
    if m:
        result["award_date"] = f"{m.group(1)}-{int(m.group(2)):02d}"
    elif re.search(r"\d{4}", full):
        result["award_date"] = re.search(r"(\d{4})", full).group(1)

    # 颁发单位
    m = re.search(r"(?:颁发单位|授予单位|颁发机关)[：:\s]*([^\s，。]{3,30})", full)
    if m:
        result["award_org"] = m.group(1).strip()

    return result


# ── 论文/著作 ───────────────────────────────────────────────────────

def recognize_paper(image_path: str, secret_id: str, secret_key: str) -> dict:
    """论文/著作封面或收录证明识别。"""
    payload = {"ImageBase64": _img_b64(image_path)}
    data = _call(secret_id, secret_key, "GeneralAccurateOCR", payload)
    lines = [item["DetectedText"] for item in data.get("TextDetections", [])]
    full = " ".join(lines)
    return _parse_paper_text(full)


def _parse_paper_text(full: str) -> dict:
    result: dict = {}

    # 论文标题（通常是最长的中文短语）
    candidates = [t for t in full.split() if len(t) >= 6 and re.search(r"[一-鿿]{4,}", t)]
    if candidates:
        result["title"] = max(candidates, key=len)[:60]

    # 期刊/出版社
    m = re.search(r"(?:发表于|刊登于|期刊|杂志|出版社)[：:\s]*([^\s，。]{3,30})", full)
    if m:
        result["journal"] = m.group(1).strip()
    else:
        for kw in ["学报", "期刊", "杂志", "Journal", "出版社"]:
            idx = full.find(kw)
            if idx >= 0:
                result["journal"] = full[max(0, idx-10):idx+len(kw)].strip()
                break

    # 发表时间
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", full)
    if m:
        result["publish_date"] = f"{m.group(1)}-{int(m.group(2)):02d}"
    elif re.search(r"\d{4}", full):
        result["publish_date"] = re.search(r"(\d{4})", full).group(1)

    # ISSN/ISBN/DOI
    m = re.search(r"ISSN\s*[：:]?\s*([\d\-X]{8,})", full, re.I)
    if m:
        result["issn"] = m.group(1)
    m = re.search(r"ISBN\s*[：:]?\s*([\d\-X]{10,})", full, re.I)
    if m:
        result["isbn"] = m.group(1)
    m = re.search(r"DOI\s*[：:]?\s*(10\.\S+)", full, re.I)
    if m:
        result["doi"] = m.group(1)

    # 作者
    m = re.search(r"(?:作者|著者|Author)[：:\s]*([^\s，。]{2,20})", full)
    if m:
        result["authors"] = m.group(1).strip()

    return result


# ── 年度考核表 ─────────────────────────────────────────────────────

def recognize_annual_review(image_path: str, secret_id: str, secret_key: str) -> dict:
    """年度考核表识别。"""
    payload = {"ImageBase64": _img_b64(image_path)}
    data = _call(secret_id, secret_key, "GeneralAccurateOCR", payload)
    lines = [item["DetectedText"] for item in data.get("TextDetections", [])]
    full = " ".join(lines)
    return _parse_annual_review_text(full)


def _parse_annual_review_text(full: str) -> dict:
    result: dict = {}

    # 考核年度
    m = re.search(r"(\d{4})\s*年(?:度|份)?考核", full)
    if m:
        result["review_year"] = m.group(1)
    else:
        m = re.search(r"(\d{4})", full)
        if m:
            result["review_year"] = m.group(1)

    # 考核结果
    for grade in ["优秀", "良好", "合格", "基本合格", "不合格"]:
        if grade in full:
            result["review_result"] = grade
            break

    # 考核单位
    m = re.search(r"(?:考核单位|填报单位|单位名称)[：:\s]*([^\s，。]{3,30})", full)
    if m:
        result["review_unit"] = m.group(1).strip()

    return result


# ── 通用日期规范化 ─────────────────────────────────────────────────

def _norm_date(s: str) -> str:
    """将 '2020年3月' / '2020/3/1' 等规范化为 'YYYY-MM'"""
    s = re.sub(r"[年月/]", "-", s).rstrip("-")
    parts = [p for p in s.split("-") if p]
    if len(parts) >= 2:
        try:
            return f"{parts[0]}-{int(parts[1]):02d}"
        except ValueError:
            return s
    return s
