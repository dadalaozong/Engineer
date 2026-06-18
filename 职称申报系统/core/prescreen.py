"""资格预审引擎 — 根据申报人数据自动检查申报条件，返回结构化结果"""
from __future__ import annotations
from datetime import date
from typing import NamedTuple


class CheckItem(NamedTuple):
    name:    str        # 检查项名称
    passed:  bool       # 是否通过
    detail:  str        # 说明
    level:   str        # "must" 必须项 / "warn" 建议项


def _months_since(year_month: str) -> int:
    """计算从 YYYY-MM 到今天的月数（从次月起算）。"""
    try:
        y, m = int(year_month[:4]), int(year_month[5:7])
        m += 1
        if m > 12:
            y += 1; m = 1
        today = date.today()
        return max(0, (today.year - y) * 12 + (today.month - m))
    except Exception:
        return 0


def _parse_year(s: str) -> int | None:
    import re
    m = re.search(r"\d{4}", str(s or ""))
    return int(m.group()) if m else None


def prescreen(applicant: dict, project: dict,
              achievements: list, awards: list, papers: list,
              insurances: list, edu_trainings: list) -> list[CheckItem]:
    """
    运行全部检查项，返回 CheckItem 列表。
    """
    items: list[CheckItem] = []
    apply_level = project.get("apply_level", "") or ""

    # ── 1. 学历要求 ────────────────────────────────────────────────
    edu = applicant.get("education", "") or ""
    edu_rank = {"大专": 1, "本科": 2, "硕士": 3, "博士": 4}.get(edu, 0)
    if apply_level in ("高级工程师", "正高级工程师"):
        edu_ok = edu_rank >= 2   # 本科及以上
        items.append(CheckItem(
            "学历要求", edu_ok,
            f"现学历：{edu or '未填'}（申报{apply_level}需本科及以上）",
            "must"
        ))
    elif apply_level == "工程师":
        edu_ok = edu_rank >= 1
        items.append(CheckItem(
            "学历要求", edu_ok,
            f"现学历：{edu or '未填'}（申报工程师需大专及以上）",
            "must"
        ))

    # ── 2. 资历年限 ────────────────────────────────────────────────
    title_month = applicant.get("title_month", "") or ""
    title_year  = applicant.get("title_year", "")  or ""
    title_level = applicant.get("title_level", "") or ""

    start_ym = None
    if title_month and len(title_month) >= 7:
        start_ym = title_month[:7]
    elif title_year:
        start_ym = f"{title_year}-01"

    if start_ym:
        months = _months_since(start_ym)
        years  = months // 12
        rem    = months % 12
        # 所需年限规则
        if apply_level == "工程师":
            required = 4
        elif apply_level == "高级工程师":
            required = 7 if edu == "大专" else 5
        elif apply_level == "正高级工程师":
            required = 5
        else:
            required = 5
        passed = months >= required * 12
        detail = (
            f"现职称：{title_level}，取得时间：{start_ym}，"
            f"从次月起已满 {years}年{rem}个月，"
            f"申报{apply_level}需满{required}年"
        )
        if not passed:
            need = required * 12 - months
            detail += f"，还差{need}个月"
        items.append(CheckItem("资历年限", passed, detail, "must"))
    else:
        items.append(CheckItem(
            "资历年限", False,
            "未填写现职称取得年月，无法计算资历",
            "must"
        ))

    # ── 3. 社保缴纳 ───────────────────────────────────────────────
    total_ins = sum(int(r.get("insure_months") or 0) for r in insurances)
    ins_ok = total_ins >= 36
    items.append(CheckItem(
        "社保缴纳", ins_ok,
        f"系统记录社保共 {total_ins} 个月（申报要求≥36个月）",
        "must"
    ))

    # ── 4. 继续教育 ───────────────────────────────────────────────
    from datetime import date as _date
    cur_year = _date.today().year
    # 检查近3年每年学时
    edu_issues = []
    for yr in range(cur_year - 3, cur_year):
        hrs = sum(int(e.get("hours") or 0) for e in edu_trainings if str(e.get("year","")) == str(yr))
        if hrs < 90:
            edu_issues.append(f"{yr}年仅{hrs}学时")
    edu_ok = len(edu_issues) == 0
    detail = "近3年每年≥90学时" if edu_ok else ("不达标：" + "；".join(edu_issues))
    if not edu_trainings:
        detail = "尚无继续教育记录"
        edu_ok = False
    items.append(CheckItem("继续教育", edu_ok, detail, "must"))

    # ── 5. 代表性工程业绩 ─────────────────────────────────────────
    rep = [a for a in achievements if a.get("is_representative")]
    rep_ok = len(rep) >= 2
    items.append(CheckItem(
        "代表性工程", rep_ok,
        f"已录入代表性工程 {len(rep)} 项（一般要求≥2项）",
        "must"
    ))

    # ── 6. 工程业绩总数 ───────────────────────────────────────────
    items.append(CheckItem(
        "工程业绩数量", len(achievements) >= 3,
        f"已录入工程业绩 {len(achievements)} 项（建议≥3项）",
        "warn"
    ))

    # ── 7. 论文著作 ───────────────────────────────────────────────
    if apply_level in ("高级工程师", "正高级工程师"):
        paper_ok = len(papers) >= 1
        items.append(CheckItem(
            "论文著作", paper_ok,
            f"已录入论文/著作 {len(papers)} 篇（申报高级职称需至少1篇）",
            "must"
        ))
    else:
        if papers:
            items.append(CheckItem("论文著作", True, f"已录入 {len(papers)} 篇论文（加分项）", "warn"))

    # ── 8. 获奖情况 ───────────────────────────────────────────────
    if awards:
        high = [w for w in awards if w.get("award_level") in ("国家级","省部级")]
        items.append(CheckItem(
            "获奖情况", True,
            f"共 {len(awards)} 项获奖，其中国家/省部级 {len(high)} 项",
            "warn"
        ))

    # ── 9. 基本信息完整性 ─────────────────────────────────────────
    missing = [f for f in ["name","id_card","birth_date","phone","work_unit","education","major"]
               if not (applicant.get(f) or "").strip()]
    items.append(CheckItem(
        "基本信息完整", len(missing) == 0,
        "信息完整" if not missing else f"以下字段未填：{'、'.join(missing)}",
        "must"
    ))

    return items


def summary(items: list[CheckItem]) -> dict:
    must_items = [i for i in items if i.level == "must"]
    passed_must = sum(1 for i in must_items if i.passed)
    all_passed  = all(i.passed for i in must_items)
    return {
        "all_passed":   all_passed,
        "must_total":   len(must_items),
        "must_passed":  passed_must,
        "warn_total":   sum(1 for i in items if i.level == "warn"),
    }
