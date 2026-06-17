"""Scheme A — 专业深色侧边栏 全局 QSS"""

SIDEBAR_BG    = "#1e293b"
SIDEBAR_HOVER = "#334155"
ACCENT        = "#2563eb"
ACCENT_HOVER  = "#1d4ed8"
TEXT_PRIMARY  = "#f1f5f9"
TEXT_MUTED    = "#64748b"
CONTENT_BG    = "#f8fafc"
TOPBAR_BG     = "#ffffff"
CARD_BG       = "#ffffff"
BORDER        = "#e2e8f0"
SUCCESS       = "#16a34a"
WARNING       = "#d97706"
DANGER        = "#dc2626"

QSS = f"""
/* ── Global ── */
QWidget {{
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}

/* ── Sidebar ── */
#sidebar {{
    background-color: {SIDEBAR_BG};
    min-width: 220px;
    max-width: 220px;
}}
#sidebar QLabel#logo {{
    font-size: 15px;
    font-weight: bold;
    color: {TEXT_PRIMARY};
    padding: 18px 16px 14px;
    border-bottom: 1px solid #334155;
}}
#sidebar QPushButton {{
    text-align: left;
    padding: 9px 16px 9px 36px;
    border: none;
    border-radius: 6px;
    color: #94a3b8;
    background: transparent;
    margin: 1px 8px;
}}
#sidebar QPushButton:hover {{
    background-color: {SIDEBAR_HOVER};
    color: {TEXT_PRIMARY};
}}
#sidebar QPushButton[active="true"] {{
    background-color: rgba(37,99,235,0.25);
    color: #60a5fa;
    border-left: 3px solid {ACCENT};
    padding-left: 33px;
    font-weight: bold;
}}
#navGroupLabel {{
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.08em;
    color: {TEXT_MUTED};
    padding: 14px 16px 4px;
}}

/* ── Topbar ── */
#topbar {{
    background-color: {TOPBAR_BG};
    border-bottom: 1px solid {BORDER};
    min-height: 54px;
    max-height: 54px;
}}
#topbarTitle {{
    font-size: 16px;
    font-weight: bold;
    color: #1e293b;
}}

/* ── Content area ── */
#contentArea {{
    background-color: {CONTENT_BG};
}}

/* ── Stat card ── */
#statCard {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 16px;
}}
#statCard QLabel#statNum {{
    font-size: 26px;
    font-weight: bold;
    color: {ACCENT};
}}
#statCard QLabel#statLabel {{
    font-size: 12px;
    color: {TEXT_MUTED};
}}
#statCard QLabel#statSub {{
    font-size: 11px;
    color: {TEXT_MUTED};
}}

/* ── Table ── */
QTableWidget {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: #f1f5f9;
    outline: none;
}}
QTableWidget::item {{
    padding: 8px 12px;
    color: #334155;
    border-bottom: 1px solid #f1f5f9;
}}
QTableWidget::item:selected {{
    background-color: #dbeafe;
    color: #1e40af;
}}
QHeaderView::section {{
    background-color: #f8fafc;
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid {BORDER};
}}

/* ── Buttons ── */
QPushButton#btnPrimary {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
}}
QPushButton#btnPrimary:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton#btnOutline {{
    background-color: transparent;
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 16px;
}}
QPushButton#btnOutline:hover {{
    border-color: #94a3b8;
    color: #334155;
}}
QPushButton#btnDanger {{
    background-color: transparent;
    color: {DANGER};
    border: 1px solid #fecaca;
    border-radius: 6px;
    padding: 7px 16px;
}}
QPushButton#btnDanger:hover {{
    background-color: #fee2e2;
}}

/* ── Inputs ── */
QLineEdit, QComboBox, QTextEdit, QSpinBox, QDateEdit {{
    background-color: white;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 10px;
    color: #334155;
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
    border-color: {ACCENT};
    outline: none;
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

/* ── Dialog ── */
QDialog {{
    background-color: white;
}}

/* ── Scrollbar ── */
QScrollBar:vertical {{
    width: 6px;
    background: transparent;
}}
QScrollBar::handle:vertical {{
    background: #cbd5e1;
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
