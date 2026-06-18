"""本地资料目录管理 — 创建/扫描申报人材料文件夹"""
from __future__ import annotations
import os, re
from pathlib import Path

# 子目录结构（顺序即清单顺序）
# key = 目录名, value = OCR类型（None=不识别，仅归档）
SUBFOLDERS = [
    ("01_身份证",       "id_card"),
    ("02_学历学位证",   "degree"),
    ("03_职称证书",     "title"),
    ("04_执业资格证",   "pro_cert"),
    ("05_社保记录",     "social_insurance"),
    ("06_工程业绩",     None),
    ("07_获奖证书",     None),
    ("08_论文著作",     None),
    ("09_其他",         None),
]

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".pdf"}

# 目录名→OCR类型 快查表
_DIR_TO_TYPE = {d: t for d, t in SUBFOLDERS}


def make_folder_name(applicant: dict) -> str:
    name    = re.sub(r"[^一-龥A-Za-z0-9]", "", applicant.get("name", "未知"))
    id_card = applicant.get("id_card", "")
    suffix  = id_card[-4:] if len(id_card) >= 4 else "xxxx"
    return f"{name}_{suffix}"


def create_applicant_folder(applicant: dict, docs_folder: str) -> str:
    """创建申报人资料目录及子目录，返回目录绝对路径。"""
    root = Path(docs_folder) / make_folder_name(applicant)
    root.mkdir(parents=True, exist_ok=True)
    for dirname, _ in SUBFOLDERS:
        (root / dirname).mkdir(exist_ok=True)
    # 写一个说明文件
    readme = root / "材料清单说明.txt"
    if not readme.exists():
        lines = ["请将对应材料扫描后放入以下子目录：\n"]
        for dirname, _ in SUBFOLDERS:
            lines.append(f"  {dirname}/")
        lines.append("\n支持格式：jpg / png / pdf 等图片格式")
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
    for sub, cert_type in SUBFOLDERS:
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
