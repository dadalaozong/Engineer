"""自动填报任务 — 驱动 BrowserManager 完成登录 + 表单填写全流程。"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from automation.browser import BrowserManager
from config import load_config
from core.crypto import decrypt


SITE_URL = "https://www.gxrczc.com"


@dataclass
class FillStep:
    name:    str
    success: bool
    message: str = ""


@dataclass
class FillReport:
    applicant_name: str
    project_id:     int
    started_at:     str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    steps:          list[FillStep] = field(default_factory=list)
    screenshot:     str = ""
    finished_at:    str = ""

    def add(self, name: str, success: bool, message: str = "") -> None:
        self.steps.append(FillStep(name, success, message))

    def finish(self):
        self.finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def success_count(self) -> int:
        return sum(1 for s in self.steps if s.success)

    @property
    def failed_steps(self) -> list[str]:
        return [s.name for s in self.steps if not s.success]

    def summary(self) -> str:
        lines = [
            f"申报人：{self.applicant_name}",
            f"开始时间：{self.started_at}",
            f"完成时间：{self.finished_at}",
            f"步骤完成：{self.success_count}/{len(self.steps)}",
        ]
        if self.failed_steps:
            lines.append(f"未完成步骤：{', '.join(self.failed_steps)}")
        if self.screenshot:
            lines.append(f"截图：{self.screenshot}")
        return "\n".join(lines)


class FormFiller:
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    def run(
        self,
        applicant: dict,
        project:   dict,
        log_callback=None,
    ) -> FillReport:
        """
        Execute full fill workflow.
        log_callback(step_name, success, message) is called after each step.
        """
        report = FillReport(
            applicant_name=applicant.get("name", ""),
            project_id=project.get("id", 0),
        )

        def step(name: str, success: bool, msg: str = ""):
            report.add(name, success, msg)
            if log_callback:
                log_callback(name, success, msg)

        cfg      = load_config()
        username = cfg["website"].get("username", "")
        password = decrypt(cfg["website"].get("password_cipher", ""))

        # ── Step 1: 浏览器已就绪 ──────────────────────────────────
        step("浏览器启动", self.browser.is_running)
        if not self.browser.is_running:
            report.finish()
            return report

        # ── Step 2: 登录 ──────────────────────────────────────────
        try:
            ok = self.browser.login(SITE_URL, username, password)
            step("登录网站", ok, "" if ok else "登录失败，请检查账号密码")
        except Exception as e:
            step("登录网站", False, str(e))
            report.finish()
            return report

        if not report.steps[-1].success:
            report.finish()
            return report

        # ── Step 3: 进入申报入口 ──────────────────────────────────
        try:
            # try to navigate to declaration entry
            for sel in [
                'a:has-text("申报")', 'a:has-text("职称申报")',
                '.apply-btn', '#applyEntry',
            ]:
                if self.browser.safe_click(sel, timeout=4_000):
                    break
            self.browser.page.wait_for_load_state("networkidle", timeout=10_000)
            step("进入申报入口", True)
        except Exception as e:
            step("进入申报入口", False, str(e))

        # ── Step 4: 选择行业和评委会 ──────────────────────────────
        try:
            from core.industries.construction import select_industry_and_committee
            results = select_industry_and_committee(
                self.browser.page,
                project.get("industry", ""),
                project.get("committee", ""),
            )
            ok = any(results.values())
            step("选择行业/评委会", ok,
                 f"行业:{results.get('select_industry')}, 评委会:{results.get('select_committee')}")
        except Exception as e:
            step("选择行业/评委会", False, str(e))

        # ── Step 5: 填写基本信息 ──────────────────────────────────
        try:
            from core.industries.construction import fill_basic_info
            results = fill_basic_info(self.browser.page, applicant, project)
            filled = sum(1 for v in results.values() if v)
            total  = len(results)
            step("填写基本信息", filled > 0,
                 f"成功填写 {filled}/{total} 个字段: {list(results.keys())}")
        except Exception as e:
            step("填写基本信息", False, str(e))

        # ── Step 6: 截图存档 ──────────────────────────────────────
        try:
            from config import DATA_DIR
            screenshots_dir = DATA_DIR / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = applicant.get("name", "unknown").replace(" ", "_")
            path = str(screenshots_dir / f"{name}_{ts}.png")
            self.browser.screenshot(path)
            report.screenshot = path
            step("截图存档", True, path)
        except Exception as e:
            step("截图存档", False, str(e))

        # ── Step 7: 提交表单（可选，默认不自动提交）────────────────
        # 设计上要求人工确认后再提交，此处仅记录步骤
        step("等待人工确认提交", True,
             "自动填写完成，请在浏览器中人工核对后手动点击提交")

        report.finish()
        return report
