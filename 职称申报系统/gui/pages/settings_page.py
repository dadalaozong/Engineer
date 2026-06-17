"""系统设置页 — API Key、网站账号、AI模型配置（加密存储）。"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFormLayout, QGroupBox, QComboBox,
    QTabWidget, QMessageBox, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt
from config import load_config, save_config
from core.crypto import encrypt, decrypt
from gui.widgets import SectionTitle


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)
        root.addWidget(SectionTitle("系统设置"))

        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabBar::tab{padding:8px 20px;font-size:13px;}"
            "QTabBar::tab:selected{color:#2563eb;border-bottom:2px solid #2563eb;}"
        )

        tabs.addTab(self._build_ai_tab(),    "AI 写作")
        tabs.addTab(self._build_img_tab(),   "图像处理 API")
        tabs.addTab(self._build_site_tab(),  "申报网站账号")

        root.addWidget(tabs)

        # save button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save = QPushButton("保存所有设置")
        btn_save.setObjectName("btnPrimary")
        btn_save.setFixedHeight(38)
        btn_save.setMinimumWidth(160)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    # ── AI Tab ────────────────────────────────────────────────────
    def _build_ai_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(14)

        info = QLabel(
            "DeepSeek API 与 OpenAI SDK 兼容。API Key 请在 platform.deepseek.com 获取。\n"
            "Key 使用 Fernet 对称加密后存储在本地，不会上传到任何服务器。"
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background:#dbeafe;color:#1e40af;border-radius:6px;padding:8px 12px;font-size:12px;"
        )
        lay.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self._f_deepseek_key = self._key_input("deepseek_api_key")
        self._f_model        = QComboBox()
        self._f_model.addItems(["deepseek-chat", "deepseek-coder", "deepseek-reasoner"])

        form.addRow("DeepSeek API Key：", self._f_deepseek_key)
        form.addRow("使用模型：",          self._f_model)

        btn_test = QPushButton("测试连接")
        btn_test.setObjectName("btnOutline")
        btn_test.clicked.connect(self._test_deepseek)
        form.addRow("", btn_test)

        lay.addLayout(form)
        lay.addStretch()
        return w

    # ── Image API Tab ──────────────────────────────────────────────
    def _build_img_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(14)

        rows = [
            ("remove.bg API Key：",  "_f_removebg",   "remove_bg_key",
             "https://www.remove.bg/dashboard#api-key  — 免费额度50次/月，去除图片背景"),
            ("Clipdrop API Key：",   "_f_clipdrop",   "clipdrop_key",
             "https://clipdrop.co/apis  — 超分辨率放大，图片修复"),
            ("阿里云 AppCode：",     "_f_aliyun",     "aliyun_key",
             "阿里云市场 → 图像增强 API  — 老照片修复、超清画质"),
            ("腾讯云 SecretKey：",   "_f_tencent",    "tencent_key",
             "腾讯云图像处理 API  — 备用方案"),
        ]

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        for label, attr, cfg_key, hint in rows:
            inp = self._key_input(cfg_key, section="img_apis")
            setattr(self, attr, inp)

            hint_lbl = QLabel(hint)
            hint_lbl.setStyleSheet("color:#64748b;font-size:11px;")
            hint_lbl.setWordWrap(True)

            form.addRow(label, inp)
            form.addRow("", hint_lbl)

        lay.addLayout(form)
        lay.addStretch()
        return w

    # ── Site Tab ──────────────────────────────────────────────────
    def _build_site_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(14)

        info = QLabel(
            "申报网站：https://www.gxrczc.com\n"
            "账号密码用于自动填报模块（P7），密码加密存储。"
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background:#f0fdf4;color:#166534;border-radius:6px;padding:8px 12px;font-size:12px;"
        )
        lay.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self._f_site_user = QLineEdit()
        self._f_site_user.setPlaceholderText("登录用户名")

        self._f_site_pass = QLineEdit()
        self._f_site_pass.setEchoMode(QLineEdit.Password)
        self._f_site_pass.setPlaceholderText("登录密码（加密存储）")

        form.addRow("用户名：", self._f_site_user)
        form.addRow("密码：",   self._f_site_pass)
        lay.addLayout(form)
        lay.addStretch()
        return w

    # ── helpers ───────────────────────────────────────────────────
    def _key_input(self, cfg_key: str, section: str = "ai") -> QLineEdit:
        le = QLineEdit()
        le.setEchoMode(QLineEdit.Password)
        le.setPlaceholderText("粘贴 API Key（输入后加密保存）")
        le.setProperty("cfg_key",  cfg_key)
        le.setProperty("cfg_section", section)
        return le

    def refresh(self):
        cfg = load_config()
        # AI tab
        raw = decrypt(cfg["ai"].get("deepseek_api_key", ""))
        self._f_deepseek_key.setText(raw)
        model = cfg["ai"].get("model", "deepseek-chat")
        idx = self._f_model.findText(model)
        if idx >= 0: self._f_model.setCurrentIndex(idx)

        # img tab
        img = cfg.get("img_apis", {})
        self._f_removebg.setText(decrypt(img.get("remove_bg_key", "")))
        self._f_clipdrop.setText(decrypt(img.get("clipdrop_key", "")))
        self._f_aliyun.setText(decrypt(img.get("aliyun_key", "")))
        self._f_tencent.setText(decrypt(img.get("tencent_key", "")))

        # site tab
        site = cfg.get("website", {})
        self._f_site_user.setText(site.get("username", ""))
        self._f_site_pass.setText(decrypt(site.get("password_cipher", "")))

    def _save(self):
        cfg = load_config()

        cfg["ai"]["deepseek_api_key"] = encrypt(self._f_deepseek_key.text().strip())
        cfg["ai"]["model"]            = self._f_model.currentText()

        cfg["img_apis"]["remove_bg_key"] = encrypt(self._f_removebg.text().strip())
        cfg["img_apis"]["clipdrop_key"]  = encrypt(self._f_clipdrop.text().strip())
        cfg["img_apis"]["aliyun_key"]    = encrypt(self._f_aliyun.text().strip())
        cfg["img_apis"]["tencent_key"]   = encrypt(self._f_tencent.text().strip())

        cfg["website"]["username"]        = self._f_site_user.text().strip()
        cfg["website"]["password_cipher"] = encrypt(self._f_site_pass.text())

        save_config(cfg)
        QMessageBox.information(self, "已保存", "设置已保存（API Key 加密存储）")

    def _test_deepseek(self):
        raw = self._f_deepseek_key.text().strip()
        if not raw:
            QMessageBox.warning(self, "提示", "请先填写 DeepSeek API Key"); return
        try:
            from openai import OpenAI
            client = OpenAI(api_key=raw, base_url="https://api.deepseek.com")
            resp = client.chat.completions.create(
                model=self._f_model.currentText(),
                messages=[{"role": "user", "content": "你好，回复连接成功三个字即可。"}],
                max_tokens=10,
            )
            reply = resp.choices[0].message.content or ""
            QMessageBox.information(self, "连接成功", f"DeepSeek 响应：{reply}")
        except Exception as e:
            QMessageBox.critical(self, "连接失败", str(e))
