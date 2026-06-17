from database.db import get_conn

# ---- Applicants ----

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

def insert_applicant(**kw):
    conn = get_conn()
    conn.execute(
        "INSERT INTO applicants (name,id_card,phone,email,education,major,work_unit,title_level,title_year,notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (kw.get("name"), kw.get("id_card"), kw.get("phone"), kw.get("email"),
         kw.get("education"), kw.get("major"), kw.get("work_unit"),
         kw.get("title_level"), kw.get("title_year"), kw.get("notes"))
    )
    conn.commit()
    conn.close()

def update_applicant(aid, **kw):
    conn = get_conn()
    conn.execute(
        "UPDATE applicants SET name=?,id_card=?,phone=?,email=?,education=?,major=?,work_unit=?,title_level=?,title_year=?,notes=? WHERE id=?",
        (kw.get("name"), kw.get("id_card"), kw.get("phone"), kw.get("email"),
         kw.get("education"), kw.get("major"), kw.get("work_unit"),
         kw.get("title_level"), kw.get("title_year"), kw.get("notes"), aid)
    )
    conn.commit()
    conn.close()

def delete_applicant(aid):
    conn = get_conn()
    conn.execute("DELETE FROM applicants WHERE id=?", (aid,))
    conn.commit()
    conn.close()

# ---- Batches ----

def list_batches():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM batches ORDER BY year DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_batch(**kw):
    conn = get_conn()
    conn.execute(
        "INSERT INTO batches (year,industry,committee,level,deadline,note) VALUES (?,?,?,?,?,?)",
        (kw.get("year"), kw.get("industry"), kw.get("committee"), kw.get("level"), kw.get("deadline"), kw.get("note"))
    )
    conn.commit()
    conn.close()

def update_batch(bid, **kw):
    conn = get_conn()
    conn.execute(
        "UPDATE batches SET year=?,industry=?,committee=?,level=?,deadline=?,note=? WHERE id=?",
        (kw.get("year"), kw.get("industry"), kw.get("committee"), kw.get("level"), kw.get("deadline"), kw.get("note"), bid)
    )
    conn.commit()
    conn.close()

def delete_batch(bid):
    conn = get_conn()
    conn.execute("DELETE FROM batches WHERE id=?", (bid,))
    conn.commit()
    conn.close()

# ---- Projects ----

def list_projects(applicant_id=None):
    conn = get_conn()
    if applicant_id:
        rows = conn.execute(
            "SELECT p.*, a.name as applicant_name FROM projects p LEFT JOIN applicants a ON a.id=p.applicant_id WHERE p.applicant_id=? ORDER BY p.id DESC",
            (applicant_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT p.*, a.name as applicant_name FROM projects p LEFT JOIN applicants a ON a.id=p.applicant_id ORDER BY p.id DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_project(pid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def insert_project(**kw):
    conn = get_conn()
    conn.execute(
        "INSERT INTO projects (applicant_id,batch_id,industry,committee,level,project_name,project_type,scale,role,status,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (kw.get("applicant_id") or None, kw.get("batch_id") or None,
         kw.get("industry"), kw.get("committee"), kw.get("level"),
         kw.get("project_name"), kw.get("project_type"), kw.get("scale"),
         kw.get("role"), kw.get("status") or "准备中", kw.get("notes"))
    )
    conn.commit()
    conn.close()

def update_project(pid, **kw):
    conn = get_conn()
    conn.execute(
        "UPDATE projects SET applicant_id=?,batch_id=?,industry=?,committee=?,level=?,project_name=?,project_type=?,scale=?,role=?,status=?,notes=? WHERE id=?",
        (kw.get("applicant_id") or None, kw.get("batch_id") or None,
         kw.get("industry"), kw.get("committee"), kw.get("level"),
         kw.get("project_name"), kw.get("project_type"), kw.get("scale"),
         kw.get("role"), kw.get("status") or "准备中", kw.get("notes"), pid)
    )
    conn.commit()
    conn.close()

def delete_project(pid):
    conn = get_conn()
    conn.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()
    conn.close()

# ---- Dashboard Stats ----

def dashboard_stats():
    conn = get_conn()
    total_applicants = conn.execute("SELECT COUNT(*) FROM applicants").fetchone()[0]
    total_projects = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    total_fees = conn.execute("SELECT COALESCE(SUM(paid),0) FROM fees").fetchone()[0]
    total_amount = conn.execute("SELECT COALESCE(SUM(total),0) FROM fees").fetchone()[0]
    pending_fees = total_amount - total_fees
    conn.close()
    return {
        "total_applicants": total_applicants,
        "total_projects": total_projects,
        "total_fees": round(float(total_fees), 2),
        "pending_fees": round(float(pending_fees), 2),
    }
