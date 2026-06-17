"""材料目录管理页 — 生成文件夹结构、扫描完整性、打开文件夹"""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QFileDialog,
    QMessageBox, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from database.models import list_applicants, list_projects, update_project
from core.folder_builder import build_folder, scan_folder, get_material_list
from gui.widgets import SectionTitle


class DocManagerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects    = []
        self._scan_result = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)
        root.addWidget(SectionTitle("材料目录管理"))

        # ── 选择申报项目 ──────────────────────────────────────────
        select_box = QFrame()
        select_box.setStyleSheet(
            "QFrame{background:white;border:1px solid #e2e8f0;border-radius:8px;padding:4px;}"
        )
        select_lay = QHBoxLayout(select_box)
        select_lay.setContentsMargins(14, 10, 14, 10)
        select_lay.setSpacing(12)

        select_lay.addWidget(QLabel("申报人："))
        self._cmb_applicant = QComboBox()
        self._cmb_applicant.setMinimumWidth(160)
        self._cmb_applicant.currentIndexChanged.connect(self._on_applicant_changed)
        select_lay.addWidget(self._cmb_applicant)

        select_lay.addWidget(QLabel("申报项目："))
        self._cmb_project = QComboBox()
        self._cmb_project.setMinimumWidth(220)
        self._cmb_project.currentIndexChanged.connect(self._on_project_changed)
        select_lay.addWidget(self._cmb_project)

        select_lay.addStretch()

        btn_create = QPushButton("📁 生成标准文件夹")
        btn_create.setObjectName("btnPrimary")
        btn_create.clicked.connect(self._create_folder)

        btn_scan = QPushButton("🔄 扫描完整性")
        btn_scan.setObjectName("btnOutline")
        btn_scan.clicked.connect(self._scan)

        btn_open = QPushButton("📂 打开文件夹")
        btn_open.setObjectName("btnOutline")
        btn_open.clicked.connect(self._open_folder)

        select_lay.addWidget(btn_create)
        select_lay.addWidget(btn_scan)
        select_lay.addWidget(btn_open)
        root.addWidget(select_box)

        # ── 完整性进度条 ──────────────────────────────────────────
        prog_row = QHBoxLayout()
        self._prog_label = QLabel("请先选择申报项目并扫描")
        self._prog_label.setStyleSheet("color:#64748b; font-size:12px;")
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(12)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(
            "QProgressBar{background:#e2e8f0;border-radius:6px;}"
            "QProgressBar::chunk{background:#2563eb;border-radius:6px;}"
        )
        prog_row.addWidget(self._prog_label)
        prog_row.addWidget(self._progress, 1)
        root.addLayout(prog_row)

        # ── 材料清单表格 ──────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["材料名称", "文件夹路径", "文件数量", "状态"])
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("QTableWidget{alternate-background-color:#f8fafc;}")
        self._table.doubleClicked.connect(self._open_row_folder)
        root.addWidget(self._table)

        hint = QLabel("💡 双击行可打开对应子文件夹")
        hint.setStyleSheet("color:#94a3b8; font-size:11px;")
        root.addWidget(hint)

    # ── data ──────────────────────────────────────────────────────
    def refresh(self):
        self._cmb_applicant.blockSignals(True)
        self._cmb_applicant.clear()
        self._cmb_applicant.addItem("-- 选择申报人 --", None)
        for a in list_applicants():
            self._cmb_applicant.addItem(a["name"], a["id"])
        self._cmb_applicant.blockSignals(False)
        self._cmb_applicant.setCurrentIndex(0)
        self._cmb_project.clear()
        self._table.setRowCount(0)

    def _on_applicant_changed(self, _):
        aid = self._cmb_applicant.currentData()
        self._cmb_project.clear()
        self._cmb_project.addItem("-- 选择项目 --", None)
        if not aid:
            return
        self._projects = list_projects(applicant_id=aid)
        for p in self._projects:
            label = f"{p.get('apply_level','')} · {p.get('industry','')}"
            self._cmb_project.addItem(label, p["id"])

    def _on_project_changed(self, _):
        self._table.setRowCount(0)
        self._progress.setValue(0)
        self._prog_label.setText("请扫描查看完整性")
        pid = self._cmb_project.currentData()
        if not pid:
            return
        p = next((x for x in self._projects if x["id"] == pid), None)
        if not p:
            return
        level = p.get("apply_level", "高级工程师")
        # show expected list without scan
        items = get_material_list(level)
        self._table.setRowCount(len(items))
        for i, (display, folder_name) in enumerate(items):
            self._table.setItem(i, 0, self._cell(display))
            self._table.setItem(i, 1, self._cell(folder_name))
            self._table.setItem(i, 2, self._cell("—"))
            lbl = self._cell("待扫描")
            lbl.setForeground(QColor("#94a3b8"))
            self._table.setItem(i, 3, lbl)
        self._table.resizeRowsToContents()

    def _current_project(self):
        pid = self._cmb_project.currentData()
        return next((x for x in self._projects if x["id"] == pid), None)

    def _current_folder(self) -> str | None:
        p = self._current_project()
        return p.get("folder_path") if p else None

    # ── actions ───────────────────────────────────────────────────
    def _create_folder(self):
        p = self._current_project()
        if not p:
            QMessageBox.warning(self, "提示", "请先选择申报项目"); return

        base = QFileDialog.getExistingDirectory(self, "选择保存位置", str(Path.home()))
        if not base:
            return

        applicant_name = self._cmb_applicant.currentText()
        level          = p.get("apply_level", "高级工程师")
        root_path, _   = build_folder(base, applicant_name, level)

        update_project(p["id"], folder_path=root_path)
        # refresh project list so folder_path is fresh
        self._on_applicant_changed(None)
        for i in range(self._cmb_project.count()):
            if self._cmb_project.itemData(i) == p["id"]:
                self._cmb_project.setCurrentIndex(i)
                break

        QMessageBox.information(
            self, "文件夹已生成",
            f"标准材料文件夹已创建：\n{root_path}\n\n请将对应材料扫描件放入各子文件夹。"
        )
        self._open_path(root_path)

    def _scan(self):
        p = self._current_project()
        if not p:
            QMessageBox.warning(self, "提示", "请先选择申报项目"); return

        folder = p.get("folder_path")
        if not folder or not Path(folder).exists():
            QMessageBox.warning(
                self, "提示",
                "尚未设置材料文件夹，或文件夹不存在。\n请先点击「生成标准文件夹」或在项目编辑中设置路径。"
            )
            return

        level = p.get("apply_level", "高级工程师")
        self._scan_result = scan_folder(folder, level)

        self._table.setRowCount(len(self._scan_result))
        has_count = sum(1 for r in self._scan_result if r["has_files"])
        total     = len(self._scan_result)

        for i, r in enumerate(self._scan_result):
            self._table.setItem(i, 0, self._cell(r["display_name"]))
            self._table.setItem(i, 1, self._cell(r["path"]))
            cnt_item = self._cell(str(r["file_count"]) if r["exists"] else "文件夹缺失")
            self._table.setItem(i, 2, cnt_item)

            if not r["exists"]:
                status, fg, bg = "⚠ 文件夹缺失", "#854d0e", "#fef9c3"
            elif r["has_files"]:
                status, fg, bg = f"✅ 已上传 {r['file_count']} 个", "#166534", "#dcfce7"
            else:
                status, fg, bg = "❌ 待上传", "#991b1b", "#fee2e2"

            lbl = self._cell(status)
            lbl.setForeground(QColor(fg))
            lbl.setBackground(QColor(bg))
            self._table.setItem(i, 3, lbl)

        self._table.resizeRowsToContents()

        pct = int(has_count / total * 100) if total > 0 else 0
        self._progress.setValue(pct)
        color = "#16a34a" if pct >= 90 else "#d97706" if pct >= 60 else "#dc2626"
        self._progress.setStyleSheet(
            f"QProgressBar{{background:#e2e8f0;border-radius:6px;}}"
            f"QProgressBar::chunk{{background:{color};border-radius:6px;}}"
        )
        self._prog_label.setText(f"材料完整性：{has_count}/{total}  ({pct}%)")

    def _open_folder(self):
        folder = self._current_folder()
        if not folder:
            QMessageBox.warning(self, "提示", "未设置材料文件夹")
            return
        self._open_path(folder)

    def _open_row_folder(self, index):
        row = index.row()
        if row < 0 or row >= len(self._scan_result):
            return
        path = self._scan_result[row]["path"]
        if Path(path).exists():
            self._open_path(path)
        else:
            QMessageBox.information(self, "提示", f"文件夹不存在：\n{path}")

    @staticmethod
    def _open_path(path: str):
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    @staticmethod
    def _cell(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
