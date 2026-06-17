"""新增 / 编辑申报项目对话框"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QTextEdit,
    QPushButton, QMessageBox, QFrame, QDoubleSpinBox,
    QDateEdit, QGroupBox
)
from PyQt5.QtCore import Qt, QDate
from database.models import (
    insert_project, update_project, get_project,
    list_applicants, list_batches, upsert_fee, get_fee
)

INDUSTRY_COMMITTEE = {
    "建筑工程": ["广西建筑工程系列评委会", "广西市政公用评委会"],
    "市政公用": ["广西市政公用评委会", "广西建筑工程系列评委会"],
    "装饰装修": ["广西建筑工程系列评委会"],
    "机电安装": ["广西建筑工程系列评委会"],
    "公路工程": ["广西公路工程系列评委会"],
    "教育":     ["广西中小学教师系列评委会", "广西高校教师系列评委会"],
}
ALL_INDUSTRIES = list(INDUSTRY_COMMITTEE.keys())
APPLY_LEVELS   = ["中级工程师", "高级工程师", "正高级工程师", "中学一级", "中学高级"]


class ProjectDialog(QDialog):
    def __init__(self, project_id=None, applicant_id=None, parent=None):
        super().__init__(parent)
        self.project_id   = project_id
        self.applicant_id = applicant_id
        self.setWindowTitle("编辑申报项目" if project_id else "新增申报项目")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._build_ui()
        if project_id:
            self._load(project_id)

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        title = QLabel("编辑申报项目" if self.project_id else "新增申报项目")
        title.setStyleSheet("font-size:15px; font-weight:bold; color:#1e293b;")
        lay.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet("color:#e2e8f0;")
        lay.addWidget(sep)

        # ── 基本信息 ──────────────────────────────────────────────
        form = QFormLayout(); form.setSpacing(10); form.setLabelAlignment(Qt.AlignRight)

        # 申报人（新增时可选，编辑时锁定）
        self.f_applicant = QComboBox()
        self._applicants = list_applicants()
        self.f_applicant.addItem("-- 选择申报人 --", None)
        for a in self._applicants:
            self.f_applicant.addItem(a["name"], a["id"])
        if self.applicant_id:
            for i, a in enumerate(self._applicants):
                if a["id"] == self.applicant_id:
                    self.f_applicant.setCurrentIndex(i + 1)
                    break
            self.f_applicant.setEnabled(self.project_id is None)

        # 批次
        self.f_batch = QComboBox()
        self.f_batch.addItem("-- 暂不关联批次 --", None)
        self._batches = list_batches()
        for b in self._batches:
            label = f"{b['year']}年 {b['industry']} {b['committee']} {b['level']}"
            self.f_batch.addItem(label, b["id"])

        # 行业 → 评委会联动
        self.f_industry = QComboBox()
        self.f_industry.addItems(ALL_INDUSTRIES)
        self.f_industry.currentTextChanged.connect(self._on_industry_changed)

        self.f_committee = QComboBox()
        self._on_industry_changed(self.f_industry.currentText())

        self.f_level       = QComboBox(); self.f_level.addItems(APPLY_LEVELS)
        self.f_proj_name   = QLineEdit(); self.f_proj_name.setPlaceholderText("代表作项目名称（可选）")
        self.f_folder      = QLineEdit(); self.f_folder.setPlaceholderText("材料文件夹路径（可选）")
        self.f_note        = QTextEdit(); self.f_note.setFixedHeight(60)

        form.addRow("申报人 *",   self.f_applicant)
        form.addRow("关联批次",   self.f_batch)
        form.addRow("申报行业 *", self.f_industry)
        form.addRow("评委会 *",   self.f_committee)
        form.addRow("申报级别 *", self.f_level)
        form.addRow("代表项目名", self.f_proj_name)
        form.addRow("材料文件夹", self.f_folder)
        form.addRow("备注",       self.f_note)
        lay.addLayout(form)

        # ── 费用信息 ──────────────────────────────────────────────
        fee_box = QGroupBox("费用信息")
        fee_box.setStyleSheet(
            "QGroupBox { font-weight:bold; color:#1e293b; border:1px solid #e2e8f0;"
            "border-radius:6px; margin-top:8px; padding-top:8px; }"
            "QGroupBox::title { subcontrol-origin:margin; left:10px; }"
        )
        fee_form = QFormLayout(fee_box); fee_form.setSpacing(8); fee_form.setLabelAlignment(Qt.AlignRight)

        def spin():
            s = QDoubleSpinBox()
            s.setRange(0, 99999); s.setDecimals(0); s.setSuffix(" 元")
            return s

        self.f_total   = spin()
        self.f_deposit = spin()
        self.f_paid    = spin()
        self.f_paid_date = QDateEdit(QDate.currentDate()); self.f_paid_date.setCalendarPopup(True)
        self.f_fee_note  = QLineEdit()

        fee_form.addRow("总费用",   self.f_total)
        fee_form.addRow("定金",     self.f_deposit)
        fee_form.addRow("已付金额", self.f_paid)
        fee_form.addRow("付款日期", self.f_paid_date)
        fee_form.addRow("费用备注", self.f_fee_note)
        lay.addWidget(fee_box)

        # buttons
        btns = QHBoxLayout(); btns.addStretch()
        cancel = QPushButton("取消"); cancel.setObjectName("btnOutline")
        save   = QPushButton("保存"); save.setObjectName("btnPrimary")
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save)
        lay.addLayout(btns)

    def _on_industry_changed(self, industry):
        self.f_committee.clear()
        committees = INDUSTRY_COMMITTEE.get(industry, [])
        self.f_committee.addItems(committees)

    def _load(self, pid):
        p = get_project(pid)
        if not p: return

        # applicant
        for i, a in enumerate(self._applicants):
            if a["id"] == p.get("applicant_id"):
                self.f_applicant.setCurrentIndex(i + 1); break

        # batch
        for i, b in enumerate(self._batches):
            if b["id"] == p.get("batch_id"):
                self.f_batch.setCurrentIndex(i + 1); break

        # industry / committee
        ind = p.get("industry", "")
        idx = self.f_industry.findText(ind)
        if idx >= 0: self.f_industry.setCurrentIndex(idx)
        com = p.get("committee", "")
        idx = self.f_committee.findText(com)
        if idx >= 0: self.f_committee.setCurrentIndex(idx)

        lvl = p.get("apply_level", "")
        idx = self.f_level.findText(lvl)
        if idx >= 0: self.f_level.setCurrentIndex(idx)

        self.f_proj_name.setText(p.get("project_name") or "")
        self.f_folder.setText(p.get("folder_path") or "")
        self.f_note.setPlainText(p.get("note") or "")

        # fee
        fee = get_fee(pid)
        if fee:
            self.f_total.setValue(fee.get("total") or 0)
            self.f_deposit.setValue(fee.get("deposit") or 0)
            self.f_paid.setValue(fee.get("paid") or 0)
            pd = fee.get("paid_date") or ""
            if pd:
                self.f_paid_date.setDate(QDate.fromString(pd, "yyyy-MM-dd"))
            self.f_fee_note.setText(fee.get("note") or "")

    def _save(self):
        applicant_id = self.f_applicant.currentData()
        if not applicant_id:
            QMessageBox.warning(self, "提示", "请选择申报人")
            return
        industry  = self.f_industry.currentText()
        committee = self.f_committee.currentText()
        level     = self.f_level.currentText()

        kwargs = dict(
            applicant_id  = applicant_id,
            batch_id      = self.f_batch.currentData(),
            industry      = industry,
            committee     = committee,
            apply_level   = level,
            project_name  = self.f_proj_name.text().strip() or None,
            folder_path   = self.f_folder.text().strip() or None,
            note          = self.f_note.toPlainText().strip() or None,
        )

        if self.project_id:
            update_project(self.project_id, **kwargs)
            pid = self.project_id
        else:
            pid = insert_project(**kwargs)

        # save fee
        upsert_fee(
            project_id = pid,
            total      = self.f_total.value(),
            deposit    = self.f_deposit.value(),
            paid       = self.f_paid.value(),
            paid_date  = self.f_paid_date.date().toString("yyyy-MM-dd"),
            note       = self.f_fee_note.text().strip(),
        )
        self.accept()
