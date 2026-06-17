from flask import Blueprint, render_template
from database.db import get_conn

bp = Blueprint("fees", __name__, url_prefix="/fees")

@bp.route("/")
def report_page():
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.*, a.name as applicant_name,
               f.total, f.deposit, f.paid, f.paid_date, f.note as fee_note
        FROM projects p
        LEFT JOIN applicants a ON a.id = p.applicant_id
        LEFT JOIN fees f ON f.project_id = p.id
        ORDER BY p.created_at DESC
    """).fetchall()
    conn.close()

    fees_data = [dict(r) for r in rows]
    total_amount = sum(float(r["total"] or 0) for r in fees_data)
    total_paid = sum(float(r["paid"] or 0) for r in fees_data)
    total_pending = total_amount - total_paid
    summary = {
        "total_amount": round(total_amount, 2),
        "total_paid": round(total_paid, 2),
        "total_pending": round(total_pending, 2),
    }
    return render_template("fees/report.html", fees_data=fees_data, summary=summary)
