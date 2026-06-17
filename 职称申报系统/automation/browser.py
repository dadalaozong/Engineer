"""浏览器管理 — Playwright 封装，支持有头/无头模式，截图，等待。"""
from __future__ import annotations
from typing import Optional


class BrowserManager:
    """单例浏览器会话，跨填报任务复用。"""

    def __init__(self):
        self._playwright = None
        self._browser    = None
        self._context    = None
        self.page        = None
        self._headless   = False

    # ── lifecycle ─────────────────────────────────────────────────
    def start(self, headless: bool = False) -> None:
        from playwright.sync_api import sync_playwright
        self._headless   = headless
        self._playwright = sync_playwright().start()
        self._browser    = self._playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._context = self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="zh-CN",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self.page = self._context.new_page()

    def stop(self) -> None:
        try:
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._browser = self._context = self.page = self._playwright = None

    @property
    def is_running(self) -> bool:
        return self.page is not None

    # ── navigation ────────────────────────────────────────────────
    def goto(self, url: str, timeout: int = 30_000) -> None:
        self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")

    def wait_for_selector(self, selector: str, timeout: int = 15_000):
        return self.page.wait_for_selector(selector, timeout=timeout)

    def screenshot(self, path: str) -> None:
        self.page.screenshot(path=path, full_page=False)

    # ── login ─────────────────────────────────────────────────────
    def login(self, url: str, username: str, password: str) -> bool:
        """
        Navigate to login page and submit credentials.
        Returns True if login succeeded (URL changed away from login page).
        """
        self.goto(url)

        # wait for login form
        self.page.wait_for_load_state("networkidle", timeout=20_000)

        # fill username — try common selectors
        for sel in ['input[name="username"]', 'input[type="text"]',
                    '#username', '#loginName', 'input[placeholder*="用户名"]',
                    'input[placeholder*="账号"]']:
            try:
                self.page.fill(sel, username, timeout=3_000)
                break
            except Exception:
                continue

        # fill password
        for sel in ['input[name="password"]', 'input[type="password"]',
                    '#password', '#loginPassword']:
            try:
                self.page.fill(sel, password, timeout=3_000)
                break
            except Exception:
                continue

        # submit
        for sel in ['button[type="submit"]', 'input[type="submit"]',
                    '.login-btn', '#loginBtn', 'button:has-text("登录")',
                    'a:has-text("登录")']:
            try:
                self.page.click(sel, timeout=3_000)
                break
            except Exception:
                continue

        # wait for navigation
        try:
            self.page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass

        current_url = self.page.url
        return "login" not in current_url.lower() and "signin" not in current_url.lower()

    # ── form helpers ──────────────────────────────────────────────
    def safe_fill(self, selector: str, value: str, timeout: int = 5_000) -> bool:
        try:
            self.page.fill(selector, value, timeout=timeout)
            return True
        except Exception:
            return False

    def safe_select(self, selector: str, value: str, timeout: int = 5_000) -> bool:
        try:
            self.page.select_option(selector, label=value, timeout=timeout)
            return True
        except Exception:
            try:
                self.page.select_option(selector, value=value, timeout=timeout)
                return True
            except Exception:
                return False

    def safe_click(self, selector: str, timeout: int = 5_000) -> bool:
        try:
            self.page.click(selector, timeout=timeout)
            return True
        except Exception:
            return False

    def type_slowly(self, selector: str, text: str, delay: int = 50) -> bool:
        """Type character by character to bypass paste detection."""
        try:
            el = self.page.query_selector(selector)
            if el:
                el.click()
                el.type(text, delay=delay)
                return True
            return False
        except Exception:
            return False
