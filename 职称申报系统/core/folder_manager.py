"""本地资料目录管理 — 创建/扫描申报人材料文件夹

目录结构严格对应广西职称网左侧菜单Tab顺序，
方便操作人员按网站页面逐Tab核对材料。
"""
from __future__ import annotations
import os, re
from pathlib import Path

# ── 子目录定义 ────────────────────────────────────────────────────
# (目录名, OCR类型, 对应网站Tab说明)
# OCR类型 None = 仅归档，不调用识别
SUBFOLDERS = [
    ("01_基本信息",   "id_card",          "网站Tab1：个人基本信息 + 照片"),
    ("02_学历学位",   "degree",           "网站Tab2：学历学位情况"),
    ("03_工作经历",   None,               "网站Tab3：工作经历（网页直接填表，无需扫描件）"),
    ("04_职称证书",   "title",            "网站Tab4：现职称情况"),
    ("05_执业资格",   "pro_cert",         "网站Tab5：执业资格证书"),
    ("06_社保记录",   "social_insurance", "网站Tab6：社会保险缴纳情况"),
    ("07_继续教育",   "edu_training",     "网站Tab7：继续教育情况"),
    ("08_工程业绩",   "achievement",      "网站Tab8：工程业绩（合同+竣工+业绩证明）"),
    ("09_获奖证书",   "award",            "网站Tab9：获奖情况"),
    ("10_论文著作",   "paper",            "网站Tab10：论文著作"),
    ("11_年度考核",   "annual_review",    "网站Tab11：年度考核表"),
    ("12_工作总结",   None,               "网站Tab12：工程技术工作总结（AI生成Word）"),
    ("13_其他材料",   None,               "其他补充材料"),
]

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".pdf"}

# 目录名→OCR类型 快查表
_DIR_TO_TYPE = {d: t for d, t, _ in SUBFOLDERS}


def make_folder_name(applicant: dict) -> str:
    name    = re.sub(r"[^一-龥A-Za-z0-9]", "", applicant.get("name", "未知"))
    id_card = applicant.get("id_card", "")
    suffix  = id_card[-4:] if len(id_card) >= 4 else "xxxx"
    return f"{name}_{suffix}"


def create_applicant_folder(applicant: dict, docs_folder: str) -> str:
    """创建申报人资料目录及子目录，返回目录绝对路径。"""
    root = Path(docs_folder) / make_folder_name(applicant)
    root.mkdir(parents=True, exist_ok=True)
    for dirname, _, desc in SUBFOLDERS:
        (root / dirname).mkdir(exist_ok=True)
    # 写说明文件，对应网站Tab
    readme = root / "材料放置说明.txt"
    lines = [
        f"申报人：{applicant.get('name', '')}",
        f"身份证：{applicant.get('id_card', '')}",
        "",
        "【材料放置说明】",
        "请将对应材料扫描件放入对应子目录，目录编号与广西职称网左侧菜单Tab一致：",
        "",
    ]
    for dirname, cert_type, desc in SUBFOLDERS:
        need = "（需扫描件）" if cert_type else "（网页直接填写，无需扫描件）"
        lines.append(f"  {dirname}/  {need}")
        lines.append(f"      {desc}")
        lines.append("")
    lines.append("支持格式：jpg / png / pdf")
    readme.write_text("\n".join(lines), encoding="utf-8")
    return str(root)


def scan_folder(folder_path: str) -> list[dict]:
    """
    扫描资料目录，返回所有图片文件列表。
    每项：{path, rel_path, subfolder, cert_type, filename}
    """
    root = Path(folder_path)
    if not root.exists():
        return []
    files = []
    for sub, cert_type, _ in SUBFOLDERS:
        sub_dir = root / sub
        if not sub_dir.exists():
            continue
        for f in sorted(sub_dir.iterdir()):
            if f.suffix.lower() in IMAGE_EXTS:
                files.append({
                    "path":      str(f),
                    "rel_path":  f"{sub}/{f.name}",
                    "subfolder": sub,
                    "cert_type": cert_type,
                    "filename":  f.name,
                })
    return files


def folder_exists(folder_path: str) -> bool:
    return bool(folder_path) and Path(folder_path).exists()


def tab_file_status(folder_path: str) -> dict[str, bool]:
    """返回各Tab目录是否有文件，{目录名: True/False}"""
    root = Path(folder_path) if folder_path else None
    result = {}
    for sub, cert_type, _ in SUBFOLDERS:
        if not root or not (root / sub).exists():
            result[sub] = False
            continue
        has_file = any(
            f.suffix.lower() in IMAGE_EXTS
            for f in (root / sub).iterdir()
            if f.is_file()
        )
        result[sub] = has_file
    return result

