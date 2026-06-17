"""工程规模判断引擎 — 支持5个专业，任一指标达标即判定为该规模。"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ScaleRule:
    """Single indicator threshold for a scale level."""
    indicator: str   # indicator name
    unit:      str   # display unit
    value:     float # threshold value


@dataclass
class ScaleLevel:
    name:  str              # 大型 / 中型 / 小型
    color: str              # hex color for UI
    rules: list[ScaleRule]  # ANY rule met → this level


@dataclass
class Specialty:
    name:        str
    levels:      list[ScaleLevel]  # ordered: 大型 first
    description: str = ""


# ── Rule definitions ─────────────────────────────────────────────

_SPECIALTIES: list[Specialty] = [

    Specialty(
        name="房屋建筑工程",
        levels=[
            ScaleLevel("大型", "#dc2626", [
                ScaleRule("建筑面积",     "万㎡", 10),
                ScaleRule("工程造价",     "万元", 2000),
                ScaleRule("建筑高度",     "m",    50),
                ScaleRule("地下层数",     "层",   3),
            ]),
            ScaleLevel("中型", "#d97706", [
                ScaleRule("建筑面积",     "万㎡", 3),
                ScaleRule("工程造价",     "万元", 500),
                ScaleRule("建筑高度",     "m",    24),
                ScaleRule("地下层数",     "层",   2),
            ]),
            ScaleLevel("小型", "#16a34a", [
                ScaleRule("建筑面积",     "万㎡", 0),
                ScaleRule("工程造价",     "万元", 0),
            ]),
        ],
        description="适用于住宅、办公、商业、工业等房屋建筑项目",
    ),

    Specialty(
        name="市政公用工程",
        levels=[
            ScaleLevel("大型", "#dc2626", [
                ScaleRule("道路长度",     "km",   5),
                ScaleRule("工程造价",     "万元", 3000),
                ScaleRule("管道直径",     "mm",   1000),
                ScaleRule("桥梁跨径",     "m",    100),
            ]),
            ScaleLevel("中型", "#d97706", [
                ScaleRule("道路长度",     "km",   1),
                ScaleRule("工程造价",     "万元", 500),
                ScaleRule("管道直径",     "mm",   400),
                ScaleRule("桥梁跨径",     "m",    30),
            ]),
            ScaleLevel("小型", "#16a34a", [
                ScaleRule("工程造价",     "万元", 0),
            ]),
        ],
        description="适用于道路、桥梁、给排水、燃气等市政工程项目",
    ),

    Specialty(
        name="装饰装修工程",
        levels=[
            ScaleLevel("大型", "#dc2626", [
                ScaleRule("装修面积",     "㎡",   20000),
                ScaleRule("工程造价",     "万元", 1000),
            ]),
            ScaleLevel("中型", "#d97706", [
                ScaleRule("装修面积",     "㎡",   5000),
                ScaleRule("工程造价",     "万元", 200),
            ]),
            ScaleLevel("小型", "#16a34a", [
                ScaleRule("装修面积",     "㎡",   0),
                ScaleRule("工程造价",     "万元", 0),
            ]),
        ],
        description="适用于建筑内外墙、幕墙、室内精装等装饰装修项目",
    ),

    Specialty(
        name="机电安装工程",
        levels=[
            ScaleLevel("大型", "#dc2626", [
                ScaleRule("工程造价",     "万元", 1500),
                ScaleRule("变压器容量",   "kVA",  10000),
                ScaleRule("冷机容量",     "冷吨", 2000),
            ]),
            ScaleLevel("中型", "#d97706", [
                ScaleRule("工程造价",     "万元", 300),
                ScaleRule("变压器容量",   "kVA",  2000),
                ScaleRule("冷机容量",     "冷吨", 500),
            ]),
            ScaleLevel("小型", "#16a34a", [
                ScaleRule("工程造价",     "万元", 0),
            ]),
        ],
        description="适用于电气、暖通、给排水、消防、弱电等机电安装项目",
    ),

    Specialty(
        name="公路工程",
        levels=[
            ScaleLevel("大型", "#dc2626", [
                ScaleRule("公路长度",     "km",   20),
                ScaleRule("工程造价",     "万元", 5000),
                ScaleRule("设计速度",     "km/h", 80),
            ]),
            ScaleLevel("中型", "#d97706", [
                ScaleRule("公路长度",     "km",   5),
                ScaleRule("工程造价",     "万元", 1000),
                ScaleRule("设计速度",     "km/h", 40),
            ]),
            ScaleLevel("小型", "#16a34a", [
                ScaleRule("公路长度",     "km",   0),
                ScaleRule("工程造价",     "万元", 0),
            ]),
        ],
        description="适用于高速公路、国省道、农村公路等公路项目",
    ),
]

SPECIALTY_NAMES = [s.name for s in _SPECIALTIES]
_SPECIALTY_MAP  = {s.name: s for s in _SPECIALTIES}


@dataclass
class JudgeResult:
    scale:      str          # 大型 / 中型 / 小型
    color:      str          # hex
    hit_rules:  list[str]    # which rules triggered
    detail:     str          # human-readable summary


def judge(specialty_name: str, indicators: dict[str, float]) -> JudgeResult:
    """
    Determine engineering scale for given specialty and indicator values.
    indicators: {indicator_name: value}
    Returns JudgeResult.
    """
    sp = _SPECIALTY_MAP.get(specialty_name)
    if not sp:
        return JudgeResult("未知专业", "#64748b", [], "请选择正确的专业类别")

    # check from largest to smallest; first match wins
    for level in sp.levels[:-1]:  # skip 小型 (catch-all)
        hit = []
        for rule in level.rules:
            val = indicators.get(rule.indicator, 0)
            if val > 0 and val >= rule.value:
                hit.append(
                    f"{rule.indicator} {val:g} {rule.unit} "
                    f"（≥{rule.value:g} {rule.unit}）"
                )
        if hit:
            detail = f"符合{level.name}工程标准：\n" + "\n".join(f"  · {h}" for h in hit)
            return JudgeResult(level.name, level.color, hit, detail)

    # 小型 catch-all
    last = sp.levels[-1]
    return JudgeResult(
        last.name, last.color, [],
        f"所填指标均未达到中型/大型标准，判定为{last.name}工程"
    )


def get_specialty(name: str) -> Specialty | None:
    return _SPECIALTY_MAP.get(name)
