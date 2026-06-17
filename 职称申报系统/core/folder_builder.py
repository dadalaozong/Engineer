"""材料文件夹生成模块 — 按行业/级别创建标准目录结构。"""
from __future__ import annotations
from pathlib import Path
import os

# 每个 (industry, level) 对应的材料清单
# key: 显示名称, value: 文件夹名（英文/拼音，避免路径问题）
_MATERIAL_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "高级工程师": [
        ("01_个人申请表",       "01_申请表"),
        ("02_身份证复印件",     "02_身份证"),
        ("03_学历学位证书",     "03_学历证书"),
        ("04_现职称证书",       "04_现职称证书"),
        ("05_继续教育证明",     "05_继续教育"),
        ("06_工作总结",         "06_工作总结"),
        ("07_代表作说明书",     "07_代表作说明"),
        ("08_业绩证明材料",     "08_业绩材料"),
        ("09_工程项目合同",     "09_项目合同"),
        ("10_工程竣工验收报告", "10_竣工验收"),
        ("11_获奖证书",         "11_获奖证书"),
        ("12_论文著作",         "12_论文著作"),
        ("13_单位推荐表",       "13_单位推荐"),
        ("14_其他材料",         "14_其他"),
    ],
    "中级工程师": [
        ("01_个人申请表",       "01_申请表"),
        ("02_身份证复印件",     "02_身份证"),
        ("03_学历学位证书",     "03_学历证书"),
        ("04_现职称证书",       "04_现职称证书"),
        ("05_继续教育证明",     "05_继续教育"),
        ("06_工作总结",         "06_工作总结"),
        ("07_业绩证明材料",     "07_业绩材料"),
        ("08_工程项目合同",     "08_项目合同"),
        ("09_单位推荐表",       "09_单位推荐"),
        ("10_其他材料",         "10_其他"),
    ],
    "正高级工程师": [
        ("01_个人申请表",       "01_申请表"),
        ("02_身份证复印件",     "02_身份证"),
        ("03_学历学位证书",     "03_学历证书"),
        ("04_现职称证书",       "04_现职称证书"),
        ("05_继续教育证明",     "05_继续教育"),
        ("06_工作总结",         "06_工作总结"),
        ("07_代表作说明书",     "07_代表作说明"),
        ("08_重大业绩证明",     "08_重大业绩"),
        ("09_工程项目合同",     "09_项目合同"),
        ("10_竣工验收报告",     "10_竣工验收"),
        ("11_省级以上获奖证书", "11_获奖证书"),
        ("12_核心期刊论文",     "12_核心论文"),
        ("13_单位推荐表",       "13_单位推荐"),
        ("14_其他材料",         "14_其他"),
    ],
}

# 通用 fallback
_MATERIAL_TEMPLATES["中学一级"]  = _MATERIAL_TEMPLATES["中级工程师"]
_MATERIAL_TEMPLATES["中学高级"]  = _MATERIAL_TEMPLATES["高级工程师"]


def get_material_list(apply_level: str) -> list[tuple[str, str]]:
    """Return [(display_name, folder_name), ...] for the given level."""
    for key in _MATERIAL_TEMPLATES:
        if key in apply_level:
            return _MATERIAL_TEMPLATES[key]
    return _MATERIAL_TEMPLATES["高级工程师"]


def build_folder(base_dir: str, applicant_name: str, apply_level: str) -> tuple[str, list[str]]:
    """
    Create standard material folder structure.
    Returns (root_path, [created_subfolders]).
    """
    safe_name  = applicant_name.replace("/", "_").replace("\\", "_")
    safe_level = apply_level.replace("/", "_")
    root = Path(base_dir) / f"{safe_name}_{safe_level}_申报材料"
    root.mkdir(parents=True, exist_ok=True)

    created = []
    for _, folder_name in get_material_list(apply_level):
        sub = root / folder_name
        sub.mkdir(exist_ok=True)
        # put a placeholder readme
        readme = sub / "（此处放材料）.txt"
        if not readme.exists():
            readme.write_text("请将对应材料扫描件放入此文件夹。\n", encoding="utf-8")
        created.append(str(sub))

    return str(root), created


def scan_folder(root_path: str, apply_level: str) -> list[dict]:
    """
    Scan an existing folder and return material status list.
    Each item: {display_name, folder_name, path, file_count, has_files}
    """
    root = Path(root_path)
    result = []
    for display, folder_name in get_material_list(apply_level):
        sub = root / folder_name
        exists = sub.exists()
        if exists:
            files = [f for f in sub.iterdir()
                     if f.is_file() and not f.name.startswith("（")]
            file_count = len(files)
        else:
            file_count = 0
        result.append({
            "display_name": display,
            "folder_name":  folder_name,
            "path":         str(sub),
            "file_count":   file_count,
            "has_files":    file_count > 0,
            "exists":       exists,
        })
    return result
