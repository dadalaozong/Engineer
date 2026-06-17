"""OCR识别模块 — 优先使用 PaddleOCR，不可用时降级到提示。"""
from __future__ import annotations
from pathlib import Path
import re

_paddle_available = False
_ocr_instance = None


def _get_ocr():
    global _paddle_available, _ocr_instance
    if _ocr_instance is not None:
        return _ocr_instance
    try:
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        _paddle_available = True
        return _ocr_instance
    except ImportError:
        return None


def is_available() -> bool:
    return _get_ocr() is not None


def recognize(image_path: str) -> str:
    """Run OCR on image_path, return full text joined by newlines."""
    ocr = _get_ocr()
    if ocr is None:
        raise RuntimeError(
            "PaddleOCR 未安装。\n请运行：pip install paddlepaddle paddleocr"
        )
    result = ocr.ocr(image_path, cls=True)
    lines = []
    for block in result:
        if block:
            for line in block:
                if line and len(line) >= 2:
                    lines.append(line[1][0])
    return "\n".join(lines)


# ── 结构化解析 ────────────────────────────────────────────────────

def parse_id_card(text: str) -> dict:
    """Extract key fields from ID card OCR text."""
    result = {}
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    full = " ".join(lines)

    # 身份证号：18位数字或17位数字+X
    m = re.search(r"\b(\d{17}[\dXx])\b", full)
    if m:
        result["id_card"] = m.group(1).upper()

    # 姓名：通常在"姓名"后面一行
    for i, line in enumerate(lines):
        if "姓名" in line:
            name_part = line.replace("姓名", "").strip()
            if name_part:
                result["name"] = name_part
            elif i + 1 < len(lines):
                result["name"] = lines[i + 1]
            break

    # 性别
    if "男" in full:
        result["gender"] = "男"
    elif "女" in full:
        result["gender"] = "女"

    # 出生日期
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", full)
    if m:
        result["birth_date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    return result


def parse_degree_cert(text: str) -> dict:
    """Extract key fields from graduation certificate OCR text."""
    result = {}
    full = " ".join(text.splitlines())

    # 学历
    for edu in ["博士研究生", "硕士研究生", "本科", "大专", "专科", "中专", "高中"]:
        if edu in full:
            result["education"] = edu.replace("研究生", "")
            break

    # 专业
    m = re.search(r"专业[：:]\s*([^\s，。]{2,12})", full)
    if m:
        result["major"] = m.group(1)

    # 毕业院校
    m = re.search(r"([一-龥]{2,15}(?:大学|学院|学校|职业技术))", full)
    if m:
        result["school"] = m.group(1)

    # 毕业年份
    m = re.search(r"(\d{4})年", full)
    if m:
        result["grad_year"] = m.group(1)

    return result


def parse_title_cert(text: str) -> dict:
    """Extract key fields from existing professional title certificate."""
    result = {}
    full = " ".join(text.splitlines())

    for level in ["正高级工程师", "高级工程师", "工程师", "助理工程师", "技术员"]:
        if level in full:
            result["current_level"] = level
            break

    m = re.search(r"(\d{4})年", full)
    if m:
        result["issue_year"] = m.group(1)

    m = re.search(r"专业[：:]\s*([^\s，。]{2,12})", full)
    if m:
        result["specialty"] = m.group(1)

    return result
