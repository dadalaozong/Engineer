"""建筑工程行业 — gxrczc.com 表单填报插件。"""
from __future__ import annotations


# 行业/评委会 → 网站下拉选项映射（按实际网站选项调整）
INDUSTRY_MAP = {
    "建筑工程":  "建设行业",
    "市政公用":  "建设行业",
    "装饰装修":  "建设行业",
    "机电安装":  "建设行业",
    "公路工程":  "交通运输行业",
}

COMMITTEE_MAP = {
    "广西建筑工程系列评委会": "建筑工程",
    "广西市政公用评委会":     "市政公用工程",
    "广西公路工程系列评委会": "公路工程",
}

LEVEL_MAP = {
    "中级工程师":   "工程师（中级）",
    "高级工程师":   "高级工程师",
    "正高级工程师": "正高级工程师",
}

EDUCATION_MAP = {
    "高中/中专": "中专",
    "大专":      "专科",
    "本科":      "本科",
    "硕士":      "硕士",
    "博士":      "博士",
}


def select_industry_and_committee(page, industry: str, committee: str) -> dict[str, bool]:
    """
    On gxrczc.com: select industry type and committee after login.
    Returns {step: success}.
    """
    results = {}

    # 1. select 行业大类
    site_industry = INDUSTRY_MAP.get(industry, industry)
    for sel in ['select[name="industry"]', '#industrySelect', 'select:near(:text("行业"))']:
        try:
            page.select_option(sel, label=site_industry, timeout=4_000)
            results["select_industry"] = True
            break
        except Exception:
            results["select_industry"] = False

    page.wait_for_timeout(800)

    # 2. select 评委会
    site_committee = COMMITTEE_MAP.get(committee, committee)
    for sel in ['select[name="committee"]', '#committeeSelect', 'select:near(:text("评委会"))']:
        try:
            page.select_option(sel, label=site_committee, timeout=4_000)
            results["select_committee"] = True
            break
        except Exception:
            results["select_committee"] = False

    page.wait_for_timeout(500)

    # 3. select 申报级别
    return results


def fill_basic_info(page, applicant: dict, project: dict) -> dict[str, bool]:
    """Fill basic applicant info on the form page."""
    results = {}
    level = project.get("apply_level", "")
    site_level = LEVEL_MAP.get(level, level)
    site_edu   = EDUCATION_MAP.get(applicant.get("education", ""), applicant.get("education", ""))

    field_map = [
        # (field_key_in_db, possible_selectors, value)
        ("name",     ['input[name="name"]', '#applyName', 'input[placeholder*="姓名"]'],
                     applicant.get("name", "")),
        ("id_card",  ['input[name="idCard"]', '#idCard', 'input[placeholder*="身份证"]'],
                     applicant.get("id_card", "") or ""),
        ("phone",    ['input[name="phone"]', '#phone', 'input[placeholder*="电话"]'],
                     applicant.get("phone", "") or ""),
        ("work_unit",['input[name="workUnit"]', '#workUnit', 'input[placeholder*="单位"]'],
                     applicant.get("work_unit", "") or ""),
        ("major",    ['input[name="major"]', '#major', 'input[placeholder*="专业"]'],
                     applicant.get("major", "") or ""),
    ]

    for key, selectors, value in field_map:
        if not value:
            continue
        ok = False
        for sel in selectors:
            try:
                page.fill(sel, value, timeout=3_000)
                ok = True
                break
            except Exception:
                continue
        results[key] = ok

    # select fields
    for sel_key, selectors, value in [
        ("education", ['select[name="education"]', '#education'], site_edu),
        ("apply_level", ['select[name="applyLevel"]', '#applyLevel'], site_level),
    ]:
        ok = False
        for sel in selectors:
            try:
                page.select_option(sel, label=value, timeout=3_000)
                ok = True
                break
            except Exception:
                continue
        results[sel_key] = ok

    return results
