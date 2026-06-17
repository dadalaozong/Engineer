"""图像处理页 — 本地增强 + 第三方API（去背景/超分/阿里云）。"""
from __future__ import annotations
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFileDialog, QMessageBox, QProgressBar,
    QFrame, QSplitter, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
from config import load_config
from core.crypto import decrypt
from gui.widgets import SectionTitle


OPERATIONS = {
    "enhance_scan":       ("扫描件增强（本地·免费）",   False),
    "deskew":             ("自动纠偏（本地·免费）",      False),
    "remove_background":  ("去除背景 — remove.bg",       True),
    "upscale_image":      ("超分辨率放大 — Clipdrop",    True),
    "aliyun_enhance":     ("图像增强 — 阿里云",          True),
}


class ProcWorker(QThread):
    finished = pyqtSignal(str)   # output path
    error    = pyqtSignal(str)

    def __init__(self, op: str, input_path: str, api_key: str):
        super().__init__()
        self.op         = op
        self.input_path = input_path
        self.api_key    = api_key

    def run(self):
        try:
            import core.img_processor as proc
            fn = getattr(proc, self.op)
            if self.api_key:
                out = fn(self.input_path, self.api_key)
            else:
                out = fn(self.input_path)
            self.finished.emit(out)
        except Exception as e:
            self.error.emit(str(e))


class ImgProcPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._input_path  = None
        self._output_path = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)
        root.addWidget(SectionTitle("图像处理"))

        # ── 操作选择 ──────────────────────────────────────────────
        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("处理操作："))
        self._cmb_op = QComboBox()
        self._cmb_op.setMinimumWidth(280)
        for key, (label, _) in OPERATIONS.items():
            self._cmb_op.addItem(label, key)
        self._cmb_op.currentIndexChanged.connect(self._on_op_changed)
        op_row.addWidget(self._cmb_op)
        op_row.addStretch()

        btn_select = QPushButton("📂 选择图片")
        btn_select.setObjectName("btnOutline")
        btn_select.clicked.connect(self._select_input)

        self._btn_run = QPushButton("▶ 开始处理")
        self._btn_run.setObjectName("btnPrimary")
        self._btn_run.setEnabled(False)
        self._btn_run.clicked.connect(self._run)

        op_row.addWidget(btn_select)
        op_row.addWidget(self._btn_run)
        root.addLayout(op_row)

        # API Key 提示
        self._api_hint = QLabel()
        self._api_hint.setStyleSheet(
            "background:#fef9c3;color:#854d0e;border-radius:6px;padding:6px 12px;font-size:12px;"
        )
        self._api_hint.setVisible(False)
        root.addWidget(self._api_hint)

        # 进度条
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setFixedHeight(6)
        self._progress.setVisible(False)
        self._progress.setStyleSheet(
            "QProgressBar{background:#e2e8f0;border-radius:3px;}"
            "QProgressBar::chunk{background:#2563eb;border-radius:3px;}"
        )
        root.addWidget(self._progress)

        # ── 图片预览对比 ──────────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)

        self._before = self._preview_panel("处理前")
        self._after  = self._preview_panel("处理后")
        splitter.addWidget(self._before[0])
        splitter.addWidget(self._after[0])
        root.addWidget(splitter)

        # 操作按钮行
        action_row = QHBoxLayout()
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color:#64748b; font-size:12px;")
        action_row.addWidget(self._status_label)
        action_row.addStretch()

        self._btn_save = QPushButton("💾 另存为…")
        self._btn_save.setObjectName("btnOutline")
        self._btn_save.setEnabled(False)
        self._btn_save.clicked.connect(self._save_output)
        action_row.addWidget(self._btn_save)
        root.addLayout(action_row)

        self._on_op_changed(0)

    def _preview_panel(self, title: str):
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(8, 8, 8, 8)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-weight:bold;color:#1e293b;font-size:12px;")
        img_lbl = QLabel("尚未加载图片")
        img_lbl.setAlignment(Qt.AlignCenter)
        img_lbl.setMinimumHeight(320)
        img_lbl.setStyleSheet("color:#94a3b8;")
        lay.addWidget(lbl_title)
        lay.addWidget(img_lbl)
        return frame, img_lbl

    # ── events ────────────────────────────────────────────────────
    def refresh(self):
        pass

    def _on_op_changed(self, _):
        key = self._cmb_op.currentData()
        needs_api = OPERATIONS.get(key, (None, False))[1]
        if needs_api:
            cfg    = load_config()
            key_map = {
                "remove_background": ("img_apis", "remove_bg_key",  "remove.bg"),
                "upscale_image":     ("img_apis", "clipdrop_key",   "Clipdrop"),
                "aliyun_enhance":    ("img_apis", "aliyun_key",     "阿里云"),
            }
            section, cfg_key, name = key_map.get(key, ("img_apis", "", "未知"))
            api_val = decrypt(cfg.get(section, {}).get(cfg_key, ""))
            if not api_val:
                self._api_hint.setText(
                    f"⚠ 需要 {name} API Key，请前往「系统设置 → 图像处理 API」配置。"
                )
                self._api_hint.setVisible(True)
            else:
                self._api_hint.setVisible(False)
        else:
            self._api_hint.setVisible(False)

    def _select_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
        )
        if not path: return
        self._input_path = path
        self._btn_run.setEnabled(True)
        self._output_path = None
        self._btn_save.setEnabled(False)
        self._show_image(self._before[1], path)
        self._after[1].setText("处理后预览")
        self._status_label.setText(f"已选择：{Path(path).name}")

    def _run(self):
        if not self._input_path: return
        op  = self._cmb_op.currentData()
        cfg = load_config()
        key_map = {
            "remove_background": ("img_apis", "remove_bg_key"),
            "upscale_image":     ("img_apis", "clipdrop_key"),
            "aliyun_enhance":    ("img_apis", "aliyun_key"),
        }
        api_key = ""
        if op in key_map:
            sec, ckey = key_map[op]
            api_key = decrypt(cfg.get(sec, {}).get(ckey, ""))

        self._btn_run.setEnabled(False)
        self._progress.setVisible(True)
        self._status_label.setText("处理中，请稍候…")
        QApplication.processEvents()

        self._worker = ProcWorker(op, self._input_path, api_key)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, output_path: str):
        self._output_path = output_path
        self._progress.setVisible(False)
        self._btn_run.setEnabled(True)
        self._btn_save.setEnabled(True)
        self._show_image(self._after[1], output_path)
        self._status_label.setText(f"✅ 处理完成 → {Path(output_path).name}")

    def _on_error(self, msg: str):
        self._progress.setVisible(False)
        self._btn_run.setEnabled(True)
        self._status_label.setText("❌ 处理失败")
        QMessageBox.critical(self, "图像处理错误", msg)

    def _save_output(self):
        if not self._output_path: return
        src = Path(self._output_path)
        path, _ = QFileDialog.getSaveFileName(
            self, "另存为", src.name, f"图片 (*{src.suffix})"
        )
        if not path: return
        import shutil
        shutil.copy2(self._output_path, path)
        QMessageBox.information(self, "已保存", f"图片已保存至：\n{path}")

    @staticmethod
    def _show_image(label: QLabel, path: str):
        pix = QPixmap(path)
        if pix.isNull():
            label.setText(f"无法预览：{Path(path).name}")
        else:
            label.setPixmap(
                pix.scaled(label.width() or 480, 360,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
