"""OCR 识别页 — 选图 → 识别 → 结构化字段 → 一键回填申报人信息"""
from __future__ import annotations
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTextEdit, QComboBox, QGroupBox,
    QFormLayout, QLineEdit, QScrollArea, QFrame,
    QMessageBox, QSplitter, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QColor
from gui.widgets import SectionTitle
from database.models import list_applicants, update_applicant


DOC_TYPES = ["身份证", "毕业证/学位证", "职称证书"]


class OcrWorker(QThread):
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path

    def run(self):
        try:
            from core.ocr_reader import recognize
            text = recognize(self.image_path)
            self.finished.emit(text)
        except Exception as e:
            self.error.emit(str(e))


class OcrPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image_path = None
        self._raw_text   = ""
        self._parsed     = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)
        root.addWidget(SectionTitle("证件 OCR 识别"))

        splitter = QSplitter(Qt.Horizontal)

        # ── 左侧：图片选择 + 预览 ─────────────────────────────────
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 8, 0)
        left_lay.setSpacing(10)

        # doc type
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("证件类型："))
        self._cmb_type = QComboBox()
        self._cmb_type.addItems(DOC_TYPES)
        type_row.addWidget(self._cmb_type)
        type_row.addStretch()
        left_lay.addLayout(type_row)

        # image preview
        self._img_label = QLabel("点击下方按钮选择图片")
        self._img_label.setAlignment(Qt.AlignCenter)
        self._img_label.setMinimumHeight(280)
        self._img_label.setStyleSheet(
            "background:#f8fafc; border:2px dashed #cbd5e1; border-radius:8px; color:#94a3b8;"
        )
        left_lay.addWidget(self._img_label)

        btn_row = QHBoxLayout()
        btn_select = QPushButton("📂 选择图片")
        btn_select.setObjectName("btnOutline")
        btn_select.clicked.connect(self._select_image)
        self._btn_ocr = QPushButton("🔍 开始识别")
        self._btn_ocr.setObjectName("btnPrimary")
        self._btn_ocr.setEnabled(False)
        self._btn_ocr.clicked.connect(self._run_ocr)
        btn_row.addWidget(btn_select)
        btn_row.addWidget(self._btn_ocr)
        left_lay.addLayout(btn_row)

        self._ocr_status = QLabel("")
        self._ocr_status.setStyleSheet("color:#64748b; font-size:12px;")
        left_lay.addWidget(self._ocr_status)

        # raw text output
        left_lay.addWidget(QLabel("识别原始文本："))
        self._raw_edit = QTextEdit()
        self._raw_edit.setReadOnly(True)
        self._raw_edit.setPlaceholderText("识别结果将显示在此处…")
        self._raw_edit.setMinimumHeight(120)
        left_lay.addWidget(self._raw_edit)

        splitter.addWidget(left)

        # ── 右侧：结构化字段 + 回填 ───────────────────────────────
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(8, 0, 0, 0)
        right_lay.setSpacing(10)

        right_lay.addWidget(QLabel("识别结果（可手动修正）："))

        self._fields: dict[str, QLineEdit] = {}
        field_box = QGroupBox()
        field_box.setStyleSheet(
            "QGroupBox{border:1px solid #e2e8f0;border-radius:8px;padding:8px;}"
        )
        field_form = QFormLayout(field_box)
        field_form.setSpacing(8)
        field_form.setLabelAlignment(Qt.AlignRight)

        for key, label in [
            ("name",          "姓名"),
            ("id_card",       "身份证号"),
            ("gender",        "性别"),
            ("birth_date",    "出生日期"),
            ("education",     "学历"),
            ("major",         "所学专业"),
            ("school",        "毕业院校"),
            ("grad_year",     "毕业年份"),
            ("current_level", "现有职称"),
        ]:
            le = QLineEdit()
            self._fields[key] = le
            field_form.addRow(label + "：", le)

        right_lay.addWidget(field_box)

        # 回填到申报人
        fill_box = QGroupBox("回填到申报人")
        fill_box.setStyleSheet(
            "QGroupBox{font-weight:bold;color:#1e293b;border:1px solid #e2e8f0;"
            "border-radius:6px;margin-top:8px;padding-top:8px;}"
            "QGroupBox::title{subcontrol-origin:margin;left:10px;}"
        )
        fill_lay = QVBoxLayout(fill_box)
        fill_lay.setSpacing(8)

        ap_row = QHBoxLayout()
        ap_row.addWidget(QLabel("选择申报人："))
        self._cmb_applicant = QComboBox()
        self._cmb_applicant.setMinimumWidth(180)
        ap_row.addWidget(self._cmb_applicant)
        ap_row.addStretch()
        fill_lay.addLayout(ap_row)

        btn_fill = QPushButton("一键回填到选中申报人")
        btn_fill.setObjectName("btnPrimary")
        btn_fill.clicked.connect(self._fill_applicant)
        fill_lay.addWidget(btn_fill)

        right_lay.addWidget(fill_box)
        right_lay.addStretch()

        splitter.addWidget(right)
        splitter.setSizes([480, 400])
        root.addWidget(splitter)

    # ── operations ────────────────────────────────────────────────
    def refresh(self):
        self._cmb_applicant.clear()
        for a in list_applicants():
            self._cmb_applicant.addItem(a["name"], a["id"])

    def _select_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择证件图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
        )
        if not path:
            return
        self._image_path = path
        self._btn_ocr.setEnabled(True)
        pix = QPixmap(path)
        if not pix.isNull():
            self._img_label.setPixmap(
                pix.scaled(440, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self._img_label.setText(path.split("/")[-1])

    def _run_ocr(self):
        if not self._image_path:
            return
        from core.ocr_reader import is_available
        if not is_available():
            QMessageBox.warning(
                self, "PaddleOCR 未安装",
                "请先安装 PaddleOCR：\n\npip install paddlepaddle paddleocr\n\n安装后重启程序。"
            )
            return

        self._btn_ocr.setEnabled(False)
        self._ocr_status.setText("识别中，请稍候…")
        QApplication.processEvents()

        self._worker = OcrWorker(self._image_path)
        self._worker.finished.connect(self._on_ocr_done)
        self._worker.error.connect(self._on_ocr_error)
        self._worker.start()

    def _on_ocr_done(self, text: str):
        self._raw_text = text
        self._raw_edit.setPlainText(text)
        self._btn_ocr.setEnabled(True)
        self._ocr_status.setText("✅ 识别完成")

        # parse
        doc_type = self._cmb_type.currentText()
        from core.ocr_reader import parse_id_card, parse_degree_cert, parse_title_cert
        if doc_type == "身份证":
            self._parsed = parse_id_card(text)
        elif doc_type == "毕业证/学位证":
            self._parsed = parse_degree_cert(text)
        else:
            self._parsed = parse_title_cert(text)

        for key, le in self._fields.items():
            le.setText(self._parsed.get(key, ""))

    def _on_ocr_error(self, msg: str):
        self._btn_ocr.setEnabled(True)
        self._ocr_status.setText("❌ 识别失败")
        QMessageBox.critical(self, "OCR 错误", msg)

    def _fill_applicant(self):
        aid = self._cmb_applicant.currentData()
        if not aid:
            QMessageBox.warning(self, "提示", "请先选择申报人")
            return

        kwargs = {}
        field_map = {
            "name": "name", "id_card": "id_card",
            "education": "education", "major": "major",
            "current_level": "current_level",
        }
        for src, dst in field_map.items():
            val = self._fields[src].text().strip()
            if val:
                kwargs[dst] = val

        if not kwargs:
            QMessageBox.information(self, "提示", "没有可回填的字段")
            return

        update_applicant(aid, **kwargs)
        name = self._cmb_applicant.currentText()
        QMessageBox.information(self, "回填成功", f"已更新申报人「{name}」的信息")
