"""Simple DAO helpers — each function returns dicts (sqlite3.Row)."""
import sqlite3
from database.db import get_conn


# ── Batches ──────────────────────────────────────────────
def list_batches() -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM batches ORDER BY year DESC, deadline ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def insert_batch(year, industry, committee, level, deadline="", note="") -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO batches(year,industry,committee,level,deadline,note) VALUES(?,?,?,?,?,?)",
        (year, industry, committee, level, deadline, note)
    )
    conn.commit(); conn.close()
    return cur.lastrowid


def update_batch(bid, **kwargs) -> None:
    fields = ", ".join(f"{k}=?" for k in kwargs)
    conn = get_conn()
    conn.execute(f"UPDATE batches SET {fields} WHERE id=?", (*kwargs.values(), bid))
    conn.commit(); conn.close()


def delete_batch(bid) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM batches WHERE id=?", (bid,))
    conn.commit(); conn.close()


# ── Applicants ───────────────────────────────────────────
def list_applicants(search="") -> list:
    conn = get_conn()
    if search:
        rows = conn.execute(
            "SELECT * FROM applicants WHERE name LIKE ? OR id_card LIKE ? OR phone LIKE ? ORDER BY created_at DESC",
            (f"%{search}%", f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM applicants ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_applicant(aid) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM applicants WHERE id=?", (aid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def insert_applicant(**kwargs) -> int:
    cols = ", ".join(kwargs.keys())
    placeholders = ", ".join("?" * len(kwargs))
    conn = get_conn()
    cur = conn.execute(f"INSERT INTO applicants({cols}) VALUES({placeholders})", list(kwargs.values()))
    conn.commit(); conn.close()
    return cur.lastrowid


def update_applicant(aid, **kwargs) -> None:
    fields = ", ".join(f"{k}=?" for k in kwargs)
    conn = get_conn()
    conn.execute(f"UPDATE applicants SET {fields} WHERE id=?", (*kwargs.values(), aid))
    conn.commit(); conn.close()


def delete_applicant(aid) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM applicants WHERE id=?", (aid,))
    conn.commit(); conn.close()


# ── Projects ─────────────────────────────────────────────
def list_projects(applicant_id=None, batch_id=None) -> list:
    conn = get_conn()
    sql = """
        SELECT p.*, a.name as applicant_name,
               b.year as batch_year, b.deadline as batch_deadline
        FROM projects p
        LEFT JOIN applicants a ON a.id = p.applicant_id
        LEFT JOIN batches b ON b.id = p.batch_id
    """
    params = []
    wheres = []
    if applicant_id:
        wheres.append("p.applicant_id=?"); params.append(applicant_id)
    if batch_id:
        wheres.append("p.batch_id=?"); params.append(batch_id)
    if wheres:
        sql += " WHERE " + " AND ".join(wheres)
    sql += " ORDER BY p.created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project(pid) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def insert_project(**kwargs) -> int:
    cols = ", ".join(kwargs.keys())
    placeholders = ", ".join("?" * len(kwargs))
    conn = get_conn()
    cur = conn.execute(f"INSERT INTO projects({cols}) VALUES({placeholders})", list(kwargs.values()))
    conn.commit(); conn.close()
    return cur.lastrowid


def update_project(pid, **kwargs) -> None:
    fields = ", ".join(f"{k}=?" for k in kwargs)
    conn = get_conn()
    conn.execute(f"UPDATE projects SET {fields} WHERE id=?", (*kwargs.values(), pid))
    conn.commit(); conn.close()


def delete_project(pid) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit(); conn.close()


# ── Fees ─────────────────────────────────────────────────
def get_fee(project_id) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM fees WHERE project_id=?", (project_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_fee(project_id, total=0, deposit=0, paid=0, paid_date="", note="") -> None:
    conn = get_conn()
    existing = conn.execute("SELECT id FROM fees WHERE project_id=?", (project_id,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE fees SET total=?,deposit=?,paid=?,paid_date=?,note=? WHERE project_id=?",
            (total, deposit, paid, paid_date, note, project_id)
        )
    else:
        conn.execute(
            "INSERT INTO fees(project_id,total,deposit,paid,paid_date,note) VALUES(?,?,?,?,?,?)",
            (project_id, total, deposit, paid, paid_date, note)
        )
    conn.commit(); conn.close()


# ── Dashboard stats ───────────────────────────────────────
def dashboard_stats() -> dict:
    conn = get_conn()
    total_applicants = conn.execute("SELECT COUNT(*) FROM applicants").fetchone()[0]
    total_projects   = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    total_fees       = conn.execute("SELECT COALESCE(SUM(paid),0) FROM fees").fetchone()[0]
    pending_fees     = conn.execute(
        "SELECT COALESCE(SUM(total-paid),0) FROM fees WHERE total>paid"
    ).fetchone()[0]
    conn.close()
    return {
        "total_applicants": total_applicants,
        "total_projects": total_projects,
        "total_fees": total_fees,
        "pending_fees": pending_fees,
    }
