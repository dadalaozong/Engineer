"""Reusable small widgets."""
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from gui.styles import ACCENT, SUCCESS, WARNING, DANGER, TEXT_MUTED


class StatCard(QWidget):
    def __init__(self, label: str, value: str, sub: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        lay = QVBoxLayout(self)
        lay.setSpacing(4)

        lbl = QLabel(label)
        lbl.setObjectName("statLabel")

        num = QLabel(value)
        num.setObjectName("statNum")
        f = num.font()
        f.setPointSize(20)
        f.setBold(True)
        num.setFont(f)

        lay.addWidget(lbl)
        lay.addWidget(num)
        if sub:
            s = QLabel(sub)
            s.setObjectName("statSub")
            lay.addWidget(s)

        self.num_label = num
        self.lbl_label = lbl

    def update_value(self, value: str, sub: str = ""):
        self.num_label.setText(value)


class DeadlineCard(QWidget):
    """Shows a single batch deadline with urgency color."""
    def __init__(self, committee: str, batch_name: str, days_left: int, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        lay = QVBoxLayout(self)
        lay.setSpacing(4)

        com_lbl = QLabel(committee)
        com_lbl.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px;")

        name_lbl = QLabel(batch_name)
        name_lbl.setStyleSheet("font-weight:bold; font-size:13px; color:#1e293b;")
        name_lbl.setWordWrap(True)

        if days_left > 30:
            color, text = "#16a34a", f"距截止 {days_left} 天"
            bg = "#dcfce7"
        elif days_left > 14:
            color, text = "#d97706", f"⚠ 还剩 {days_left} 天"
            bg = "#fef9c3"
        else:
            color, text = "#dc2626", f"🔴 紧急 {days_left} 天"
            bg = "#fee2e2"

        badge = QLabel(text)
        badge.setStyleSheet(
            f"color:{color}; background:{bg}; border-radius:10px;"
            f"padding:2px 10px; font-size:11px; font-weight:bold;"
        )
        badge.setFixedHeight(22)

        lay.addWidget(com_lbl)
        lay.addWidget(name_lbl)
        lay.addWidget(badge)
        lay.addStretch()


class SectionTitle(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        f = self.font()
        f.setPointSize(13)
        f.setBold(True)
        self.setFont(f)
        self.setStyleSheet("color:#1e293b; padding:0 0 4px;")


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet("color:#e2e8f0;")


def fee_status_badge(paid: float, total: float) -> QLabel:
    lbl = QLabel()
    lbl.setFixedHeight(20)
    if total <= 0:
        lbl.setText("未设置")
        lbl.setStyleSheet("color:#64748b; background:#f1f5f9; border-radius:4px; padding:1px 6px; font-size:11px;")
    elif paid >= total:
        lbl.setText("已结清")
        lbl.setStyleSheet("color:#166534; background:#dcfce7; border-radius:4px; padding:1px 6px; font-size:11px; font-weight:bold;")
    elif paid > 0:
        lbl.setText("定金已付")
        lbl.setStyleSheet("color:#854d0e; background:#fef9c3; border-radius:4px; padding:1px 6px; font-size:11px; font-weight:bold;")
    else:
        lbl.setText("未付")
        lbl.setStyleSheet("color:#991b1b; background:#fee2e2; border-radius:4px; padding:1px 6px; font-size:11px; font-weight:bold;")
    return lbl
