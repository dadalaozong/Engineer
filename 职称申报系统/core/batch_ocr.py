"""批量OCR扫描 — 遍历申报人资料目录，按证件类型识别并汇总结果"""
from __future__ import annotations
from core.ocr_reader import (
    recognize_id_card, recognize_degree_cert,
    recognize_title_cert, recognize_pro_cert,
    recognize_social_insurance,
    recognize_edu_training, recognize_achievement,
    recognize_award, recognize_paper, recognize_annual_review,
)


def batch_scan(files: list[dict], secret_id: str, secret_key: str) -> dict:
    """
    files: core.folder_manager.scan_folder() 返回的文件列表
    返回:
      applicant_fields:    dict        合并后的申报人字段
      pro_certs:           list[dict]  执业资格证记录
      insurance_segments:  list[dict]  社保时段
      edu_trainings:       list[dict]  继续教育记录
      achievements:        list[dict]  工程业绩记录
      awards:              list[dict]  获奖记录
      papers:              list[dict]  论文著作记录
      annual_reviews:      list[dict]  年度考核记录
      raw_results:         list[dict]  每个文件的详细结果
    """
    applicant_fields: dict = {}
    pro_certs:        list = []
    insurance_segments: list = []
    edu_trainings:    list = []
    achievements:     list = []
    awards:           list = []
    papers:           list = []
    annual_reviews:   list = []
    raw_results:      list = []

    for fi in files:
        path      = fi["path"]
        cert_type = fi["cert_type"]
        entry = {"file": fi["rel_path"], "cert_type": cert_type, "fields": {}, "error": None}

        try:
            if cert_type == "id_card":
                fields = recognize_id_card(path, secret_id, secret_key, card_side="FRONT")
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
                if fields:
                    pro_certs.append(fields)

            elif cert_type == "social_insurance":
                result = recognize_social_insurance(path, secret_id, secret_key)
                entry["fields"] = {"raw": result.get("raw", "")[:200]}
                insurance_segments.extend(result.get("segments", []))

            elif cert_type == "edu_training":
                fields = recognize_edu_training(path, secret_id, secret_key)
                entry["fields"] = fields
                if fields:
                    edu_trainings.append(fields)

            elif cert_type == "achievement":
                fields = recognize_achievement(path, secret_id, secret_key)
                entry["fields"] = fields
                if fields:
                    achievements.append(fields)

            elif cert_type == "award":
                fields = recognize_award(path, secret_id, secret_key)
                entry["fields"] = fields
                if fields:
                    awards.append(fields)

            elif cert_type == "paper":
                fields = recognize_paper(path, secret_id, secret_key)
                entry["fields"] = fields
                if fields:
                    papers.append(fields)

            elif cert_type == "annual_review":
                fields = recognize_annual_review(path, secret_id, secret_key)
                entry["fields"] = fields
                if fields:
                    annual_reviews.append(fields)

        except Exception as e:
            entry["error"] = str(e)

        raw_results.append(entry)

    return {
        "applicant_fields":   applicant_fields,
        "pro_certs":          pro_certs,
        "insurance_segments": insurance_segments,
        "edu_trainings":      edu_trainings,
        "achievements":       achievements,
        "awards":             awards,
        "papers":             papers,
        "annual_reviews":     annual_reviews,
        "raw_results":        raw_results,
    }
