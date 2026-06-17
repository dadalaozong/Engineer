"""自动填报页 — 启动浏览器、选择项目、执行填报、查看日志。"""
from __future__ import annotations
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QGroupBox, QFormLayout,
    QCheckBox, QFrame, QMessageBox, QSplitter, QProgressBar,
    QScrollArea, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor
from database.models import list_applicants, list_projects, get_applicant
from config import load_config
from core.crypto import decrypt
from gui.widgets import SectionTitle


class FillWorker(QThread):
    log_step = pyqtSignal(str, bool, str)   # step_name, success, message
    finished = pyqtSignal(str)              # summary text
    error    = pyqtSignal(str)

    def __init__(self, applicant: dict, project: dict, headless: bool):
        super().__init__()
        self.applicant = applicant
        self.project   = project
        self.headless  = headless
        self._browser  = None

    def run(self):
        try:
            from automation.browser import BrowserManager
            from automation.form_filler import FormFiller

            self._browser = BrowserManager()
            self._browser.start(headless=self.headless)

            filler = FormFiller(self._browser)
            report = filler.run(
                self.applicant,
                self.project,
                log_callback=lambda name, ok, msg: self.log_step.emit(name, ok, msg),
            )
            self.finished.emit(report.summary())
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if self._browser:
                # keep browser open for human review unless headless
                if self.headless:
                    self._browser.stop()

    def stop_browser(self):
        if self._browser:
            self._browser.stop()


class AutoFillPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects  = []
        self._worker: FillWorker | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)
        root.addWidget(SectionTitle("自动填报"))

        # ── 前置检查提示 ──────────────────────────────────────────
        self._check_banner = QLabel()
        self._check_banner.setWordWrap(True)
        self._check_banner.setVisible(False)
        root.addWidget(self._check_banner)

        splitter = QSplitter(Qt.Horizontal)

        # ── 左侧：配置区 ──────────────────────────────────────────
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 10, 0)
        ll.setSpacing(12)

        # 项目选择
        sel_box = QGroupBox("选择填报项目")
        sel_box.setStyleSheet(
            "QGroupBox{font-weight:bold;color:#1e293b;border:1px solid #e2e8f0;"
            "border-radius:8px;margin-top:6px;padding-top:10px;}"
            "QGroupBox::title{subcontrol-origin:margin;left:12px;}"
        )
        sel_form = QFormLayout(sel_box)
        sel_form.setSpacing(8)
        sel_form.setLabelAlignment(Qt.AlignRight)

        self._cmb_applicant = QComboBox()
        self._cmb_applicant.currentIndexChanged.connect(self._on_applicant_changed)
        self._cmb_project = QComboBox()
        self._cmb_project.currentIndexChanged.connect(self._on_project_changed)

        sel_form.addRow("申报人：",  self._cmb_applicant)
        sel_form.addRow("申报项目：", self._cmb_project)
        ll.addWidget(sel_box)

        # 项目信息预览
        self._info_box = QGroupBox("项目信息预览")
        self._info_box.setStyleSheet(sel_box.styleSheet())
        info_form = QFormLayout(self._info_box)
        info_form.setSpacing(6)
        info_form.setLabelAlignment(Qt.AlignRight)

        self._lbl_industry  = QLabel("—")
        self._lbl_committee = QLabel("—")
        self._lbl_level     = QLabel("—")
        self._lbl_scale     = QLabel("—")
        self._lbl_folder    = QLabel("—")
        self._lbl_folder.setWordWrap(True)

        for label, widget in [
            ("行业：",    self._lbl_industry),
            ("评委会：",  self._lbl_committee),
            ("申报级别：", self._lbl_level),
            ("工程规模：", self._lbl_scale),
            ("材料路径：", self._lbl_folder),
        ]:
            info_form.addRow(label, widget)
        ll.addWidget(self._info_box)

        # 填报选项
        opt_box = QGroupBox("填报选项")
        opt_box.setStyleSheet(sel_box.styleSheet())
        opt_lay = QVBoxLayout(opt_box)
        self._chk_headless = QCheckBox("无头模式（后台运行，不显示浏览器窗口）")
        self._chk_headless.setChecked(False)
        opt_lay.addWidget(self._chk_headless)
        ll.addWidget(opt_box)

        # 操作按钮
        btn_row = QHBoxLayout()
        self._btn_start = QPushButton("▶ 开始自动填报")
        self._btn_start.setObjectName("btnPrimary")
        self._btn_start.setFixedHeight(40)
        self._btn_start.clicked.connect(self._start)

        self._btn_stop = QPushButton("■ 停止 / 关闭浏览器")
        self._btn_stop.setObjectName("btnDanger")
        self._btn_stop.setFixedHeight(40)
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._stop)

        btn_row.addWidget(self._btn_start)
        btn_row.addWidget(self._btn_stop)
        ll.addLayout(btn_row)

        # 总体进度
        self._progress = QProgressBar()
        self._progress.setRange(0, 7)
        self._progress.setValue(0)
        self._progress.setFixedHeight(10)
        self._progress.setStyleSheet(
            "QProgressBar{background:#e2e8f0;border-radius:5px;}"
            "QProgressBar::chunk{background:#2563eb;border-radius:5px;}"
        )
        ll.addWidget(self._progress)
        ll.addStretch()

        splitter.addWidget(left)

        # ── 右侧：运行日志 ────────────────────────────────────────
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(10, 0, 0, 0)
        rl.setSpacing(8)

        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("填报日志："))
        log_header.addStretch()
        btn_clear_log = QPushButton("清空日志")
        btn_clear_log.setObjectName("btnOutline")
        btn_clear_log.clicked.connect(self._clear_log)
        log_header.addWidget(btn_clear_log)
        rl.addLayout(log_header)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        f = QFont("Courier New, Consolas, monospace"); f.setPointSize(11)
        self._log.setFont(f)
        self._log.setStyleSheet(
            "QTextEdit{background:#0f172a;color:#e2e8f0;border-radius:8px;padding:8px;}"
        )
        rl.addWidget(self._log)

        splitter.addWidget(right)
        splitter.setSizes([360, 540])
        root.addWidget(splitter)

    # ── data ──────────────────────────────────────────────────────
    def refresh(self):
        self._check_config()
        self._cmb_applicant.blockSignals(True)
        self._cmb_applicant.clear()
        self._cmb_applicant.addItem("-- 选择申报人 --", None)
        for a in list_applicants():
            self._cmb_applicant.addItem(a["name"], a["id"])
        self._cmb_applicant.blockSignals(False)

    def _check_config(self):
        cfg = load_config()
        username = cfg["website"].get("username", "")
        password = decrypt(cfg["website"].get("password_cipher", ""))
        if not username or not password:
            self._check_banner.setText(
                "⚠ 尚未配置申报网站账号密码，请先前往「系统设置 → 申报网站账号」填写后再使用自动填报。"
            )
            self._check_banner.setStyleSheet(
                "background:#fef9c3;color:#854d0e;border-radius:6px;padding:8px 12px;font-size:12px;"
            )
            self._check_banner.setVisible(True)
        else:
            self._check_banner.setVisible(False)

        # check playwright
        try:
            import playwright
            self._playwright_ok = True
        except ImportError:
            self._check_banner.setText(
                "⚠ Playwright 未安装。请运行：\n"
                "pip install playwright\n"
                "playwright install chromium"
            )
            self._check_banner.setStyleSheet(
                "background:#fee2e2;color:#991b1b;border-radius:6px;padding:8px 12px;font-size:12px;"
            )
            self._check_banner.setVisible(True)
            self._playwright_ok = False

    def _on_applicant_changed(self, _):
        aid = self._cmb_applicant.currentData()
        self._cmb_project.clear()
        self._cmb_project.addItem("-- 选择项目 --", None)
        self._projects = []
        if not aid: return
        self._projects = list_projects(applicant_id=aid)
        for p in self._projects:
            label = f"{p.get('apply_level','')} · {p.get('industry','')} · {p.get('committee','')}"
            self._cmb_project.addItem(label, p["id"])

    def _on_project_changed(self, _):
        pid = self._cmb_project.currentData()
        p   = next((x for x in self._projects if x["id"] == pid), None)
        if not p:
            for lbl in [self._lbl_industry, self._lbl_committee,
                        self._lbl_level, self._lbl_scale, self._lbl_folder]:
                lbl.setText("—")
            return
        self._lbl_industry.setText(p.get("industry") or "—")
        self._lbl_committee.setText(p.get("committee") or "—")
        self._lbl_level.setText(p.get("apply_level") or "—")
        self._lbl_scale.setText(p.get("scale") or "未判断")
        folder = p.get("folder_path") or "未设置"
        self._lbl_folder.setText(folder)

    # ── actions ───────────────────────────────────────────────────
    def _start(self):
        if not getattr(self, "_playwright_ok", True):
            QMessageBox.warning(self, "缺少依赖", "请先安装 Playwright")
            return

        pid = self._cmb_project.currentData()
        aid = self._cmb_applicant.currentData()
        if not pid or not aid:
            QMessageBox.warning(self, "提示", "请选择申报人和申报项目")
            return

        project   = next((x for x in self._projects if x["id"] == pid), None)
        applicant = get_applicant(aid)
        if not applicant or not project:
            QMessageBox.warning(self, "提示", "数据加载失败，请重试")
            return

        # confirm
        name  = applicant.get("name", "")
        level = project.get("apply_level", "")
        ret   = QMessageBox.question(
            self, "确认开始自动填报",
            f"即将为「{name}」填报「{level}」。\n\n"
            f"请确保：\n"
            f"  · 已在设置中配置正确的网站账号密码\n"
            f"  · 申报网站（gxrczc.com）正常可访问\n"
            f"  · 浏览器窗口打开后请勿手动操作\n\n"
            f"自动填写完成后需人工核对并手动点击提交。\n\n确认继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret != QMessageBox.Yes:
            return

        self._log_line("═" * 50)
        self._log_line(f"▶ 开始填报：{name} · {level}")
        self._log_line("═" * 50)

        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._progress.setValue(0)

        headless = self._chk_headless.isChecked()
        self._worker = FillWorker(applicant, project, headless)
        self._worker.log_step.connect(self._on_step)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _stop(self):
        if self._worker:
            self._worker.stop_browser()
            self._worker.quit()
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._log_line("■ 用户手动停止", success=False)

    def _on_step(self, name: str, success: bool, message: str):
        self._log_line(f"{'✅' if success else '❌'}  {name}", success=success)
        if message:
            self._log_line(f"   └─ {message}", muted=True)
        val = self._progress.value()
        self._progress.setValue(min(val + 1, 7))
        color = "#16a34a" if success else "#dc2626"
        self._progress.setStyleSheet(
            f"QProgressBar{{background:#e2e8f0;border-radius:5px;}}"
            f"QProgressBar::chunk{{background:{color};border-radius:5px;}}"
        )

    def _on_finished(self, summary: str):
        self._log_line("═" * 50)
        self._log_line("✅ 填报流程完成", success=True)
        for line in summary.splitlines():
            self._log_line(f"   {line}", muted=True)
        self._log_line("═" * 50)
        self._log_line("请在浏览器中核对信息后手动点击提交！", success=True)
        self._btn_start.setEnabled(True)
        self._progress.setValue(7)

    def _on_error(self, msg: str):
        self._log_line(f"❌ 严重错误：{msg}", success=False)
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        QMessageBox.critical(self, "填报错误", msg)

    # ── log helpers ───────────────────────────────────────────────
    def _log_line(self, text: str, success: bool | None = None, muted: bool = False):
        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        if muted:
            fmt.setForeground(QColor("#64748b"))
        elif success is True:
            fmt.setForeground(QColor("#4ade80"))
        elif success is False:
            fmt.setForeground(QColor("#f87171"))
        else:
            fmt.setForeground(QColor("#e2e8f0"))
        cursor.setCharFormat(fmt)
        cursor.insertText(text + "\n")
        self._log.setTextCursor(cursor)
        self._log.ensureCursorVisible()

    def _clear_log(self):
        self._log.clear()
        self._progress.setValue(0)
