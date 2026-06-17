from flask import Blueprint, render_template
from database.models import dashboard_stats, list_batches, list_applicants, list_projects
from datetime import date

bp = Blueprint("dashboard", __name__)

@bp.route("/")
def index():
    stats   = dashboard_stats()
    batches = list_batches()

    today = date.today()
    warnings = []
    for b in batches:
        if b.get("status") == "已结束":
            continue
        for field, label in [("deadline", "评审截止"), ("submit_deadline", "材料提交截止")]:
            d = b.get(field)
            if not d:
                continue
            try:
                dd = date.fromisoformat(d)
                days = (dd - today).days
                if days < 0:
                    warnings.append({"batch": b, "label": label, "days": days,
                                     "level": "danger", "text": f"已逾期 {-days} 天"})
                elif days <= 7:
                    warnings.append({"batch": b, "label": label, "days": days,
                                     "level": "danger", "text": f"还剩 {days} 天"})
                elif days <= 30:
                    warnings.append({"batch": b, "label": label, "days": days,
                                     "level": "warning", "text": f"还剩 {days} 天"})
            except ValueError:
                pass

    recent_applicants = list_applicants()[:5]
    recent_projects   = list_projects()[:5]

    return render_template("dashboard.html",
                           stats=stats,
                           batches=batches[:3],
                           warnings=warnings,
                           recent_applicants=recent_applicants,
                           recent_projects=recent_projects)
