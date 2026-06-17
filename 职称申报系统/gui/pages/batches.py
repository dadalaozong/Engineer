"""批次管理页 — 含截止日期倒计时三色预警"""
from datetime import date
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QMessageBox,
    QMenu, QScrollArea, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor, QColor, QFont
from database.models import list_batches, delete_batch, list_projects
from gui.pages.batch_dialog import BatchDialog
from gui.widgets import SectionTitle


def _urgency(days_left: int):
    """Return (text, fg, bg) based on days remaining."""
    if days_left < 0:
        return f"已过期 {-days_left} 天", "#6b7280", "#f3f4f6"
    if days_left <= 14:
        return f"🔴 紧急  {days_left} 天", "#991b1b", "#fee2e2"
    if days_left <= 30:
        return f"⚠  还剩 {days_left} 天", "#854d0e", "#fef9c3"
    return f"距截止 {days_left} 天", "#166534", "#dcfce7"


class BatchesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        # refresh countdown every minute
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60_000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── toolbar ──────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.addWidget(SectionTitle("申报批次管理"))
        toolbar.addStretch()
        btn_add = QPushButton("＋ 新增批次")
        btn_add.setObjectName("btnPrimary")
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self._add)
        toolbar.addWidget(btn_add)
        root.addLayout(toolbar)

        # ── urgent banner (hidden by default) ────────────────────
        self._banner = QLabel()
        self._banner.setWordWrap(True)
        self._banner.setStyleSheet(
            "background:#fee2e2; color:#991b1b; border-radius:8px;"
            "padding:10px 16px; font-weight:bold; font-size:13px;"
        )
        self._banner.setVisible(False)
        root.addWidget(self._banner)

        # ── deadline cards row ────────────────────────────────────
        self._cards_label = SectionTitle("即将截止（60天内）")
        root.addWidget(self._cards_label)
        self._cards_area = QWidget()
        self._cards_layout = QHBoxLayout(self._cards_area)
        self._cards_layout.setSpacing(14)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._cards_area)

        # ── full table ────────────────────────────────────────────
        root.addWidget(SectionTitle("全部批次"))

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["年度", "行业", "评委会", "级别", "截止日期", "倒计时", "项目数"]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("QTableWidget{alternate-background-color:#f8fafc;}")
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._context_menu)
        self._table.doubleClicked.connect(self._edit_selected)
        root.addWidget(self._table)

        self._status = QLabel()
        self._status.setStyleSheet("color:#64748b; font-size:12px;")
        root.addWidget(self._status)

    # ── data ──────────────────────────────────────────────────────
    def refresh(self):
        batches = list_batches()
        today   = date.today()
        self._data = batches

        # project count per batch
        all_projects = list_projects()
        proj_count = {}
        for p in all_projects:
            bid = p.get("batch_id")
            if bid:
                proj_count[bid] = proj_count.get(bid, 0) + 1

        # ── cards (≤60 days) ─────────────────────────────────────
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        urgent_names = []
        card_count = 0
        for b in batches:
            if not b.get("deadline"): continue
            try:
                dl = date.fromisoformat(b["deadline"])
                days_left = (dl - today).days
            except ValueError:
                continue
            if days_left < 0 or days_left > 60:
                continue

            text, fg, bg = _urgency(days_left)
            card = self._make_card(b, text, fg, bg)
            self._cards_layout.addWidget(card)
            card_count += 1
            if days_left <= 14:
                urgent_names.append(f"{b['year']}年{b['level']}（{b['committee']}）")
            if card_count >= 4:
                break

        if card_count == 0:
            lbl = QLabel("暂无 60 天内即将截止的批次")
            lbl.setStyleSheet("color:#94a3b8; font-size:13px;")
            self._cards_layout.addWidget(lbl)
        self._cards_layout.addStretch()

        # urgent banner
        if urgent_names:
            self._banner.setText("⚠ 紧急提醒（14天内截止）：" + "、".join(urgent_names))
            self._banner.setVisible(True)
        else:
            self._banner.setVisible(False)

        # ── table ─────────────────────────────────────────────────
        self._table.setRowCount(len(batches))
        for i, b in enumerate(batches):
            dl_str = b.get("deadline") or "—"
            if b.get("deadline"):
                try:
                    dl = date.fromisoformat(b["deadline"])
                    days_left = (dl - today).days
                    text, fg, bg = _urgency(days_left)
                except ValueError:
                    text, fg, bg = "日期格式错误", "#64748b", "#f1f5f9"
            else:
                text, fg, bg = "未设置", "#64748b", "#f1f5f9"

            cnt = proj_count.get(b["id"], 0)
            self._table.setItem(i, 0, self._cell(str(b.get("year", ""))))
            self._table.setItem(i, 1, self._cell(b.get("industry", "")))
            self._table.setItem(i, 2, self._cell(b.get("committee", "")))
            self._table.setItem(i, 3, self._cell(b.get("level", "")))
            self._table.setItem(i, 4, self._cell(dl_str))

            countdown_item = self._cell(text)
            countdown_item.setForeground(QColor(fg))
            countdown_item.setBackground(QColor(bg))
            self._table.setItem(i, 5, countdown_item)

            cnt_item = self._cell(str(cnt) if cnt else "0")
            cnt_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(i, 6, cnt_item)

        self._table.resizeRowsToContents()
        self._status.setText(f"共 {len(batches)} 个批次")

    @staticmethod
    def _cell(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def _make_card(self, b: dict, countdown_text: str, fg: str, bg: str) -> QWidget:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background:white; border:1px solid #e2e8f0; border-radius:8px; }}"
        )
        card.setFixedWidth(220)
        lay = QVBoxLayout(card)
        lay.setSpacing(6)
        lay.setContentsMargins(14, 12, 14, 12)

        committee_lbl = QLabel(b.get("committee", ""))
        committee_lbl.setStyleSheet("color:#64748b; font-size:11px;")
        committee_lbl.setWordWrap(True)

        name_lbl = QLabel(f"{b.get('year')}年度 {b.get('level')}")
        name_lbl.setStyleSheet("font-weight:bold; font-size:13px; color:#1e293b;")

        deadline_lbl = QLabel(f"截止：{b.get('deadline','未设置')}")
        deadline_lbl.setStyleSheet("color:#64748b; font-size:11px;")

        badge = QLabel(countdown_text)
        badge.setStyleSheet(
            f"color:{fg}; background:{bg}; border-radius:10px;"
            f"padding:3px 10px; font-size:11px; font-weight:bold;"
        )
        badge.setFixedHeight(24)

        lay.addWidget(committee_lbl)
        lay.addWidget(name_lbl)
        lay.addWidget(deadline_lbl)
        lay.addWidget(badge)
        return card

    # ── actions ───────────────────────────────────────────────────
    def _selected_row(self):
        rows = self._table.selectionModel().selectedRows()
        return rows[0].row() if rows else None

    def _add(self):
        dlg = BatchDialog(parent=self)
        if dlg.exec_() == BatchDialog.Accepted:
            self.refresh()

    def _edit_selected(self):
        row = self._selected_row()
        if row is None: return
        dlg = BatchDialog(batch_id=self._data[row]["id"], parent=self)
        if dlg.exec_() == BatchDialog.Accepted:
            self.refresh()

    def _delete_selected(self):
        row = self._selected_row()
        if row is None: return
        b = self._data[row]
        ret = QMessageBox.question(
            self, "确认删除",
            f"删除「{b['year']}年度 {b['level']}」批次？\n关联项目的批次绑定将被清除。",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            delete_batch(b["id"])
            self.refresh()

    def _context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0: return
        self._table.selectRow(row)
        menu = QMenu(self)
        menu.addAction("编辑批次", self._edit_selected)
        menu.addSeparator()
        menu.addAction("删除批次", self._delete_selected)
        menu.exec_(QCursor.pos())
