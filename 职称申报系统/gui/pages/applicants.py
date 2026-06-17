"""申报人列表页"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox, QMenu, QAction, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor
from database.models import list_applicants, delete_applicant
from gui.pages.applicant_dialog import ApplicantDialog


class ApplicantsPage(QWidget):
    # emitted when user wants to view projects for an applicant
    view_projects = pyqtSignal(int, str)   # (applicant_id, name)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        # ── toolbar ──────────────────────────────────────────────
        toolbar = QHBoxLayout()

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  搜索姓名 / 身份证 / 电话…")
        self._search.setFixedHeight(36)
        self._search.setMinimumWidth(260)
        self._search.textChanged.connect(self._do_search)

        btn_add = QPushButton("＋ 新增申报人")
        btn_add.setObjectName("btnPrimary")
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self._add)

        toolbar.addWidget(self._search)
        toolbar.addStretch()
        toolbar.addWidget(btn_add)
        lay.addLayout(toolbar)

        # ── table ─────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["姓名", "身份证号", "联系电话", "学历", "工作单位", "现有职称", "备注"]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self._table.horizontalHeader().setMinimumSectionSize(80)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            "QTableWidget { alternate-background-color: #f8fafc; }"
        )
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._context_menu)
        self._table.doubleClicked.connect(self._edit_selected)

        lay.addWidget(self._table)

        # ── status bar ───────────────────────────────────────────
        self._status = QLabel()
        self._status.setStyleSheet("color:#64748b; font-size:12px;")
        lay.addWidget(self._status)

    # ── data loading ─────────────────────────────────────────────
    def refresh(self):
        self._load(self._search.text().strip())

    def _do_search(self, text):
        self._load(text.strip())

    def _load(self, search=""):
        rows = list_applicants(search)
        self._table.setRowCount(len(rows))
        self._data = rows  # keep reference for id lookup

        for i, r in enumerate(rows):
            self._table.setItem(i, 0, self._cell(r.get("name", "")))
            self._table.setItem(i, 1, self._cell(self._mask_id(r.get("id_card") or "")))
            self._table.setItem(i, 2, self._cell(r.get("phone") or ""))
            self._table.setItem(i, 3, self._cell(r.get("education") or ""))
            self._table.setItem(i, 4, self._cell(r.get("work_unit") or ""))
            self._table.setItem(i, 5, self._cell(r.get("current_level") or ""))
            self._table.setItem(i, 6, self._cell(r.get("note") or ""))

        self._table.resizeRowsToContents()
        word = f"（搜索：{search}）" if search else ""
        self._status.setText(f"共 {len(rows)} 条记录{word}")

    @staticmethod
    def _cell(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    @staticmethod
    def _mask_id(id_card: str) -> str:
        if len(id_card) == 18:
            return id_card[:6] + "********" + id_card[-4:]
        return id_card

    # ── actions ───────────────────────────────────────────────────
    def _selected_row(self):
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        return rows[0].row()

    def _add(self):
        dlg = ApplicantDialog(parent=self)
        if dlg.exec_() == ApplicantDialog.Accepted:
            self.refresh()

    def _edit_selected(self, index=None):
        row = self._selected_row()
        if row is None:
            return
        aid = self._data[row]["id"]
        dlg = ApplicantDialog(applicant_id=aid, parent=self)
        if dlg.exec_() == ApplicantDialog.Accepted:
            self.refresh()

    def _delete_selected(self):
        row = self._selected_row()
        if row is None:
            return
        name = self._data[row]["name"]
        aid  = self._data[row]["id"]
        ret = QMessageBox.question(
            self, "确认删除",
            f"删除申报人「{name}」将同时删除其所有项目和材料记录，确认继续吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            delete_applicant(aid)
            self.refresh()

    def _view_projects(self):
        row = self._selected_row()
        if row is None:
            return
        r = self._data[row]
        self.view_projects.emit(r["id"], r["name"])

    def _context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        self._table.selectRow(row)

        menu = QMenu(self)
        menu.addAction("查看项目", self._view_projects)
        menu.addAction("编辑信息", self._edit_selected)
        menu.addSeparator()
        act_del = QAction("删除", self)
        act_del.setProperty("danger", True)
        act_del.triggered.connect(self._delete_selected)
        menu.addAction(act_del)
        menu.exec_(QCursor.pos())
