"""批量OCR扫描 — 遍历申报人资料目录，按证件类型识别并汇总结果"""
from __future__ import annotations
from core.ocr_reader import (
    recognize_id_card, recognize_degree_cert,
    recognize_title_cert, recognize_pro_cert,
    recognize_social_insurance,
)


def batch_scan(files: list[dict], secret_id: str, secret_key: str) -> dict:
    """
    files: core.folder_manager.scan_folder() 返回的文件列表
    返回:
      applicant_fields: dict  — 合并后的申报人字段（可直接 update_applicant）
      pro_certs: list[dict]   — 执业资格证记录列表
      insurance_segments: list[dict] — 社保时段列表
      raw_results: list[dict] — 每个文件的详细结果
    """
    applicant_fields: dict = {}
    pro_certs: list = []
    insurance_segments: list = []
    raw_results: list = []

    for fi in files:
        path      = fi["path"]
        cert_type = fi["cert_type"]
        entry = {"file": fi["rel_path"], "cert_type": cert_type, "fields": {}, "error": None}

        try:
            if cert_type == "id_card":
                # 正面（含姓名身份证号），背面识别较少字段，都尝试正面
                fields = recognize_id_card(path, secret_id, secret_key, card_side="FRONT")
                # 如果识别到身份证号则为正面；否则尝试背面
                if not fields.get("id_card"):
                    fields = recognize_id_card(path, secret_id, secret_key, card_side="BACK")
                entry["fields"] = fields
                applicant_fields.update({k: v for k, v in fields.items() if v})

            elif cert_type == "degree":
                fields = recognize_degree_cert(path, secret_id, secret_key)
                entry["fields"] = fields
                applicant_fields.update({k: v for k, v in fields.items() if v})

            elif cert_type == "title":
                fields = recognize_title_cert(path, secret_id, secret_key)
                entry["fields"] = fields
                applicant_fields.update({k: v for k, v in fields.items() if v})

            elif cert_type == "pro_cert":
                fields = recognize_pro_cert(path, secret_id, secret_key)
                entry["fields"] = fields
                if fields.get("cert_type"):
                    pro_certs.append(fields)

            elif cert_type == "social_insurance":
                result = recognize_social_insurance(path, secret_id, secret_key)
                entry["fields"] = {"raw": result.get("raw", "")[:200]}
                insurance_segments.extend(result.get("segments", []))

        except Exception as e:
            entry["error"] = str(e)

        raw_results.append(entry)

    return {
        "applicant_fields":    applicant_fields,
        "pro_certs":           pro_certs,
        "insurance_segments":  insurance_segments,
        "raw_results":         raw_results,
    }
