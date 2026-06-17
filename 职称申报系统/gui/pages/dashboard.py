"""Dashboard — 首页概览"""
from datetime import date
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from database.models import dashboard_stats, list_batches
from gui.widgets import StatCard, DeadlineCard, SectionTitle


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setSpacing(16)

        # stat row
        self._stat_row = QHBoxLayout()
        self._stat_row.setSpacing(14)
        self._stat_cards = {}
        for key, label, sub in [
            ("total_applicants", "申报人总数", ""),
            ("total_projects", "申报项目数", ""),
            ("total_fees", "已收费用(元)", ""),
            ("pending_fees", "待收费用(元)", ""),
        ]:
            card = StatCard(label, "—", sub)
            self._stat_cards[key] = card
            self._stat_row.addWidget(card)
        lay.addLayout(self._stat_row)

        # deadline section
        lay.addWidget(SectionTitle("即将截止的申报批次"))
        self._dl_row = QHBoxLayout()
        self._dl_row.setSpacing(14)
        self._dl_placeholder = QLabel("暂无即将截止的批次")
        self._dl_placeholder.setStyleSheet("color:#94a3b8; font-size:13px;")
        self._dl_row.addWidget(self._dl_placeholder)
        self._dl_row.addStretch()
        lay.addLayout(self._dl_row)

        lay.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll)

    def refresh(self):
        stats = dashboard_stats()
        self._stat_cards["total_applicants"].update_value(str(stats["total_applicants"]))
        self._stat_cards["total_projects"].update_value(str(stats["total_projects"]))
        self._stat_cards["total_fees"].update_value(f"¥{stats['total_fees']:,.0f}")
        self._stat_cards["pending_fees"].update_value(f"¥{stats['pending_fees']:,.0f}")

        # rebuild deadline cards
        while self._dl_row.count():
            item = self._dl_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        today = date.today()
        batches = list_batches()
        shown = 0
        for b in batches:
            if not b.get("deadline"):
                continue
            try:
                dl = date.fromisoformat(b["deadline"])
                days_left = (dl - today).days
                if 0 <= days_left <= 60:
                    name = f"{b['year']}年度{b['level']} ({b['industry']})"
                    card = DeadlineCard(b["committee"], name, days_left)
                    self._dl_row.addWidget(card)
                    shown += 1
                    if shown >= 3:
                        break
            except ValueError:
                continue

        if shown == 0:
            placeholder = QLabel("暂无 60 天内即将截止的批次")
            placeholder.setStyleSheet("color:#94a3b8; font-size:13px;")
            self._dl_row.addWidget(placeholder)
        self._dl_row.addStretch()
