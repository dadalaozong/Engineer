"""费用汇总报表页"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QComboBox,
    QFrame, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from database.models import list_projects, get_fee, list_batches
from gui.widgets import SectionTitle
import csv, os


class FeesReportPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # ── toolbar ──────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.addWidget(SectionTitle("费用汇总报表"))
        toolbar.addStretch()

        self._cmb_batch = QComboBox()
        self._cmb_batch.setMinimumWidth(240)
        self._cmb_batch.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(QLabel("筛选批次："))
        toolbar.addWidget(self._cmb_batch)

        btn_export = QPushButton("导出 CSV")
        btn_export.setObjectName("btnOutline")
        btn_export.setFixedHeight(34)
        btn_export.clicked.connect(self._export_csv)
        toolbar.addSpacing(10)
        toolbar.addWidget(btn_export)
        root.addLayout(toolbar)

        # ── summary cards ─────────────────────────────────────────
        self._summary_row = QHBoxLayout()
        self._summary_row.setSpacing(14)
        self._s_total   = self._make_summary_card("应收总额", "¥0", "#2563eb")
        self._s_paid    = self._make_summary_card("已收金额", "¥0", "#16a34a")
        self._s_pending = self._make_summary_card("待收金额", "¥0", "#dc2626")
        self._s_rate    = self._make_summary_card("结清率",   "0%",  "#d97706")
        for card in [self._s_total, self._s_paid, self._s_pending, self._s_rate]:
            self._summary_row.addWidget(card[0])
        root.addLayout(self._summary_row)

        # ── table ─────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            ["申报人", "行业", "评委会", "级别", "总费用", "定金", "已付", "状态"]
        )
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("QTableWidget{alternate-background-color:#f8fafc;}")
        root.addWidget(self._table)

        self._status = QLabel()
        self._status.setStyleSheet("color:#64748b; font-size:12px;")
        root.addWidget(self._status)

    def _make_summary_card(self, label: str, value: str, color: str):
        card = QFrame()
        card.setStyleSheet(
            "QFrame{background:white;border:1px solid #e2e8f0;border-radius:8px;padding:4px;}"
        )
        lay = QVBoxLayout(card)
        lay.setSpacing(4); lay.setContentsMargins(16, 12, 16, 12)

        lbl = QLabel(label)
        lbl.setStyleSheet("color:#64748b; font-size:12px;")

        val = QLabel(value)
        f = val.font(); f.setPointSize(18); f.setBold(True); val.setFont(f)
        val.setStyleSheet(f"color:{color};")

        lay.addWidget(lbl); lay.addWidget(val)
        return card, val

    # ── data ──────────────────────────────────────────────────────
    def refresh(self):
        self._reload_batch_combo()
        self._load_table()

    def _reload_batch_combo(self):
        current_data = self._cmb_batch.currentData()
        self._cmb_batch.blockSignals(True)
        self._cmb_batch.clear()
        self._cmb_batch.addItem("全部批次", None)
        self._batches = list_batches()
        for b in self._batches:
            label = f"{b['year']}年 {b['industry']} {b['level']}"
            self._cmb_batch.addItem(label, b["id"])
        # restore selection
        if current_data:
            for i in range(self._cmb_batch.count()):
                if self._cmb_batch.itemData(i) == current_data:
                    self._cmb_batch.setCurrentIndex(i)
                    break
        self._cmb_batch.blockSignals(False)

    def _load_table(self):
        batch_id = self._cmb_batch.currentData()
        projects = list_projects(batch_id=batch_id)
        self._table_data = []

        for p in projects:
            fee = get_fee(p["id"])
            total   = (fee.get("total")   or 0) if fee else 0
            deposit = (fee.get("deposit") or 0) if fee else 0
            paid    = (fee.get("paid")    or 0) if fee else 0
            self._table_data.append({**p, "_total": total, "_deposit": deposit, "_paid": paid})

        self._table.setRowCount(len(self._table_data))
        sum_total = sum_paid = 0

        for i, r in enumerate(self._table_data):
            total   = r["_total"]
            deposit = r["_deposit"]
            paid    = r["_paid"]
            sum_total += total
            sum_paid  += paid

            status_text, fg, bg = self._fee_status(total, paid)

            self._table.setItem(i, 0, self._cell(r.get("applicant_name") or ""))
            self._table.setItem(i, 1, self._cell(r.get("industry") or ""))
            self._table.setItem(i, 2, self._cell(r.get("committee") or ""))
            self._table.setItem(i, 3, self._cell(r.get("apply_level") or ""))
            self._table.setItem(i, 4, self._money_cell(total))
            self._table.setItem(i, 5, self._money_cell(deposit))
            self._table.setItem(i, 6, self._money_cell(paid))

            status_item = self._cell(status_text)
            status_item.setForeground(QColor(fg))
            status_item.setBackground(QColor(bg))
            self._table.setItem(i, 7, status_item)

        self._table.resizeRowsToContents()

        # update summary cards
        sum_pending = sum_total - sum_paid
        rate = (sum_paid / sum_total * 100) if sum_total > 0 else 0
        cleared = sum(1 for r in self._table_data if r["_paid"] >= r["_total"] > 0)
        total_with_fee = sum(1 for r in self._table_data if r["_total"] > 0)

        self._s_total[1].setText(f"¥{sum_total:,.0f}")
        self._s_paid[1].setText(f"¥{sum_paid:,.0f}")
        self._s_pending[1].setText(f"¥{sum_pending:,.0f}")
        self._s_rate[1].setText(f"{rate:.1f}%")
        self._status.setText(
            f"共 {len(self._table_data)} 条记录  |  "
            f"已设置费用 {total_with_fee} 条  |  "
            f"已结清 {cleared} 条"
        )

    @staticmethod
    def _fee_status(total, paid):
        if total <= 0:
            return "未设置", "#6b7280", "#f3f4f6"
        if paid >= total:
            return "已结清", "#166534", "#dcfce7"
        if paid > 0:
            return "定金已付", "#854d0e", "#fef9c3"
        return "未付", "#991b1b", "#fee2e2"

    @staticmethod
    def _cell(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    @staticmethod
    def _money_cell(amount: float) -> QTableWidgetItem:
        text = f"¥{amount:,.0f}" if amount > 0 else "—"
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return item

    # ── export ────────────────────────────────────────────────────
    def _export_csv(self):
        if not self._table_data:
            QMessageBox.information(self, "提示", "暂无数据可导出")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出费用报表", "费用报表.csv", "CSV 文件 (*.csv)"
        )
        if not path: return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["申报人", "行业", "评委会", "级别", "总费用", "定金", "已付", "状态"])
                for r in self._table_data:
                    status, _, _ = self._fee_status(r["_total"], r["_paid"])
                    writer.writerow([
                        r.get("applicant_name", ""),
                        r.get("industry", ""),
                        r.get("committee", ""),
                        r.get("apply_level", ""),
                        r["_total"], r["_deposit"], r["_paid"],
                        status
                    ])
            QMessageBox.information(self, "导出成功", f"已保存至：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))
