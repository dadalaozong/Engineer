from flask import Blueprint, render_template, request, jsonify
from database.db import get_conn
from database.models import upsert_fee

bp = Blueprint("fees", __name__, url_prefix="/fees")

@bp.route("/")
def report_page():
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.id, p.apply_level, p.status, a.name as applicant_name,
               f.total, f.deposit, f.paid, f.paid_date, f.note as fee_note
        FROM projects p
        LEFT JOIN applicants a ON a.id = p.applicant_id
        LEFT JOIN fees f ON f.project_id = p.id
        ORDER BY p.created_at DESC
    """).fetchall()
    conn.close()

    fee_data = []
    for r in rows:
        d = dict(r)
        fee_data.append({
            "id": d["id"],
            "applicant_name": d["applicant_name"],
            "apply_level": d["apply_level"],
            "status": d["status"],
            "fee": {
                "total":     d["total"] or 0,
                "deposit":   d["deposit"] or 0,
                "paid":      d["paid"] or 0,
                "paid_date": d["paid_date"] or "",
                "note":      d["fee_note"] or "",
            }
        })

    total_sum   = sum(float(r["fee"]["total"]) for r in fee_data)
    paid_sum    = sum(float(r["fee"]["paid"])  for r in fee_data)
    pending_sum = round(total_sum - paid_sum, 2)

    return render_template("fees/report.html",
                           fee_data=fee_data,
                           total_sum=round(total_sum, 2),
                           paid_sum=round(paid_sum, 2),
                           pending_sum=pending_sum)

@bp.route("/upsert", methods=["POST"])
def upsert():
    d = request.get_json(silent=True) or {}
    pid = d.get("project_id")
    if not pid:
        return jsonify({"success": False, "error": "project_id required"})
    upsert_fee(int(pid),
               total=float(d.get("total") or 0),
               deposit=float(d.get("deposit") or 0),
               paid=float(d.get("paid") or 0),
               paid_date=d.get("paid_date", ""),
               note=d.get("note", ""))
    return jsonify({"success": True})
