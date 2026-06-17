"""新增 / 编辑申报批次对话框"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QTextEdit,
    QPushButton, QMessageBox, QFrame, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from database.models import insert_batch, update_batch, list_batches
from gui.pages.project_dialog import ALL_INDUSTRIES, INDUSTRY_COMMITTEE

LEVELS = ["中级工程师", "高级工程师", "正高级工程师", "中学一级", "中学高级"]


class BatchDialog(QDialog):
    def __init__(self, batch_id=None, parent=None):
        super().__init__(parent)
        self.batch_id = batch_id
        self.setWindowTitle("编辑批次" if batch_id else "新增申报批次")
        self.setMinimumWidth(440)
        self.setModal(True)
        self._build_ui()
        if batch_id:
            self._load(batch_id)

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(14)

        title = QLabel("编辑申报批次" if self.batch_id else "新增申报批次")
        title.setStyleSheet("font-size:15px; font-weight:bold; color:#1e293b;")
        lay.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet("color:#e2e8f0;")
        lay.addWidget(sep)

        form = QFormLayout(); form.setSpacing(10); form.setLabelAlignment(Qt.AlignRight)

        self.f_year = QComboBox()
        current_year = QDate.currentDate().year()
        self.f_year.addItems([str(y) for y in range(current_year - 1, current_year + 3)])
        self.f_year.setCurrentText(str(current_year))

        self.f_industry = QComboBox()
        self.f_industry.addItems(ALL_INDUSTRIES)
        self.f_industry.currentTextChanged.connect(self._on_industry_changed)

        self.f_committee = QComboBox()
        self._on_industry_changed(self.f_industry.currentText())

        self.f_level = QComboBox()
        self.f_level.addItems(LEVELS)

        self.f_deadline = QDateEdit()
        self.f_deadline.setCalendarPopup(True)
        self.f_deadline.setDate(QDate.currentDate().addMonths(3))
        self.f_deadline.setDisplayFormat("yyyy-MM-dd")

        self.f_note = QTextEdit(); self.f_note.setFixedHeight(64)
        self.f_note.setPlaceholderText("批次备注（可选）")

        form.addRow("年度 *",    self.f_year)
        form.addRow("行业 *",    self.f_industry)
        form.addRow("评委会 *",  self.f_committee)
        form.addRow("申报级别 *", self.f_level)
        form.addRow("截止日期",  self.f_deadline)
        form.addRow("备注",      self.f_note)
        lay.addLayout(form)

        btns = QHBoxLayout(); btns.addStretch()
        cancel = QPushButton("取消"); cancel.setObjectName("btnOutline")
        save   = QPushButton("保存"); save.setObjectName("btnPrimary")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save)
        lay.addLayout(btns)

    def _on_industry_changed(self, industry):
        self.f_committee.clear()
        self.f_committee.addItems(INDUSTRY_COMMITTEE.get(industry, []))

    def _load(self, bid):
        batches = list_batches()
        data = next((b for b in batches if b["id"] == bid), None)
        if not data: return
        self.f_year.setCurrentText(str(data.get("year", "")))
        idx = self.f_industry.findText(data.get("industry", ""))
        if idx >= 0: self.f_industry.setCurrentIndex(idx)
        idx = self.f_committee.findText(data.get("committee", ""))
        if idx >= 0: self.f_committee.setCurrentIndex(idx)
        idx = self.f_level.findText(data.get("level", ""))
        if idx >= 0: self.f_level.setCurrentIndex(idx)
        dl = data.get("deadline") or ""
        if dl:
            self.f_deadline.setDate(QDate.fromString(dl, "yyyy-MM-dd"))
        self.f_note.setPlainText(data.get("note") or "")

    def _save(self):
        year      = int(self.f_year.currentText())
        industry  = self.f_industry.currentText()
        committee = self.f_committee.currentText()
        level     = self.f_level.currentText()
        deadline  = self.f_deadline.date().toString("yyyy-MM-dd")
        note      = self.f_note.toPlainText().strip()

        if self.batch_id:
            update_batch(self.batch_id, year=year, industry=industry,
                         committee=committee, level=level,
                         deadline=deadline, note=note)
        else:
            insert_batch(year, industry, committee, level, deadline, note)
        self.accept()
