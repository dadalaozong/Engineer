import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
        -- 申报人
        CREATE TABLE IF NOT EXISTS applicants (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            id_card         TEXT,
            gender          TEXT,
            birth_date      TEXT,
            phone           TEXT,
            email           TEXT,
            ethnicity       TEXT,
            education       TEXT,
            major           TEXT,
            school          TEXT,
            graduation_year TEXT,
            work_unit       TEXT,
            work_unit_type  TEXT,
            work_start_year TEXT,
            title_level     TEXT,
            title_year      TEXT,
            notes           TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 申报批次
        CREATE TABLE IF NOT EXISTS batches (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            year            TEXT,
            industry        TEXT,
            committee       TEXT,
            level           TEXT,
            deadline        TEXT,
            submit_deadline TEXT,
            status          TEXT DEFAULT '进行中',
            note            TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 申报项目
        CREATE TABLE IF NOT EXISTS projects (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id    INTEGER REFERENCES applicants(id) ON DELETE CASCADE,
            batch_id        INTEGER REFERENCES batches(id)    ON DELETE SET NULL,
            industry        TEXT,
            committee       TEXT,
            apply_level     TEXT,
            specialty       TEXT,
            project_name    TEXT,
            project_type    TEXT,
            scale           TEXT,
            role            TEXT,
            folder_path     TEXT,
            status          TEXT DEFAULT '准备中',
            check_result    TEXT,
            submit_time     TEXT,
            review_result   TEXT,
            review_date     TEXT,
            review_comment  TEXT,
            notes           TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 工程业绩（代表性工程）
        CREATE TABLE IF NOT EXISTS achievements (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id    INTEGER REFERENCES applicants(id) ON DELETE CASCADE,
            project_name    TEXT NOT NULL,
            project_type    TEXT,
            scale           TEXT,
            role            TEXT,
            start_date      TEXT,
            end_date        TEXT,
            location        TEXT,
            owner           TEXT,
            contractor      TEXT,
            investment      REAL,
            area            REAL,
            description     TEXT,
            is_representative INTEGER DEFAULT 0,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 获奖情况
        CREATE TABLE IF NOT EXISTS awards (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id    INTEGER REFERENCES applicants(id) ON DELETE CASCADE,
            award_name      TEXT NOT NULL,
            award_level     TEXT,
            award_year      TEXT,
            award_org       TEXT,
            rank            TEXT,
            certificate_no  TEXT,
            notes           TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 论文/著作
        CREATE TABLE IF NOT EXISTS papers (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id    INTEGER REFERENCES applicants(id) ON DELETE CASCADE,
            title           TEXT NOT NULL,
            paper_type      TEXT DEFAULT '论文',
            journal         TEXT,
            pub_date        TEXT,
            author_rank     TEXT,
            cn_issn         TEXT,
            notes           TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 服务费用
        CREATE TABLE IF NOT EXISTS fees (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
            total           REAL DEFAULT 0,
            deposit         REAL DEFAULT 0,
            paid            REAL DEFAULT 0,
            paid_date       TEXT,
            note            TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 沟通记录
        CREATE TABLE IF NOT EXISTS contact_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id    INTEGER REFERENCES applicants(id) ON DELETE CASCADE,
            contact_date    TEXT,
            contact_type    TEXT DEFAULT '电话',
            content         TEXT,
            follow_up       TEXT,
            operator        TEXT DEFAULT '管理员',
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 工作经历
        CREATE TABLE IF NOT EXISTS work_experiences (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id    INTEGER REFERENCES applicants(id) ON DELETE CASCADE,
            start_date      TEXT,
            end_date        TEXT,
            work_unit       TEXT,
            position        TEXT,
            witness         TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 社保记录
        CREATE TABLE IF NOT EXISTS social_insurance (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id    INTEGER REFERENCES applicants(id) ON DELETE CASCADE,
            insure_location TEXT,
            insure_unit     TEXT,
            insure_start    TEXT,
            insure_end      TEXT,
            insure_months   INTEGER,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 继续教育
        CREATE TABLE IF NOT EXISTS edu_trainings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id    INTEGER REFERENCES applicants(id) ON DELETE CASCADE,
            year            INTEGER,
            hours           INTEGER,
            institution     TEXT,
            course_name     TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 执业资格证书
        CREATE TABLE IF NOT EXISTS pro_certificates (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id    INTEGER REFERENCES applicants(id) ON DELETE CASCADE,
            cert_type       TEXT,
            cert_no         TEXT,
            reg_no          TEXT,
            specialty       TEXT,
            valid_until     TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 学术团体及社会兼职
        CREATE TABLE IF NOT EXISTS academic_roles (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            applicant_id    INTEGER REFERENCES applicants(id) ON DELETE CASCADE,
            start_date      TEXT,
            end_date        TEXT,
            org_name        TEXT,
            position        TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # 对已存在的旧表做列迁移（ALTER TABLE ADD COLUMN IF NOT EXISTS 不支持，用 try/except）
    _migrate(conn)
    conn.commit()
    conn.close()

def _migrate(conn):
    """Add missing columns to existing tables without losing data."""
    migrations = [
        ("applicants", "gender",          "TEXT"),
        ("applicants", "birth_date",       "TEXT"),
        ("applicants", "ethnicity",        "TEXT"),
        ("applicants", "school",           "TEXT"),
        ("applicants", "graduation_year",  "TEXT"),
        ("applicants", "work_unit_type",   "TEXT"),
        ("applicants", "work_start_year",  "TEXT"),
        ("batches",    "submit_deadline",  "TEXT"),
        ("batches",    "status",           "TEXT DEFAULT '进行中'"),
        ("projects",   "apply_level",      "TEXT"),
        ("projects",   "specialty",        "TEXT"),
        ("projects",   "folder_path",      "TEXT"),
        ("projects",   "check_result",     "TEXT"),
        ("projects",   "submit_time",      "TEXT"),
        ("projects",     "review_result",   "TEXT"),
        ("projects",     "review_date",     "TEXT"),
        ("projects",     "review_comment",  "TEXT"),
        ("projects",     "progress_stage",  "INTEGER DEFAULT 0"),
        ("contact_logs", "follow_up_date",  "TEXT"),
        ("applicants",   "title_month",     "TEXT"),
        ("applicants",   "politics",        "TEXT"),
        ("applicants",   "address",         "TEXT"),
        ("applicants",   "degree",          "TEXT"),
        ("applicants",   "grad_month",      "TEXT"),
        ("applicants",   "study_mode",      "TEXT"),
        ("applicants",   "work_unit_addr",  "TEXT"),
        ("applicants",   "work_unit_phone", "TEXT"),
        ("applicants",   "current_position","TEXT"),
        ("applicants",   "current_specialty","TEXT"),
        ("applicants",   "title_specialty", "TEXT"),
        ("applicants",   "title_cert_no",   "TEXT"),
        ("applicants",   "title_issuer",    "TEXT"),
        ("applicants",   "photo_path",          "TEXT"),
        ("applicants",   "folder_path",         "TEXT"),
        # Tab3-2·破格/直接申报
        ("applicants",   "apply_exception",       "TEXT DEFAULT '否'"),
        # Tab4·职称外语和职称计算机
        ("applicants",   "lang_comp_require",     "TEXT DEFAULT '不作要求'"),
        ("applicants",   "lang_exam_result",      "TEXT DEFAULT '不作要求'"),
        ("applicants",   "comp_exam_result",      "TEXT DEFAULT '不作要求'"),
        ("applicants",   "lang_comp_check",       "TEXT DEFAULT '不作要求'"),
        ("applicants",   "lang_comp_other_prov",  "TEXT DEFAULT '不作要求'"),
        # Tab3-1·职称证书新增字段
        ("applicants",   "title_manage_no",     "TEXT"),
        ("applicants",   "title_scope",         "TEXT"),
        ("applicants",   "title_expire",        "TEXT"),
        # Tab2·学历情况新增字段
        ("applicants",   "edu_cert_no",         "TEXT"),
        ("applicants",   "degree_cert_no",       "TEXT"),
        ("applicants",   "degree_school",        "TEXT"),
        # 基本信息 Tab 新增字段（对应广西职称网实际字段）
        ("applicants",   "former_name",         "TEXT"),
        ("applicants",   "native_place",        "TEXT"),
        ("applicants",   "work_start_date",     "TEXT"),
        ("applicants",   "identity_type",       "TEXT"),
        ("applicants",   "is_first_apply",      "TEXT"),
        ("applicants",   "apply_count",         "INTEGER DEFAULT 0"),
        ("applicants",   "last_apply_date",     "TEXT"),
        ("applicants",   "rural_revitalization","TEXT"),
        ("applicants",   "is_skilled_talent",   "TEXT"),
        ("applicants",   "skill_work_years",    "TEXT"),
        ("applicants",   "unit_level",          "TEXT"),
        ("applicants",   "admin_position",      "TEXT"),
        ("applicants",   "admin_position_date", "TEXT"),
        ("applicants",   "admin_position_note", "TEXT"),
        ("applicants",   "archive_org",         "TEXT"),
        # 申报项目新增字段
        ("projects",     "title_series",        "TEXT"),
        ("projects",     "apply_title",         "TEXT"),
        ("projects",     "discipline",          "TEXT"),
        ("projects",     "apply_method",        "TEXT"),
        ("projects",     "batch_year",          "TEXT"),
        # Tab6-2·社保记录新增字段
        ("social_insurance", "data_source", "TEXT DEFAULT '数据获取'"),
        # Tab5·继续教育 edu_trainings表新增字段（对应网站实际列）
        ("edu_trainings", "mandatory_public_hours",  "REAL DEFAULT 0"),
        ("edu_trainings", "elective_public_hours",   "REAL DEFAULT 0"),
        ("edu_trainings", "industry_shared_credits", "REAL DEFAULT 0"),
        ("edu_trainings", "industry_shared_hours",   "REAL DEFAULT 0"),
        ("edu_trainings", "professional_hours",      "REAL DEFAULT 0"),
        ("edu_trainings", "total_hours",             "REAL DEFAULT 0"),
        ("edu_trainings", "data_source",             "TEXT DEFAULT '数据获取'"),
        ("edu_trainings", "train_start",             "TEXT"),
        ("edu_trainings", "train_end",               "TEXT"),
        ("edu_trainings", "issuer",                  "TEXT"),
        # Tab7-1·专业技术工作经历新增字段
        ("achievements", "criteria_item", "TEXT"),
        ("achievements", "ach_work_unit", "TEXT"),
        # Tab8-1·业绩成果新增字段
        ("achievements", "rank_in_project", "TEXT"),
        # Tab9·学术成果新增字段
        ("papers", "criteria_item", "TEXT"),
        ("papers", "is_representative_paper", "INTEGER DEFAULT 0"),
        ("papers", "is_masterpiece", "TEXT DEFAULT '否'"),
    ]
    for table, col, col_type in migrations:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
        except Exception:
            pass  # column already exists
