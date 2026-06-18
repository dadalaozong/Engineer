from database.db import get_conn

# ── Applicants ────────────────────────────────────────────────────

_APPLICANT_COLS = (
    "name","id_card","gender","birth_date","phone","email","ethnicity",
    "education","major","school","graduation_year","grad_month","study_mode","degree",
    "work_unit","work_unit_type","work_start_year","work_unit_addr","work_unit_phone",
    "current_position","current_specialty",
    "title_level","title_year","title_month","title_specialty","title_cert_no","title_issuer",
    "politics","address","photo_path","folder_path","notes",
    # Tab3-2·破格/直接申报 + Tab4·职称外语计算机
    "apply_exception","lang_comp_require","lang_exam_result",
    "comp_exam_result","lang_comp_check","lang_comp_other_prov",
    # Tab3-1·职称证书
    "title_manage_no","title_scope","title_expire",
    # Tab2·学历情况
    "edu_cert_no","degree_cert_no","degree_school",
    # 广西职称网基本信息Tab字段
    "former_name","native_place","work_start_date","identity_type",
    "is_first_apply","apply_count","last_apply_date",
    "rural_revitalization","is_skilled_talent","skill_work_years",
    "unit_level","admin_position","admin_position_date","admin_position_note",
    "archive_org",
)

def list_applicants(q=""):
    conn = get_conn()
    if q:
        rows = conn.execute(
            "SELECT * FROM applicants WHERE name LIKE ? OR id_card LIKE ? OR work_unit LIKE ? ORDER BY id DESC",
            (f"%{q}%", f"%{q}%", f"%{q}%")
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM applicants ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_applicant(aid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM applicants WHERE id=?", (aid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def insert_applicant(**kw) -> int:
    cols = ", ".join(_APPLICANT_COLS)
    ph   = ", ".join("?" * len(_APPLICANT_COLS))
    vals = [kw.get(c, "") for c in _APPLICANT_COLS]
    conn = get_conn()
    cur  = conn.execute(f"INSERT INTO applicants ({cols}) VALUES ({ph})", vals)
    conn.commit(); conn.close()
    return cur.lastrowid

def update_applicant(aid, **kw):
    sets = ", ".join(f"{c}=?" for c in _APPLICANT_COLS)
    vals = [kw.get(c, "") for c in _APPLICANT_COLS] + [aid]
    conn = get_conn()
    conn.execute(f"UPDATE applicants SET {sets} WHERE id=?", vals)
    conn.commit(); conn.close()

def delete_applicant(aid):
    conn = get_conn()
    conn.execute("DELETE FROM applicants WHERE id=?", (aid,))
    conn.commit(); conn.close()


# ── Batches ───────────────────────────────────────────────────────

def list_batches():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM batches ORDER BY year DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_batch(bid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM batches WHERE id=?", (bid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def insert_batch(**kw) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO batches (year,industry,committee,level,deadline,submit_deadline,status,note) VALUES (?,?,?,?,?,?,?,?)",
        (kw.get("year"), kw.get("industry"), kw.get("committee"), kw.get("level"),
         kw.get("deadline"), kw.get("submit_deadline"), kw.get("status","进行中"), kw.get("note"))
    )
    conn.commit(); conn.close()
    return cur.lastrowid

def update_batch(bid, **kw):
    conn = get_conn()
    conn.execute(
        "UPDATE batches SET year=?,industry=?,committee=?,level=?,deadline=?,submit_deadline=?,status=?,note=? WHERE id=?",
        (kw.get("year"), kw.get("industry"), kw.get("committee"), kw.get("level"),
         kw.get("deadline"), kw.get("submit_deadline"), kw.get("status","进行中"),
         kw.get("note"), bid)
    )
    conn.commit(); conn.close()

def delete_batch(bid):
    conn = get_conn()
    conn.execute("DELETE FROM batches WHERE id=?", (bid,))
    conn.commit(); conn.close()


# ── Projects ──────────────────────────────────────────────────────

_PROJECT_COLS = (
    "applicant_id","batch_id","industry","committee","apply_level","specialty",
    "project_name","project_type","scale","role","folder_path",
    "status","check_result","submit_time","review_result","review_date","review_comment","notes"
)

def list_projects(applicant_id=None, batch_id=None):
    conn = get_conn()
    sql = """SELECT p.*, a.name as applicant_name,
                    b.year as batch_year, b.deadline as batch_deadline
             FROM projects p
             LEFT JOIN applicants a ON a.id=p.applicant_id
             LEFT JOIN batches    b ON b.id=p.batch_id"""
    wheres, params = [], []
    if applicant_id:
        wheres.append("p.applicant_id=?"); params.append(applicant_id)
    if batch_id:
        wheres.append("p.batch_id=?"); params.append(batch_id)
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    sql += " ORDER BY p.id DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_project(pid):
    conn = get_conn()
    row = conn.execute(
        "SELECT p.*, a.name as applicant_name FROM projects p LEFT JOIN applicants a ON a.id=p.applicant_id WHERE p.id=?",
        (pid,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def insert_project(**kw) -> int:
    cols = ", ".join(_PROJECT_COLS)
    ph   = ", ".join("?" * len(_PROJECT_COLS))
    def _v(c):
        v = kw.get(c, "")
        if c in ("applicant_id","batch_id"):
            return int(v) if v else None
        return v or ("准备中" if c == "status" else "")
    vals = [_v(c) for c in _PROJECT_COLS]
    conn = get_conn()
    cur  = conn.execute(f"INSERT INTO projects ({cols}) VALUES ({ph})", vals)
    conn.commit(); conn.close()
    return cur.lastrowid

def update_project(pid, **kw):
    def _v(c):
        v = kw.get(c, "")
        if c in ("applicant_id","batch_id"):
            return int(v) if v else None
        return v or ("准备中" if c == "status" else "")
    sets = ", ".join(f"{c}=?" for c in _PROJECT_COLS)
    vals = [_v(c) for c in _PROJECT_COLS] + [pid]
    conn = get_conn()
    conn.execute(f"UPDATE projects SET {sets} WHERE id=?", vals)
    conn.commit(); conn.close()

def delete_project(pid):
    conn = get_conn()
    conn.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit(); conn.close()


# ── Achievements ──────────────────────────────────────────────────

def list_achievements(applicant_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM achievements WHERE applicant_id=? ORDER BY is_representative DESC, id DESC",
        (applicant_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_achievement(aid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM achievements WHERE id=?", (aid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def insert_achievement(**kw) -> int:
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO achievements
           (applicant_id,project_name,project_type,scale,role,start_date,end_date,
            location,owner,contractor,investment,area,description,is_representative)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (kw.get("applicant_id"), kw.get("project_name"), kw.get("project_type"),
         kw.get("scale"), kw.get("role"), kw.get("start_date"), kw.get("end_date"),
         kw.get("location"), kw.get("owner"), kw.get("contractor"),
         kw.get("investment") or None, kw.get("area") or None,
         kw.get("description"), 1 if kw.get("is_representative") else 0)
    )
    conn.commit(); conn.close()
    return cur.lastrowid

def update_achievement(rid, **kw):
    conn = get_conn()
    conn.execute(
        """UPDATE achievements SET
           project_name=?,project_type=?,scale=?,role=?,start_date=?,end_date=?,
           location=?,owner=?,contractor=?,investment=?,area=?,description=?,is_representative=?
           WHERE id=?""",
        (kw.get("project_name"), kw.get("project_type"), kw.get("scale"),
         kw.get("role"), kw.get("start_date"), kw.get("end_date"),
         kw.get("location"), kw.get("owner"), kw.get("contractor"),
         kw.get("investment") or None, kw.get("area") or None,
         kw.get("description"), 1 if kw.get("is_representative") else 0, rid)
    )
    conn.commit(); conn.close()

def delete_achievement(rid):
    conn = get_conn()
    conn.execute("DELETE FROM achievements WHERE id=?", (rid,))
    conn.commit(); conn.close()


# ── Awards ────────────────────────────────────────────────────────

def list_awards(applicant_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM awards WHERE applicant_id=? ORDER BY award_year DESC, id DESC",
        (applicant_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_award(**kw) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO awards (applicant_id,award_name,award_level,award_year,award_org,rank,certificate_no,notes) VALUES (?,?,?,?,?,?,?,?)",
        (kw.get("applicant_id"), kw.get("award_name"), kw.get("award_level"),
         kw.get("award_year"), kw.get("award_org"), kw.get("rank"),
         kw.get("certificate_no"), kw.get("notes"))
    )
    conn.commit(); conn.close()
    return cur.lastrowid

def update_award(aid, **kw):
    conn = get_conn()
    conn.execute(
        "UPDATE awards SET award_name=?,award_level=?,award_year=?,award_org=?,rank=?,certificate_no=?,notes=? WHERE id=?",
        (kw.get("award_name"), kw.get("award_level"), kw.get("award_year"),
         kw.get("award_org"), kw.get("rank"), kw.get("certificate_no"),
         kw.get("notes"), aid)
    )
    conn.commit(); conn.close()

def delete_award(aid):
    conn = get_conn()
    conn.execute("DELETE FROM awards WHERE id=?", (aid,))
    conn.commit(); conn.close()


# ── Papers ────────────────────────────────────────────────────────

def list_papers(applicant_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM papers WHERE applicant_id=? ORDER BY pub_date DESC, id DESC",
        (applicant_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_paper(**kw) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO papers (applicant_id,title,paper_type,journal,pub_date,author_rank,cn_issn,notes) VALUES (?,?,?,?,?,?,?,?)",
        (kw.get("applicant_id"), kw.get("title"), kw.get("paper_type","论文"),
         kw.get("journal"), kw.get("pub_date"), kw.get("author_rank"),
         kw.get("cn_issn"), kw.get("notes"))
    )
    conn.commit(); conn.close()
    return cur.lastrowid

def update_paper(pid, **kw):
    conn = get_conn()
    conn.execute(
        "UPDATE papers SET title=?,paper_type=?,journal=?,pub_date=?,author_rank=?,cn_issn=?,notes=? WHERE id=?",
        (kw.get("title"), kw.get("paper_type","论文"), kw.get("journal"),
         kw.get("pub_date"), kw.get("author_rank"), kw.get("cn_issn"),
         kw.get("notes"), pid)
    )
    conn.commit(); conn.close()

def delete_paper(pid):
    conn = get_conn()
    conn.execute("DELETE FROM papers WHERE id=?", (pid,))
    conn.commit(); conn.close()


# ── Contact Logs ──────────────────────────────────────────────────

def list_contact_logs(applicant_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM contact_logs WHERE applicant_id=? ORDER BY contact_date DESC, id DESC",
        (applicant_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_contact_log(**kw) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO contact_logs (applicant_id,contact_date,contact_type,content,follow_up,follow_up_date,operator) VALUES (?,?,?,?,?,?,?)",
        (kw.get("applicant_id"), kw.get("contact_date"), kw.get("contact_type","电话"),
         kw.get("content"), kw.get("follow_up"), kw.get("follow_up_date") or None,
         kw.get("operator","管理员"))
    )
    conn.commit(); conn.close()
    return cur.lastrowid

def list_pending_followups():
    conn = get_conn()
    rows = conn.execute("""
        SELECT cl.*, a.name as applicant_name
        FROM contact_logs cl
        JOIN applicants a ON a.id = cl.applicant_id
        WHERE cl.follow_up_date IS NOT NULL AND cl.follow_up_date != ''
        ORDER BY cl.follow_up_date ASC
        LIMIT 20
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_project_stage(pid, stage: int):
    conn = get_conn()
    conn.execute("UPDATE projects SET progress_stage=? WHERE id=?", (int(stage), pid))
    conn.commit(); conn.close()

def delete_contact_log(cid):
    conn = get_conn()
    conn.execute("DELETE FROM contact_logs WHERE id=?", (cid,))
    conn.commit(); conn.close()


# ── Fees ──────────────────────────────────────────────────────────

def get_fee(project_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM fees WHERE project_id=?", (project_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}

def upsert_fee(project_id, **kw):
    conn = get_conn()
    existing = conn.execute("SELECT id FROM fees WHERE project_id=?", (project_id,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE fees SET total=?,deposit=?,paid=?,paid_date=?,note=? WHERE project_id=?",
            (kw.get("total",0), kw.get("deposit",0), kw.get("paid",0),
             kw.get("paid_date",""), kw.get("note",""), project_id)
        )
    else:
        conn.execute(
            "INSERT INTO fees (project_id,total,deposit,paid,paid_date,note) VALUES (?,?,?,?,?,?)",
            (project_id, kw.get("total",0), kw.get("deposit",0), kw.get("paid",0),
             kw.get("paid_date",""), kw.get("note",""))
        )
    conn.commit(); conn.close()


# ── Work Experiences ──────────────────────────────────────────────

def list_work_experiences(applicant_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM work_experiences WHERE applicant_id=? ORDER BY start_date ASC, id ASC",
        (applicant_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_work_experience(**kw) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO work_experiences (applicant_id,start_date,end_date,work_unit,position,witness) VALUES (?,?,?,?,?,?)",
        (kw.get("applicant_id"), kw.get("start_date"), kw.get("end_date"),
         kw.get("work_unit"), kw.get("position"), kw.get("witness"))
    )
    conn.commit(); conn.close()
    return cur.lastrowid

def update_work_experience(wid, **kw):
    conn = get_conn()
    conn.execute(
        "UPDATE work_experiences SET start_date=?,end_date=?,work_unit=?,position=?,witness=? WHERE id=?",
        (kw.get("start_date"), kw.get("end_date"), kw.get("work_unit"),
         kw.get("position"), kw.get("witness"), wid)
    )
    conn.commit(); conn.close()

def delete_work_experience(wid):
    conn = get_conn()
    conn.execute("DELETE FROM work_experiences WHERE id=?", (wid,))
    conn.commit(); conn.close()


# ── Social Insurance ───────────────────────────────────────────────

def list_social_insurance(applicant_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM social_insurance WHERE applicant_id=? ORDER BY insure_start ASC, id ASC",
        (applicant_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def total_insure_months(applicant_id):
    conn = get_conn()
    val = conn.execute(
        "SELECT COALESCE(SUM(insure_months),0) FROM social_insurance WHERE applicant_id=?",
        (applicant_id,)
    ).fetchone()[0]
    conn.close()
    return int(val)

def _calc_months(start: str, end: str) -> int:
    try:
        sy, sm = int(start[:4]), int(start[5:7])
        ey, em = int(end[:4]),   int(end[5:7])
        return max(0, (ey - sy) * 12 + (em - sm))
    except Exception:
        return 0

def insert_social_insurance(**kw) -> int:
    months = kw.get("insure_months") or _calc_months(
        kw.get("insure_start",""), kw.get("insure_end","")
    )
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO social_insurance (applicant_id,insure_location,insure_unit,insure_start,insure_end,insure_months) VALUES (?,?,?,?,?,?)",
        (kw.get("applicant_id"), kw.get("insure_location"), kw.get("insure_unit"),
         kw.get("insure_start"), kw.get("insure_end"), int(months) if months else None)
    )
    conn.commit(); conn.close()
    return cur.lastrowid

def update_social_insurance(sid, **kw):
    months = kw.get("insure_months") or _calc_months(
        kw.get("insure_start",""), kw.get("insure_end","")
    )
    conn = get_conn()
    conn.execute(
        "UPDATE social_insurance SET insure_location=?,insure_unit=?,insure_start=?,insure_end=?,insure_months=? WHERE id=?",
        (kw.get("insure_location"), kw.get("insure_unit"),
         kw.get("insure_start"), kw.get("insure_end"),
         int(months) if months else None, sid)
    )
    conn.commit(); conn.close()

def delete_social_insurance(sid):
    conn = get_conn()
    conn.execute("DELETE FROM social_insurance WHERE id=?", (sid,))
    conn.commit(); conn.close()


# ── Edu Trainings ─────────────────────────────────────────────────

def list_edu_trainings(applicant_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM edu_trainings WHERE applicant_id=? ORDER BY year DESC, id DESC",
        (applicant_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def edu_hours_by_year(applicant_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT year, SUM(hours) as total FROM edu_trainings WHERE applicant_id=? GROUP BY year ORDER BY year DESC",
        (applicant_id,)
    ).fetchall()
    conn.close()
    return {r["year"]: r["total"] for r in rows}

def insert_edu_training(**kw) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO edu_trainings (applicant_id,year,hours,institution,course_name) VALUES (?,?,?,?,?)",
        (kw.get("applicant_id"), kw.get("year") or None, kw.get("hours") or None,
         kw.get("institution"), kw.get("course_name"))
    )
    conn.commit(); conn.close()
    return cur.lastrowid

def update_edu_training(eid, **kw):
    conn = get_conn()
    conn.execute(
        "UPDATE edu_trainings SET year=?,hours=?,institution=?,course_name=? WHERE id=?",
        (kw.get("year") or None, kw.get("hours") or None,
         kw.get("institution"), kw.get("course_name"), eid)
    )
    conn.commit(); conn.close()

def delete_edu_training(eid):
    conn = get_conn()
    conn.execute("DELETE FROM edu_trainings WHERE id=?", (eid,))
    conn.commit(); conn.close()


# ── Pro Certificates ──────────────────────────────────────────────

def list_pro_certificates(applicant_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM pro_certificates WHERE applicant_id=? ORDER BY id DESC",
        (applicant_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_pro_certificate(**kw) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO pro_certificates (applicant_id,cert_type,cert_no,reg_no,specialty,valid_until) VALUES (?,?,?,?,?,?)",
        (kw.get("applicant_id"), kw.get("cert_type"), kw.get("cert_no"),
         kw.get("reg_no"), kw.get("specialty"), kw.get("valid_until"))
    )
    conn.commit(); conn.close()
    return cur.lastrowid

def update_pro_certificate(cid, **kw):
    conn = get_conn()
    conn.execute(
        "UPDATE pro_certificates SET cert_type=?,cert_no=?,reg_no=?,specialty=?,valid_until=? WHERE id=?",
        (kw.get("cert_type"), kw.get("cert_no"), kw.get("reg_no"),
         kw.get("specialty"), kw.get("valid_until"), cid)
    )
    conn.commit(); conn.close()

def delete_pro_certificate(cid):
    conn = get_conn()
    conn.execute("DELETE FROM pro_certificates WHERE id=?", (cid,))
    conn.commit(); conn.close()


# ── Dashboard Stats ───────────────────────────────────────────────

def dashboard_stats():
    conn = get_conn()
    total_applicants = conn.execute("SELECT COUNT(*) FROM applicants").fetchone()[0]
    total_projects   = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    total_fees       = conn.execute("SELECT COALESCE(SUM(paid),0) FROM fees").fetchone()[0]
    total_amount     = conn.execute("SELECT COALESCE(SUM(total),0) FROM fees").fetchone()[0]
    pending_fees     = float(total_amount) - float(total_fees)
    active_batches   = conn.execute("SELECT COUNT(*) FROM batches WHERE status='进行中'").fetchone()[0]
    conn.close()
    return {
        "total_applicants": total_applicants,
        "total_projects":   total_projects,
        "total_fees":       round(float(total_fees), 2),
        "pending_fees":     round(pending_fees, 2),
        "active_batches":   active_batches,
    }
