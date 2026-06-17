import sqlite3
from contextlib import contextmanager
from config import DB_PATH

_DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS batches (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    year        INTEGER NOT NULL,
    industry    TEXT NOT NULL,
    committee   TEXT NOT NULL,
    level       TEXT NOT NULL,
    deadline    TEXT,
    note        TEXT,
    created_at  TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS applicants (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    id_card       TEXT,
    phone         TEXT,
    email         TEXT,
    education     TEXT,
    major         TEXT,
    current_level TEXT,
    work_unit     TEXT,
    note          TEXT,
    created_at    TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    applicant_id    INTEGER NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    batch_id        INTEGER REFERENCES batches(id) ON DELETE SET NULL,
    industry        TEXT NOT NULL,
    committee       TEXT NOT NULL,
    apply_level     TEXT NOT NULL,
    project_name    TEXT,
    folder_path     TEXT,
    scale           TEXT,
    review_result   TEXT,
    note            TEXT,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS achievements (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    role         TEXT,
    scale        TEXT,
    start_date   TEXT,
    end_date     TEXT,
    location     TEXT,
    description  TEXT,
    ai_desc      TEXT
);

CREATE TABLE IF NOT EXISTS awards (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    level        TEXT,
    rank         TEXT,
    award_date   TEXT,
    issuer       TEXT
);

CREATE TABLE IF NOT EXISTS papers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    journal      TEXT,
    publish_date TEXT,
    is_core      INTEGER DEFAULT 0,
    author_rank  INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS fees (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    total        REAL DEFAULT 0,
    deposit      REAL DEFAULT 0,
    paid         REAL DEFAULT 0,
    paid_date    TEXT,
    note         TEXT
);

CREATE TABLE IF NOT EXISTS contact_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    applicant_id INTEGER NOT NULL REFERENCES applicants(id) ON DELETE CASCADE,
    contact_time TEXT DEFAULT (datetime('now','localtime')),
    method       TEXT,
    content      TEXT
);
"""


def init_db() -> None:
    with _conn() as conn:
        conn.executescript(_DDL)


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_conn():
    """Return a persistent connection for use in DAO classes."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
