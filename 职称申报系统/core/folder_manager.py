"""本地资料目录管理 — 创建/扫描申报人材料文件夹

目录结构严格对应广西职称网左侧菜单顺序（含二级Tab），
方便操作人员按网站页面逐Tab核对材料。
"""
from __future__ import annotations
import os, re
from pathlib import Path

# ── 子目录定义 ────────────────────────────────────────────────────
# (目录名, OCR类型, 对应网站菜单说明)
# OCR类型 None = 仅归档，不调用识别
# 07-1 和 08-1 都用 achievement 类型，batch_ocr 会合并结果
SUBFOLDERS = [
    ("01_基本信息",              "id_card",          "网站1：基本信息 + 照片"),
    ("02_学历情况",              "degree",           "网站2：学历情况（学历证+学位证）"),
    ("03-1_现任专业技术资格",    "title",            "网站3-1：现任专业技术资格（职称证书）"),
    ("03-2_破格直接申报",        None,               "网站3-2：破格/直接申报材料（如有）"),
    ("04_外语和计算机",          None,               "网站4：外语和计算机证书（如有）"),
    ("05_继续教育",              "edu_training",     "网站5：继续教育学习完成情况"),
    ("06-1_工作简历",            None,               "网站6-1：工作简历（网页直接填表，无需扫描件）"),
    ("06-2_社保记录",            "social_insurance", "网站6-2：个人社保缴纳记录"),
    ("07-1_专业技术工作经历",    "achievement",      "网站7-1：专业技术工作经历（业绩证明材料）"),
    ("07-2_学术团体社会兼职",    None,               "网站7-2：学术团体及社会兼职（如有）"),
    ("08-1_业绩成果",            "achievement",      "网站8-1：业绩成果（合同封面+竣工验收报告）"),
    ("08-2_获奖情况",            "award",            "网站8-2：获奖情况（获奖证书）"),
    ("09_学术成果",              "paper",            "网站9：学术成果（论文著作首页/收录证明）"),
    ("10_专业技术工作总结",      None,               "网站10：专业技术工作总结（AI生成Word后放入此处）"),
    ("11_其他材料",              None,               "网站11：其他补充材料"),
    ("附_执业资格证",            "pro_cert",         "执业资格证书（注册证，配合3-1填写）"),
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
    # 写说明文件
    readme = root / "材料放置说明.txt"
    lines = [
        f"申报人：{applicant.get('name', '')}",
        f"身份证：{applicant.get('id_card', '')}",
        "",
        "【材料放置说明】",
        "目录编号与广西职称网左侧菜单一致，按菜单顺序逐一核对：",
        "",
    ]
    for dirname, cert_type, desc in SUBFOLDERS:
        need = "★需扫描件" if cert_type else "  网页填表"
        lines.append(f"  {dirname}/")
        lines.append(f"      {need} — {desc}")
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
