import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            id_card TEXT,
            phone TEXT,
            email TEXT,
            education TEXT,
            major TEXT,
            work_unit TEXT,
            title_level TEXT,
            title_year TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year TEXT,
            industry TEXT,
            committee TEXT,
            level TEXT,
            deadline TEXT,
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id INTEGER REFERENCES applicants(id),
            batch_id INTEGER REFERENCES batches(id),
            industry TEXT,
            committee TEXT,
            level TEXT,
            project_name TEXT,
            project_type TEXT,
            scale TEXT,
            role TEXT,
            status TEXT DEFAULT '准备中',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES projects(id),
            total REAL DEFAULT 0,
            deposit REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            paid_date TEXT,
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
