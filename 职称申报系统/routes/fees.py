from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.models import list_projects, get_fee, upsert_fee

bp = Blueprint("fees", __name__, url_prefix="/fees")

@bp.route("/")
def report_page():
    projects = list_projects()
    fee_data = []
    total_sum = paid_sum = 0
    for p in projects:
        fee = get_fee(p["id"]) or {}
        total = fee.get("total", 0) or 0
        paid  = fee.get("paid",  0) or 0
        total_sum += total
        paid_sum  += paid
        status = "已结清" if total and paid >= total else ("部分" if paid else ("未付" if total else "未设"))
        fee_data.append({**p, "fee": fee, "status": status})
    return render_template("fees/report.html", fee_data=fee_data,
                           total_sum=total_sum, paid_sum=paid_sum,
                           pending_sum=total_sum - paid_sum)

@bp.route("/upsert", methods=["POST"])
def upsert():
    d = request.get_json()
    upsert_fee(
        project_id=d["project_id"],
        total=float(d.get("total") or 0),
        deposit=float(d.get("deposit") or 0),
        paid=float(d.get("paid") or 0),
        paid_date=d.get("paid_date", ""),
        note=d.get("note", ""),
    )
    return jsonify({"ok": True})
