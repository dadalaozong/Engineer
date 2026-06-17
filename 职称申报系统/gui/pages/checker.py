"""完整性检查页 — 对选定批次所有项目逐一检查材料完整性，生成汇总报告。"""
from __future__ import annotations
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QProgressBar,
    QFrame, QMessageBox, QFileDialog, QMenu
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QCursor
from database.models import list_batches, list_projects, get_applicant
from core.folder_builder import scan_folder
from gui.widgets import SectionTitle
import csv


class CheckWorker(QThread):
    progress = pyqtSignal(int, int)           # current, total
    result   = pyqtSignal(int, str, int, int) # project_id, status, has, total

    def __init__(self, projects: list[dict]):
        super().__init__()
        self.projects = projects

    def run(self):
        total_p = len(self.projects)
        for i, p in enumerate(self.projects):
            self.progress.emit(i + 1, total_p)
            pid    = p["id"]
            folder = p.get("folder_path")
            level  = p.get("apply_level", "高级工程师")

            if not folder or not Path(folder).exists():
                self.result.emit(pid, "未设置文件夹", 0, 0)
                continue

            items    = scan_folder(folder, level)
            has_cnt  = sum(1 for r in items if r["has_files"])
            total_cnt = len(items)
            if has_cnt == total_cnt:
                status = "完整"
            elif has_cnt == 0:
                status = "全部缺失"
            else:
                status = f"缺{total_cnt - has_cnt}项"
            self.result.emit(pid, status, has_cnt, total_cnt)


class CheckerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects   = []
        self._check_data = {}   # pid → {status, has, total}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)
        root.addWidget(SectionTitle("材料完整性检查"))

        # ── 筛选工具栏 ────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("筛选批次："))
        self._cmb_batch = QComboBox()
        self._cmb_batch.setMinimumWidth(260)
        self._cmb_batch.currentIndexChanged.connect(self._on_batch_changed)
        toolbar.addWidget(self._cmb_batch)

        toolbar.addWidget(QLabel("状态筛选："))
        self._cmb_filter = QComboBox()
        self._cmb_filter.addItems(["全部", "完整", "缺项", "未设置文件夹"])
        self._cmb_filter.currentIndexChanged.connect(self._apply_filter)
        toolbar.addWidget(self._cmb_filter)

        toolbar.addStretch()

        self._btn_check = QPushButton("🔍 开始检查")
        self._btn_check.setObjectName("btnPrimary")
        self._btn_check.setFixedHeight(36)
        self._btn_check.clicked.connect(self._start_check)
        toolbar.addWidget(self._btn_check)

        btn_export = QPushButton("导出报告")
        btn_export.setObjectName("btnOutline")
        btn_export.setFixedHeight(36)
        btn_export.clicked.connect(self._export)
        toolbar.addWidget(btn_export)
        root.addLayout(toolbar)

        # ── 总体进度 ──────────────────────────────────────────────
        prog_row = QHBoxLayout()
        self._prog_text = QLabel("请选择批次后点击「开始检查」")
        self._prog_text.setStyleSheet("color:#64748b; font-size:12px;")
        self._prog_bar  = QProgressBar()
        self._prog_bar.setRange(0, 100)
        self._prog_bar.setValue(0)
        self._prog_bar.setFixedHeight(12)
        self._prog_bar.setTextVisible(False)
        self._prog_bar.setStyleSheet(
            "QProgressBar{background:#e2e8f0;border-radius:6px;}"
            "QProgressBar::chunk{background:#2563eb;border-radius:6px;}"
        )
        prog_row.addWidget(self._prog_text)
        prog_row.addWidget(self._prog_bar, 1)
        root.addLayout(prog_row)

        # ── 汇总卡片 ──────────────────────────────────────────────
        self._summary_row = QHBoxLayout()
        self._summary_row.setSpacing(12)
        self._s_total    = self._summary_card("检查总数", "0", "#2563eb")
        self._s_complete = self._summary_card("材料完整", "0", "#16a34a")
        self._s_missing  = self._summary_card("存在缺项", "0", "#d97706")
        self._s_nofolder = self._summary_card("未设置文件夹", "0", "#dc2626")
        for card, _ in [self._s_total, self._s_complete, self._s_missing, self._s_nofolder]:
            self._summary_row.addWidget(card)
        root.addLayout(self._summary_row)

        # ── 明细表格 ──────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["申报人", "行业", "评委会", "级别", "已上传", "总项", "完整性状态"]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("QTableWidget{alternate-background-color:#f8fafc;}")
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._context_menu)
        root.addWidget(self._table)

        self._status_bar = QLabel()
        self._status_bar.setStyleSheet("color:#64748b; font-size:12px;")
        root.addWidget(self._status_bar)

    def _summary_card(self, label: str, value: str, color: str):
        card = QFrame()
        card.setStyleSheet(
            "QFrame{background:white;border:1px solid #e2e8f0;border-radius:8px;}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(4)
        lbl = QLabel(label); lbl.setStyleSheet("color:#64748b;font-size:11px;")
        val = QLabel(value)
        from PyQt5.QtGui import QFont as QF
        f = QF(); f.setPointSize(20); f.setBold(True); val.setFont(f)
        val.setStyleSheet(f"color:{color};")
        lay.addWidget(lbl); lay.addWidget(val)
        return card, val

    # ── data ──────────────────────────────────────────────────────
    def refresh(self):
        self._cmb_batch.blockSignals(True)
        current = self._cmb_batch.currentData()
        self._cmb_batch.clear()
        self._cmb_batch.addItem("全部项目（不限批次）", None)
        for b in list_batches():
            label = f"{b['year']}年 {b['industry']} {b['level']}"
            self._cmb_batch.addItem(label, b["id"])
        # restore
        for i in range(self._cmb_batch.count()):
            if self._cmb_batch.itemData(i) == current:
                self._cmb_batch.setCurrentIndex(i); break
        self._cmb_batch.blockSignals(False)
        self._on_batch_changed()

    def _on_batch_changed(self):
        bid = self._cmb_batch.currentData()
        self._projects = list_projects(batch_id=bid)
        self._check_data = {}
        self._populate_table(self._projects)
        self._update_summary()

    def _populate_table(self, projects: list[dict]):
        self._table.setRowCount(len(projects))
        for i, p in enumerate(projects):
            pid = p["id"]
            cd  = self._check_data.get(pid)
            has   = str(cd["has"])   if cd else "—"
            total = str(cd["total"]) if cd else "—"
            status_text = cd["status"] if cd else "待检查"
            fg, bg = self._status_color(status_text)

            self._table.setItem(i, 0, self._cell(p.get("applicant_name") or ""))
            self._table.setItem(i, 1, self._cell(p.get("industry") or ""))
            self._table.setItem(i, 2, self._cell(p.get("committee") or ""))
            self._table.setItem(i, 3, self._cell(p.get("apply_level") or ""))
            has_item = self._cell(has); has_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 4, has_item)
            tot_item = self._cell(total); tot_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 5, tot_item)
            st_item = self._cell(status_text)
            st_item.setForeground(QColor(fg)); st_item.setBackground(QColor(bg))
            self._table.setItem(i, 6, st_item)

        self._table.resizeRowsToContents()
        self._status_bar.setText(f"共 {len(projects)} 条记录")

    def _apply_filter(self):
        f = self._cmb_filter.currentText()
        if f == "全部":
            filtered = self._projects
        elif f == "完整":
            filtered = [p for p in self._projects
                        if self._check_data.get(p["id"], {}).get("status") == "完整"]
        elif f == "缺项":
            filtered = [p for p in self._projects
                        if "缺" in self._check_data.get(p["id"], {}).get("status", "")]
        else:
            filtered = [p for p in self._projects
                        if self._check_data.get(p["id"], {}).get("status") == "未设置文件夹"
                        or p["id"] not in self._check_data]
        self._populate_table(filtered)

    def _update_summary(self):
        total    = len(self._check_data)
        complete = sum(1 for v in self._check_data.values() if v["status"] == "完整")
        missing  = sum(1 for v in self._check_data.values() if "缺" in v["status"])
        nofolder = sum(1 for v in self._check_data.values() if v["status"] == "未设置文件夹")
        self._s_total[1].setText(str(len(self._projects)))
        self._s_complete[1].setText(str(complete))
        self._s_missing[1].setText(str(missing))
        self._s_nofolder[1].setText(str(nofolder))

        if total > 0:
            pct = int(complete / total * 100)
            color = "#16a34a" if pct >= 90 else "#d97706" if pct >= 60 else "#dc2626"
            self._prog_bar.setValue(pct)
            self._prog_bar.setStyleSheet(
                f"QProgressBar{{background:#e2e8f0;border-radius:6px;}}"
                f"QProgressBar::chunk{{background:{color};border-radius:6px;}}"
            )
            self._prog_text.setText(f"完整率：{complete}/{total}（{pct}%）")

    # ── check worker ──────────────────────────────────────────────
    def _start_check(self):
        if not self._projects:
            QMessageBox.information(self, "提示", "当前批次下没有申报项目"); return

        self._btn_check.setEnabled(False)
        self._prog_text.setText("检查中…")
        self._prog_bar.setValue(0)
        self._check_data = {}

        self._worker = CheckWorker(self._projects)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.result.connect(self._on_worker_result)
        self._worker.finished.connect(self._on_worker_done)
        self._worker.start()

    def _on_worker_progress(self, current: int, total: int):
        pct = int(current / total * 100)
        self._prog_bar.setValue(pct)
        self._prog_text.setText(f"检查中 {current}/{total}…")

    def _on_worker_result(self, pid: int, status: str, has: int, total: int):
        self._check_data[pid] = {"status": status, "has": has, "total": total}

    def _on_worker_done(self):
        self._btn_check.setEnabled(True)
        self._apply_filter()
        self._update_summary()

    # ── export ────────────────────────────────────────────────────
    def _export(self):
        if not self._check_data:
            QMessageBox.information(self, "提示", "请先执行检查"); return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出完整性报告", "材料完整性报告.csv", "CSV 文件 (*.csv)"
        )
        if not path: return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["申报人", "行业", "评委会", "级别", "已上传", "总项", "状态"])
                for p in self._projects:
                    cd = self._check_data.get(p["id"], {})
                    writer.writerow([
                        p.get("applicant_name", ""),
                        p.get("industry", ""),
                        p.get("committee", ""),
                        p.get("apply_level", ""),
                        cd.get("has", ""),
                        cd.get("total", ""),
                        cd.get("status", "待检查"),
                    ])
            QMessageBox.information(self, "导出成功", f"已保存至：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0: return
        self._table.selectRow(row)
        menu = QMenu(self)
        menu.addAction("打开材料文件夹", lambda: self._open_folder(row))
        menu.exec_(QCursor.pos())

    def _open_folder(self, row: int):
        # find project from visible rows
        name = self._table.item(row, 0).text() if self._table.item(row, 0) else ""
        p = next((x for x in self._projects if (x.get("applicant_name") or "") == name), None)
        if not p or not p.get("folder_path"):
            QMessageBox.information(self, "提示", "该项目未设置材料文件夹"); return
        import os, sys, subprocess
        path = p["folder_path"]
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    @staticmethod
    def _status_color(status: str):
        if status == "完整":
            return "#166534", "#dcfce7"
        if "缺" in status:
            return "#854d0e", "#fef9c3"
        if status == "全部缺失":
            return "#991b1b", "#fee2e2"
        if status == "未设置文件夹":
            return "#991b1b", "#fee2e2"
        return "#64748b", "#f3f4f6"

    @staticmethod
    def _cell(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item
