"""自动填报任务 — 驱动 BrowserManager 完成登录 + 表单填写全流程。
SSE流式日志输出，供 routes/auto_fill.py 使用。
"""
from __future__ import annotations
import json
from datetime import datetime
from automation.browser import BrowserManager


SITE_URL = "https://my.gxrczc.com/Login"


def _emit(msg: str, level: str = "info") -> str:
    return json.dumps({"level": level, "msg": msg}, ensure_ascii=False)


class AutoFiller:
    """SSE流式填报，每步 yield JSON日志行。"""

    def __init__(self, headless: bool = True):
        self.headless = headless

    def run(self, applicant_id: int, project_id: int):
        from database.models import get_applicant, get_project
        from config import CONFIG
        from core.crypto import decrypt

        yield _emit("初始化填报任务…")

        # ── 加载数据 ──────────────────────────────────────────────
        applicant = get_applicant(applicant_id)
        project   = get_project(project_id)
        if not applicant:
            yield _emit(f"申报人 ID={applicant_id} 不存在", "error"); yield _emit("[DONE]"); return
        if not project:
            yield _emit(f"项目 ID={project_id} 不存在", "error"); yield _emit("[DONE]"); return

        yield _emit(f"申报人：{applicant['name']}  项目：{project.get('apply_level','—')}")

        username = CONFIG.get("username", "")
        pwd_raw  = CONFIG.get("password", "")
        try:
            password = decrypt(pwd_raw) if pwd_raw else ""
        except Exception:
            password = pwd_raw   # 未加密时直接使用

        if not username or not password:
            yield _emit("账号或密码未配置，请先在系统设置中填写", "error")
            yield _emit("[DONE]"); return

        # ── 启动浏览器 ────────────────────────────────────────────
        browser = BrowserManager()
        try:
            browser.start(headless=self.headless)
            yield _emit("浏览器已启动")
        except Exception as e:
            yield _emit(f"浏览器启动失败：{e}", "error"); yield _emit("[DONE]"); return

        try:
            yield from self._fill(browser, applicant, project, username, password)
        finally:
            browser.stop()
            yield _emit("浏览器已关闭")
        yield _emit("[DONE]")

    def _fill(self, browser: BrowserManager, applicant, project, username, password):
        page = browser.page

        # ── 登录 ─────────────────────────────────────────────────
        yield _emit(f"正在访问 {SITE_URL}…")
        try:
            browser.goto(SITE_URL)
            page.wait_for_load_state("networkidle", timeout=20_000)
        except Exception as e:
            yield _emit(f"页面加载超时：{e}", "warn")

        # 填用户名
        filled_user = False
        for sel in ['input[name="username"]','input[name="loginName"]','#loginName',
                    'input[placeholder*="用户名"]','input[placeholder*="账号"]',
                    'input[type="text"]']:
            if browser.safe_fill(sel, username, timeout=3_000):
                filled_user = True; break
        yield _emit(f"填写账号：{'✅' if filled_user else '❌ 未找到账号输入框'}")

        # 填密码
        filled_pwd = False
        for sel in ['input[name="password"]','input[name="loginPassword"]','#loginPassword',
                    'input[type="password"]']:
            if browser.safe_fill(sel, password, timeout=3_000):
                filled_pwd = True; break
        yield _emit(f"填写密码：{'✅' if filled_pwd else '❌ 未找到密码输入框'}")

        # 点登录
        clicked = False
        for sel in ['button[type="submit"]','input[type="submit"]',
                    'button:has-text("登录")','a:has-text("登录")','.login-btn','#loginBtn']:
            if browser.safe_click(sel, timeout=3_000):
                clicked = True; break
        yield _emit(f"点击登录：{'✅' if clicked else '⚠ 未找到登录按钮，尝试继续'}")

        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass

        cur = page.url
        login_ok = "login" not in cur.lower() and "Login" not in cur
        yield _emit(f"登录结果：{'✅ 成功' if login_ok else '❌ 可能失败，当前URL：' + cur}",
                    "ok" if login_ok else "error")
        if not login_ok:
            return

        # ── 进入申报入口 ─────────────────────────────────────────
        entered = False
        for sel in ['a:has-text("申报")','a:has-text("职称申报")','a:has-text("个人申报")',
                    '.apply-btn','#applyEntry','.nav-item:has-text("申报")']:
            if browser.safe_click(sel, timeout=5_000):
                entered = True; break
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass
        yield _emit(f"进入申报入口：{'✅' if entered else '⚠ 未找到申报入口，请手动导航'}")

        # ── 选择行业/评委会 ───────────────────────────────────────
        try:
            from core.industries.construction import select_industry_and_committee
            res = select_industry_and_committee(page, project.get("industry",""), project.get("committee",""))
            yield _emit(f"选择行业/评委会：行业{'✅' if res.get('select_industry') else '❌'}  评委会{'✅' if res.get('select_committee') else '❌'}")
        except Exception as e:
            yield _emit(f"选择行业/评委会异常：{e}", "warn")

        # ── 填写基本信息 ─────────────────────────────────────────
        try:
            from core.industries.construction import fill_basic_info
            res = fill_basic_info(page, applicant, project)
            ok_cnt = sum(1 for v in res.values() if v)
            yield _emit(f"填写基本信息：{ok_cnt}/{len(res)} 个字段成功", "ok" if ok_cnt else "warn")
        except Exception as e:
            yield _emit(f"填写基本信息异常：{e}", "warn")

        # ── 截图存档 ─────────────────────────────────────────────
        try:
            import os, tempfile
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = (applicant.get("name") or "unknown").replace(" ", "_")
            path = os.path.join(tempfile.gettempdir(), f"fill_{name}_{ts}.png")
            browser.screenshot(path)
            yield _emit(f"截图已保存：{path}", "ok")
        except Exception as e:
            yield _emit(f"截图失败：{e}", "warn")

        yield _emit("自动填写完成 — 请在浏览器中人工核对后手动提交", "ok")
