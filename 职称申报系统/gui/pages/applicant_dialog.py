"""新增 / 编辑申报人对话框"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QTextEdit,
    QPushButton, QDialogButtonBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from database.models import insert_applicant, update_applicant, get_applicant


EDUCATION_OPTIONS = ["高中/中专", "大专", "本科", "硕士", "博士"]
LEVEL_OPTIONS     = ["无", "技术员", "助理工程师", "工程师", "高级工程师", "正高级工程师"]


class ApplicantDialog(QDialog):
    """applicant_id=None → 新增模式；否则 → 编辑模式"""

    def __init__(self, applicant_id=None, parent=None):
        super().__init__(parent)
        self.applicant_id = applicant_id
        self.setWindowTitle("编辑申报人" if applicant_id else "新增申报人")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        if applicant_id:
            self._load(applicant_id)

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(16)

        title = QLabel("编辑申报人信息" if self.applicant_id else "新增申报人")
        title.setStyleSheet("font-size:15px; font-weight:bold; color:#1e293b;")
        lay.addWidget(title)

        line = QFrame(); line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color:#e2e8f0;")
        lay.addWidget(line)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.f_name      = QLineEdit(); self.f_name.setPlaceholderText("必填")
        self.f_id_card   = QLineEdit(); self.f_id_card.setPlaceholderText("18位身份证号")
        self.f_phone     = QLineEdit(); self.f_phone.setPlaceholderText("联系电话")
        self.f_email     = QLineEdit(); self.f_email.setPlaceholderText("电子邮箱（可选）")
        self.f_education = QComboBox(); self.f_education.addItems(EDUCATION_OPTIONS)
        self.f_major     = QLineEdit(); self.f_major.setPlaceholderText("所学专业")
        self.f_work_unit = QLineEdit(); self.f_work_unit.setPlaceholderText("工作单位全称")
        self.f_cur_level = QComboBox(); self.f_cur_level.addItems(LEVEL_OPTIONS)
        self.f_note      = QTextEdit(); self.f_note.setFixedHeight(72)
        self.f_note.setPlaceholderText("备注（可选）")

        form.addRow("姓名 *",     self.f_name)
        form.addRow("身份证号",   self.f_id_card)
        form.addRow("联系电话",   self.f_phone)
        form.addRow("电子邮箱",   self.f_email)
        form.addRow("学历",       self.f_education)
        form.addRow("所学专业",   self.f_major)
        form.addRow("工作单位",   self.f_work_unit)
        form.addRow("现有职称",   self.f_cur_level)
        form.addRow("备注",       self.f_note)

        lay.addLayout(form)

        # buttons
        btns = QHBoxLayout()
        btns.addStretch()
        cancel = QPushButton("取消"); cancel.setObjectName("btnOutline")
        save   = QPushButton("保存"); save.setObjectName("btnPrimary")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._save)
        btns.addWidget(cancel)
        btns.addWidget(save)
        lay.addLayout(btns)

    def _load(self, aid):
        data = get_applicant(aid)
        if not data:
            return
        self.f_name.setText(data.get("name", ""))
        self.f_id_card.setText(data.get("id_card", "") or "")
        self.f_phone.setText(data.get("phone", "") or "")
        self.f_email.setText(data.get("email", "") or "")
        self.f_major.setText(data.get("major", "") or "")
        self.f_work_unit.setText(data.get("work_unit", "") or "")
        self.f_note.setPlainText(data.get("note", "") or "")

        edu = data.get("education", "")
        idx = self.f_education.findText(edu)
        if idx >= 0: self.f_education.setCurrentIndex(idx)

        lvl = data.get("current_level", "")
        idx = self.f_cur_level.findText(lvl)
        if idx >= 0: self.f_cur_level.setCurrentIndex(idx)

    def _save(self):
        name = self.f_name.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "姓名不能为空")
            return

        kwargs = dict(
            name          = name,
            id_card       = self.f_id_card.text().strip() or None,
            phone         = self.f_phone.text().strip() or None,
            email         = self.f_email.text().strip() or None,
            education     = self.f_education.currentText(),
            major         = self.f_major.text().strip() or None,
            work_unit     = self.f_work_unit.text().strip() or None,
            current_level = self.f_cur_level.currentText(),
            note          = self.f_note.toPlainText().strip() or None,
        )

        if self.applicant_id:
            update_applicant(self.applicant_id, **kwargs)
        else:
            insert_applicant(**kwargs)

        self.accept()
