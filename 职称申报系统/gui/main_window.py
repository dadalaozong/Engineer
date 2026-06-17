"""Main application window — Scheme A 深色侧边栏布局"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from gui.styles import QSS, SIDEBAR_BG, TEXT_MUTED
from gui.pages.dashboard import DashboardPage
from gui.pages.applicants import ApplicantsPage
from gui.pages.projects import ProjectsPage
from gui.pages.placeholder import PlaceholderPage

# Nav definition: (group_label, [(icon, label, page_key), ...])
NAV_STRUCTURE = [
    ("申报人管理", [
        ("👤", "申报人列表",   "applicants"),
        ("➕", "新增申报人",   "applicant_new"),
    ]),
    ("项目管理", [
        ("📁", "项目列表",     "projects"),
        ("📊", "工程规模判断", "scale"),
    ]),
    ("批次管理", [
        ("📅", "申报批次",     "batches"),
        ("⏰", "截止日期",     "deadlines"),
    ]),
    ("材料管理", [
        ("📄", "材料目录",     "docs"),
        ("🔍", "完整性检查",  "checker"),
    ]),
    ("AI 辅助", [
        ("✨", "AI 写作",      "ai_writer"),
        ("🖼", "图像处理",     "img_proc"),
    ]),
    ("系统", [
        ("⚙️",  "系统设置",    "settings"),
    ]),
]

PAGE_TITLES = {
    "dashboard":     "工作台",
    "applicants":    "申报人列表",
    "applicant_new": "新增申报人",
    "projects":      "项目管理",
    "scale":         "工程规模判断",
    "batches":       "申报批次管理",
    "deadlines":     "截止日期",
    "docs":          "材料目录",
    "checker":       "完整性检查",
    "ai_writer":     "AI 辅助写作",
    "img_proc":      "图像处理",
    "settings":      "系统设置",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("职称申报系统 v1.0")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(QSS)

        self._pages: dict[str, QWidget] = {}
        self._nav_btns: dict[str, QPushButton] = {}
        self._current_page = ""

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_main_area())

        self._switch_page("dashboard")

    # ── Sidebar ───────────────────────────────────────────────────
    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Logo
        logo = QLabel("📋  职称申报系统")
        logo.setObjectName("logo")
        logo.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:#f1f5f9;"
            f"padding:18px 16px 14px; border-bottom:1px solid #334155;"
        )
        lay.addWidget(logo)

        # Dashboard shortcut
        dash_btn = self._make_nav_btn("🏠", "工作台", "dashboard")
        lay.addWidget(dash_btn)

        # Nav groups
        for group_label, items in NAV_STRUCTURE:
            grp_lbl = QLabel(group_label.upper())
            grp_lbl.setObjectName("navGroupLabel")
            grp_lbl.setStyleSheet(
                f"font-size:10px; font-weight:bold; letter-spacing:0.08em;"
                f"color:{TEXT_MUTED}; padding:14px 16px 4px;"
            )
            lay.addWidget(grp_lbl)
            for ico, label, key in items:
                btn = self._make_nav_btn(ico, label, key)
                lay.addWidget(btn)

        lay.addStretch()

        # Version
        ver = QLabel("v1.0.0")
        ver.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px; padding:8px 16px;")
        lay.addWidget(ver)

        return sidebar

    def _make_nav_btn(self, ico: str, label: str, key: str) -> QPushButton:
        btn = QPushButton(f"  {ico}  {label}")
        btn.setObjectName("navBtn")
        btn.setCheckable(False)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { text-align:left; padding:9px 16px; border:none;"
            "border-radius:6px; color:#94a3b8; background:transparent; margin:1px 8px; }"
            "QPushButton:hover { background-color:#334155; color:#f1f5f9; }"
        )
        btn.clicked.connect(lambda _, k=key: self._switch_page(k))
        self._nav_btns[key] = btn
        return btn

    # ── Main area ─────────────────────────────────────────────────
    def _build_main_area(self) -> QWidget:
        w = QWidget()
        w.setObjectName("contentArea")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Topbar
        self._topbar = QWidget()
        self._topbar.setObjectName("topbar")
        self._topbar.setFixedHeight(54)
        tb_lay = QHBoxLayout(self._topbar)
        tb_lay.setContentsMargins(20, 0, 20, 0)

        self._topbar_title = QLabel("工作台")
        self._topbar_title.setObjectName("topbarTitle")
        f = self._topbar_title.font()
        f.setPointSize(14)
        f.setBold(True)
        self._topbar_title.setFont(f)
        self._topbar_title.setStyleSheet("color:#1e293b;")

        tb_lay.addWidget(self._topbar_title)
        tb_lay.addStretch()

        user_lbl = QLabel("管理员")
        user_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:13px;")
        tb_lay.addWidget(user_lbl)

        lay.addWidget(self._topbar)

        # Page stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background-color:#f8fafc;")
        lay.addWidget(self._stack)

        return w

    # ── Page switching ────────────────────────────────────────────
    def _get_or_create_page(self, key: str) -> QWidget:
        if key in self._pages:
            return self._pages[key]

        if key == "dashboard":
            page = DashboardPage()
        elif key == "applicants":
            page = ApplicantsPage()
            page.view_projects.connect(self._open_projects_for_applicant)
        elif key == "applicant_new":
            # re-use ApplicantsPage, just open the add dialog immediately
            page = ApplicantsPage()
            page.view_projects.connect(self._open_projects_for_applicant)
        elif key == "projects":
            page = ProjectsPage()
        else:
            page = PlaceholderPage(PAGE_TITLES.get(key, key))

        self._pages[key] = page
        self._stack.addWidget(page)
        return page

    def _open_projects_for_applicant(self, applicant_id: int, name: str):
        """Switch to projects page filtered by applicant."""
        page = self._get_or_create_page("projects")
        self._switch_page("projects")
        page.set_applicant_filter(applicant_id, name)

    def _switch_page(self, key: str):
        if self._current_page == key:
            return

        # Update nav button styles
        if self._current_page and self._current_page in self._nav_btns:
            btn = self._nav_btns[self._current_page]
            btn.setStyleSheet(
                "QPushButton { text-align:left; padding:9px 16px; border:none;"
                "border-radius:6px; color:#94a3b8; background:transparent; margin:1px 8px; }"
                "QPushButton:hover { background-color:#334155; color:#f1f5f9; }"
            )

        self._current_page = key

        if key in self._nav_btns:
            btn = self._nav_btns[key]
            btn.setStyleSheet(
                "QPushButton { text-align:left; padding:9px 16px 9px 13px; border:none;"
                "border-left:3px solid #2563eb; border-radius:6px;"
                "color:#60a5fa; background:rgba(37,99,235,0.18); margin:1px 8px;"
                "font-weight:bold; }"
            )

        title = PAGE_TITLES.get(key, key)
        self._topbar_title.setText(title)

        page = self._get_or_create_page(key)
        self._stack.setCurrentWidget(page)

        if hasattr(page, "refresh"):
            page.refresh()
