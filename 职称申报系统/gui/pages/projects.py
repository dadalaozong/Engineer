"""申报项目列表页"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView,
    QMessageBox, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QColor
from database.models import list_projects, delete_project, get_fee, list_batches
from gui.pages.project_dialog import ProjectDialog, ALL_INDUSTRIES


RESULT_COLORS = {
    "通过":   ("#166534", "#dcfce7"),
    "未通过": ("#991b1b", "#fee2e2"),
    "待审核": ("#854d0e", "#fef9c3"),
    "":       ("#64748b", "#f1f5f9"),
}


class ProjectsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # optional filter: show only projects for a specific applicant
        self._filter_applicant_id   = None
        self._filter_applicant_name = None
        self._build_ui()

    def set_applicant_filter(self, applicant_id: int, name: str):
        self._filter_applicant_id   = applicant_id
        self._filter_applicant_name = name
        self._filter_label.setText(f"申报人筛选：{name}")
        self._filter_label.setVisible(True)
        self._btn_clear_filter.setVisible(True)
        self.refresh()

    def clear_applicant_filter(self):
        self._filter_applicant_id   = None
        self._filter_applicant_name = None
        self._filter_label.setVisible(False)
        self._btn_clear_filter.setVisible(False)
        self.refresh()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        # ── toolbar ──────────────────────────────────────────────
        toolbar = QHBoxLayout()

        self._cmb_industry = QComboBox()
        self._cmb_industry.addItem("全部行业", None)
        self._cmb_industry.addItems(ALL_INDUSTRIES)
        self._cmb_industry.currentIndexChanged.connect(self.refresh)

        self._cmb_result = QComboBox()
        self._cmb_result.addItems(["全部状态", "待审核", "通过", "未通过"])
        self._cmb_result.currentIndexChanged.connect(self.refresh)

        btn_add = QPushButton("＋ 新增项目")
        btn_add.setObjectName("btnPrimary")
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self._add)

        self._filter_label = QLabel()
        self._filter_label.setStyleSheet(
            "background:#dbeafe; color:#1e40af; border-radius:6px; padding:4px 10px; font-size:12px;"
        )
        self._filter_label.setVisible(False)

        self._btn_clear_filter = QPushButton("✕ 取消筛选")
        self._btn_clear_filter.setObjectName("btnOutline")
        self._btn_clear_filter.setFixedHeight(30)
        self._btn_clear_filter.setVisible(False)
        self._btn_clear_filter.clicked.connect(self.clear_applicant_filter)

        toolbar.addWidget(QLabel("行业："))
        toolbar.addWidget(self._cmb_industry)
        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel("审核结果："))
        toolbar.addWidget(self._cmb_result)
        toolbar.addSpacing(12)
        toolbar.addWidget(self._filter_label)
        toolbar.addWidget(self._btn_clear_filter)
        toolbar.addStretch()
        toolbar.addWidget(btn_add)
        lay.addLayout(toolbar)

        # ── table ─────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            ["申报人", "行业", "评委会", "申报级别", "关联批次", "费用状态", "审核结果", "备注"]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("QTableWidget { alternate-background-color: #f8fafc; }")
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._context_menu)
        self._table.doubleClicked.connect(self._edit_selected)
        lay.addWidget(self._table)

        # status
        self._status = QLabel()
        self._status.setStyleSheet("color:#64748b; font-size:12px;")
        lay.addWidget(self._status)

    # ── data ──────────────────────────────────────────────────────
    def refresh(self):
        rows = list_projects(applicant_id=self._filter_applicant_id)

        # apply filters
        ind_filter = self._cmb_industry.currentData()
        res_filter = self._cmb_result.currentText()
        if ind_filter:
            rows = [r for r in rows if r["industry"] == ind_filter]
        if res_filter != "全部状态":
            rows = [r for r in rows if (r.get("review_result") or "待审核") == res_filter]

        self._data = rows
        self._table.setRowCount(len(rows))

        for i, r in enumerate(rows):
            fee = get_fee(r["id"])
            fee_text = self._fee_label(fee)
            fee_color = self._fee_color(fee)
            result = r.get("review_result") or "待审核"
            batch_text = f"{r.get('batch_year','')}年" if r.get("batch_year") else "—"

            self._table.setItem(i, 0, self._cell(r.get("applicant_name") or ""))
            self._table.setItem(i, 1, self._cell(r.get("industry") or ""))
            self._table.setItem(i, 2, self._cell(r.get("committee") or ""))
            self._table.setItem(i, 3, self._cell(r.get("apply_level") or ""))
            self._table.setItem(i, 4, self._cell(batch_text))

            fee_item = self._cell(fee_text)
            fg, bg = fee_color
            fee_item.setForeground(QColor(fg))
            fee_item.setBackground(QColor(bg))
            self._table.setItem(i, 5, fee_item)

            res_item = self._cell(result)
            fg, bg = RESULT_COLORS.get(result, RESULT_COLORS[""])
            res_item.setForeground(QColor(fg))
            res_item.setBackground(QColor(bg))
            self._table.setItem(i, 6, res_item)

            self._table.setItem(i, 7, self._cell(r.get("note") or ""))

        self._table.resizeRowsToContents()
        self._status.setText(f"共 {len(rows)} 条项目记录")

    @staticmethod
    def _cell(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    @staticmethod
    def _fee_label(fee) -> str:
        if not fee or (fee.get("total") or 0) <= 0:
            return "未设置"
        total = fee.get("total", 0)
        paid  = fee.get("paid", 0)
        if paid >= total:
            return "已结清"
        if paid > 0:
            return f"定金已付 ¥{paid:,.0f}"
        return f"未付 ¥{total:,.0f}"

    @staticmethod
    def _fee_color(fee):
        if not fee or (fee.get("total") or 0) <= 0:
            return "#64748b", "#f1f5f9"
        paid  = fee.get("paid", 0)
        total = fee.get("total", 0)
        if paid >= total:
            return "#166534", "#dcfce7"
        if paid > 0:
            return "#854d0e", "#fef9c3"
        return "#991b1b", "#fee2e2"

    # ── actions ───────────────────────────────────────────────────
    def _selected_row(self):
        rows = self._table.selectionModel().selectedRows()
        return rows[0].row() if rows else None

    def _add(self):
        dlg = ProjectDialog(applicant_id=self._filter_applicant_id, parent=self)
        if dlg.exec_() == ProjectDialog.Accepted:
            self.refresh()

    def _edit_selected(self):
        row = self._selected_row()
        if row is None: return
        pid = self._data[row]["id"]
        dlg = ProjectDialog(project_id=pid, parent=self)
        if dlg.exec_() == ProjectDialog.Accepted:
            self.refresh()

    def _delete_selected(self):
        row = self._selected_row()
        if row is None: return
        r = self._data[row]
        name = r.get("applicant_name", "")
        level = r.get("apply_level", "")
        ret = QMessageBox.question(
            self, "确认删除",
            f"删除「{name}」的 {level} 申报项目记录？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            delete_project(r["id"])
            self.refresh()

    def _mark_result(self, result: str):
        row = self._selected_row()
        if row is None: return
        from database.models import update_project
        update_project(self._data[row]["id"], review_result=result)
        self.refresh()

    def _context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0: return
        self._table.selectRow(row)

        menu = QMenu(self)
        menu.addAction("编辑项目", self._edit_selected)
        result_menu = menu.addMenu("标记审核结果")
        for r in ["通过", "未通过", "待审核"]:
            result_menu.addAction(r, lambda _, rv=r: self._mark_result(rv))
        menu.addSeparator()
        menu.addAction("删除项目", self._delete_selected)
        menu.exec_(QCursor.pos())
