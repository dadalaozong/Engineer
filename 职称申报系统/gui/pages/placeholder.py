"""Placeholder page for modules not yet implemented."""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class PlaceholderPage(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)

        icon = QLabel("🚧")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size:48px;")

        lbl = QLabel(f"{title}\n功能开发中…")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color:#94a3b8; font-size:15px;")

        lay.addWidget(icon)
        lay.addWidget(lbl)

    def refresh(self):
        pass
