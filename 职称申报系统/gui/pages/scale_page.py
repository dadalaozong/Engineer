"""工程规模判断页 — 实时计算，结果可写回项目记录。"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QFrame, QScrollArea, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from core.scale_engine import SPECIALTY_NAMES, get_specialty, judge, JudgeResult
from database.models import list_applicants, list_projects, update_project
from gui.widgets import SectionTitle


class ScalePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._spins: dict[str, QDoubleSpinBox] = {}
        self._projects = []
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        root.addWidget(SectionTitle("工程规模判断引擎"))

        # ── 专业选择 ──────────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("专业类别："))
        self._cmb_specialty = QComboBox()
        self._cmb_specialty.addItems(SPECIALTY_NAMES)
        self._cmb_specialty.setMinimumWidth(180)
        self._cmb_specialty.currentTextChanged.connect(self._rebuild_indicators)
        top_row.addWidget(self._cmb_specialty)
        top_row.addSpacing(20)

        top_row.addWidget(QLabel("项目名称（可选）："))
        self._cmb_project = QComboBox()
        self._cmb_project.setMinimumWidth(260)
        self._cmb_project.addItem("-- 不关联项目 --", None)
        top_row.addWidget(self._cmb_project)
        top_row.addStretch()

        btn_judge = QPushButton("⚖ 立即判断")
        btn_judge.setObjectName("btnPrimary")
        btn_judge.setFixedHeight(36)
        btn_judge.clicked.connect(self._do_judge)
        top_row.addWidget(btn_judge)

        root.addLayout(top_row)

        # ── 专业说明 ──────────────────────────────────────────────
        self._desc_label = QLabel()
        self._desc_label.setStyleSheet("color:#64748b; font-size:12px;")
        root.addWidget(self._desc_label)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#e2e8f0;"); root.addWidget(sep)

        # ── 指标输入区 ────────────────────────────────────────────
        content_row = QHBoxLayout()
        content_row.setSpacing(20)

        # indicators form
        self._ind_box = QGroupBox("填写工程指标（未知项填 0）")
        self._ind_box.setStyleSheet(
            "QGroupBox{font-weight:bold;color:#1e293b;border:1px solid #e2e8f0;"
            "border-radius:8px;margin-top:6px;padding-top:10px;}"
            "QGroupBox::title{subcontrol-origin:margin;left:12px;}"
        )
        self._ind_form = QFormLayout(self._ind_box)
        self._ind_form.setSpacing(10)
        self._ind_form.setLabelAlignment(Qt.AlignRight)
        content_row.addWidget(self._ind_box, 1)

        # result panel
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        # result card
        self._result_card = QFrame()
        self._result_card.setStyleSheet(
            "QFrame{background:#f8fafc;border:2px solid #e2e8f0;border-radius:10px;padding:4px;}"
        )
        self._result_card.setMinimumWidth(260)
        rc_lay = QVBoxLayout(self._result_card)
        rc_lay.setContentsMargins(20, 16, 20, 16)
        rc_lay.setSpacing(8)

        self._result_label = QLabel("—")
        f = QFont(); f.setPointSize(32); f.setBold(True)
        self._result_label.setFont(f)
        self._result_label.setAlignment(Qt.AlignCenter)

        self._result_sub = QLabel("请填写指标后点击判断")
        self._result_sub.setAlignment(Qt.AlignCenter)
        self._result_sub.setStyleSheet("color:#64748b; font-size:12px;")
        self._result_sub.setWordWrap(True)

        rc_lay.addWidget(self._result_label)
        rc_lay.addWidget(self._result_sub)
        right_col.addWidget(self._result_card)

        # detail text
        self._detail_edit = QTextEdit()
        self._detail_edit.setReadOnly(True)
        self._detail_edit.setPlaceholderText("判断依据将显示在此处…")
        self._detail_edit.setMinimumHeight(120)
        right_col.addWidget(self._detail_edit)

        # write-back button
        self._btn_writeback = QPushButton("📝 写回到关联项目")
        self._btn_writeback.setObjectName("btnOutline")
        self._btn_writeback.setEnabled(False)
        self._btn_writeback.clicked.connect(self._write_back)
        right_col.addWidget(self._btn_writeback)

        right_col.addStretch()
        content_row.addLayout(right_col)
        root.addLayout(content_row)

        # ── rules reference table ─────────────────────────────────
        root.addWidget(SectionTitle("评定标准参考"))
        self._rules_label = QLabel()
        self._rules_label.setWordWrap(True)
        self._rules_label.setStyleSheet(
            "background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;"
            "padding:12px 16px;color:#334155;font-size:12px;line-height:1.6;"
        )
        root.addWidget(self._rules_label)
        root.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll)

        self._last_result: JudgeResult | None = None
        self._rebuild_indicators(self._cmb_specialty.currentText())

    # ── build indicator inputs for selected specialty ──────────────
    def _rebuild_indicators(self, specialty_name: str):
        sp = get_specialty(specialty_name)
        if not sp:
            return

        self._desc_label.setText(sp.description)

        # clear old spins
        while self._ind_form.rowCount():
            self._ind_form.removeRow(0)
        self._spins.clear()

        # collect unique indicators across all levels
        seen = []
        for level in sp.levels:
            for rule in level.rules:
                if rule.indicator not in seen:
                    seen.append(rule.indicator)

        for ind_name in seen:
            # find unit from any rule
            unit = next(
                r.unit for lv in sp.levels for r in lv.rules if r.indicator == ind_name
            )
            spin = QDoubleSpinBox()
            spin.setRange(0, 9_999_999)
            spin.setDecimals(2)
            spin.setSuffix(f"  {unit}")
            spin.setValue(0)
            spin.setMinimumWidth(180)
            self._spins[ind_name] = spin
            self._ind_form.addRow(f"{ind_name}：", spin)

        # rebuild rules reference
        self._rebuild_rules_label(sp)
        self._last_result = None
        self._btn_writeback.setEnabled(False)
        self._result_label.setText("—")
        self._result_label.setStyleSheet("color:#1e293b;")
        self._result_sub.setText("请填写指标后点击判断")
        self._result_card.setStyleSheet(
            "QFrame{background:#f8fafc;border:2px solid #e2e8f0;border-radius:10px;padding:4px;}"
        )
        self._detail_edit.clear()

    def _rebuild_rules_label(self, sp):
        lines = []
        for level in sp.levels[:-1]:
            rules_text = "  |  ".join(
                f"{r.indicator} ≥ {r.value:g} {r.unit}" for r in level.rules
            )
            lines.append(f"【{level.name}】满足任一条件：{rules_text}")
        lines.append(f"【{sp.levels[-1].name}】以上均不满足")
        self._rules_label.setText("\n".join(lines))

    # ── judge ──────────────────────────────────────────────────────
    def _do_judge(self):
        specialty = self._cmb_specialty.currentText()
        indicators = {name: spin.value() for name, spin in self._spins.items()}
        result = judge(specialty, indicators)
        self._last_result = result

        self._result_label.setText(result.scale)
        self._result_label.setStyleSheet(f"color:{result.color};")
        self._result_sub.setText(f"{specialty}")
        self._result_card.setStyleSheet(
            f"QFrame{{background:#fff;border:3px solid {result.color};"
            f"border-radius:10px;padding:4px;}}"
        )
        self._detail_edit.setPlainText(result.detail)
        self._btn_writeback.setEnabled(self._cmb_project.currentData() is not None)

    def _write_back(self):
        if not self._last_result:
            return
        pid = self._cmb_project.currentData()
        if not pid:
            QMessageBox.warning(self, "提示", "请先选择关联项目")
            return
        update_project(pid, scale=self._last_result.scale)
        QMessageBox.information(
            self, "已保存",
            f"工程规模「{self._last_result.scale}」已写回到关联项目"
        )

    # ── data refresh ──────────────────────────────────────────────
    def refresh(self):
        self._cmb_project.clear()
        self._cmb_project.addItem("-- 不关联项目 --", None)
        for p in list_projects():
            label = (
                f"{p.get('applicant_name','')} · "
                f"{p.get('apply_level','')} · "
                f"{p.get('industry','')}"
            )
            self._cmb_project.addItem(label, p["id"])
