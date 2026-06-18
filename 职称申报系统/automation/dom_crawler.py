"""
Crawl the Guangxi Professional Title website to extract DOM selectors for each tab.
Run: python automation/dom_crawler.py
Output: automation/dom_structure.json
"""
import json, time, os
from playwright.sync_api import sync_playwright

LOGIN_URL = "https://my.gxrczc.com/Login"
USERNAME = "450106198005310539"
PASSWORD = "Abc123@@"

def crawl():
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"]
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = ctx.new_page()

        # Step 1: Login
        print("Navigating to login page...")
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)

        # Take screenshot to see the login page
        page.screenshot(path="/tmp/login_page.png")
        print("Login page HTML snippet:")
        print(page.evaluate("() => document.body.innerHTML.substring(0, 3000)"))

        # Try to find and click "密码登录" tab first
        try:
            page.click('text=密码登录', timeout=5000)
            time.sleep(1)
        except:
            pass

        # Fill username
        for sel in ['input[name="username"]', 'input[name="loginName"]', '#loginName',
                    'input[placeholder*="账号"]', 'input[placeholder*="用户名"]',
                    'input[placeholder*="身份证"]', 'input[type="text"]:first-of-type']:
            try:
                page.fill(sel, USERNAME, timeout=3000)
                print(f"Filled username with: {sel}")
                break
            except: continue

        # Fill password
        for sel in ['input[name="password"]', 'input[name="loginPassword"]', '#loginPassword',
                    'input[type="password"]']:
            try:
                page.fill(sel, PASSWORD, timeout=3000)
                print(f"Filled password with: {sel}")
                break
            except: continue

        # Check agreement checkbox
        try:
            page.check('input[type="checkbox"]', timeout=3000)
            print("Checked agreement checkbox")
        except: pass

        # Click login button
        for sel in ['button[type="submit"]', 'button:has-text("登录")', '.login-btn', '#loginBtn']:
            try:
                page.click(sel, timeout=3000)
                print(f"Clicked login with: {sel}")
                break
            except: continue

        page.wait_for_load_state("networkidle", timeout=20000)
        page.screenshot(path="/tmp/after_login.png")
        print(f"After login URL: {page.url}")

        # Handle popups
        time.sleep(2)
        page.screenshot(path="/tmp/popup_check.png")

        # Print body to see popups
        popup_html = page.evaluate("() => document.body.innerHTML.substring(0, 5000)")
        print("After login HTML:")
        print(popup_html)

        # Click "个人用户进入"
        for sel in ['text=个人用户进入', 'button:has-text("个人用户")', '.personal-enter',
                    ':has-text("个人用户进入")']:
            try:
                page.click(sel, timeout=5000)
                print("Clicked 个人用户进入")
                time.sleep(1)
                break
            except: continue

        time.sleep(2)
        page.screenshot(path="/tmp/after_personal.png")

        # Click "知道了"
        for sel in ['text=知道了', 'button:has-text("知道了")', '.confirm-btn']:
            try:
                page.click(sel, timeout=5000)
                print("Clicked 知道了")
                time.sleep(1)
                break
            except: continue

        time.sleep(2)
        page.screenshot(path="/tmp/after_popups.png")
        print(f"After popups URL: {page.url}")
        print("After popups HTML:")
        print(page.evaluate("() => document.body.innerHTML.substring(0, 5000)"))

        # Navigate to 职称评审
        for sel in ['text=职称评审', 'a:has-text("职称评审")', '.module:has-text("职称评审")']:
            try:
                page.click(sel, timeout=5000)
                print("Clicked 职称评审")
                time.sleep(2)
                break
            except: continue

        page.wait_for_load_state("networkidle", timeout=15000)
        page.screenshot(path="/tmp/after_zhicheng.png")
        print(f"After 职称评审 URL: {page.url}")

        # Click 进入
        for sel in ['text=进入', 'button:has-text("进入")', 'a:has-text("进入")']:
            try:
                page.click(sel, timeout=5000)
                print("Clicked 进入")
                time.sleep(2)
                break
            except: continue

        page.wait_for_load_state("networkidle", timeout=15000)
        page.screenshot(path="/tmp/after_enter.png")
        print(f"After 进入 URL: {page.url}")

        # Click 更多
        for sel in ['text=更多', 'button:has-text("更多")', 'a:has-text("更多")']:
            try:
                page.click(sel, timeout=5000)
                print("Clicked 更多")
                time.sleep(2)
                break
            except: continue

        page.screenshot(path="/tmp/after_more.png")

        # Click 材料详情
        for sel in ['text=材料详情', 'a:has-text("材料详情")', 'button:has-text("材料详情")']:
            try:
                page.click(sel, timeout=5000)
                print("Clicked 材料详情")
                time.sleep(2)
                break
            except: continue

        page.wait_for_load_state("networkidle", timeout=15000)
        page.screenshot(path="/tmp/material_detail.png")
        print(f"Material detail URL: {page.url}")

        results['url'] = page.url
        results['page_title'] = page.title()

        # Get full page HTML for analysis
        full_html = page.evaluate("() => document.documentElement.outerHTML")
        with open("/tmp/material_detail.html", "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"Saved full HTML to /tmp/material_detail.html ({len(full_html)} chars)")

        # Get left menu / sidebar structure
        results['sidebar_html'] = page.evaluate("""() => {
            const sels = ['aside', '.left-menu', '.sidebar', '.el-aside',
                         '[class*="side"]', '[class*="left"]', '[class*="menu"]', '[class*="nav"]'];
            let html = '';
            sels.forEach(s => {
                const els = document.querySelectorAll(s);
                els.forEach(el => { html += el.outerHTML.substring(0, 3000) + '\\n---\\n'; });
            });
            return html.substring(0, 10000);
        }""")

        # Get all menu/tab items
        results['all_menu_items'] = page.evaluate("""() => {
            const items = document.querySelectorAll('li, .menu-item, [role="menuitem"], .tab-item, .nav-item');
            return Array.from(items).map((el, i) => ({
                index: i,
                text: el.textContent.trim().substring(0, 100),
                tag: el.tagName,
                class: el.className,
                id: el.id,
                dataAttrs: Object.keys(el.dataset)
            })).filter(i => i.text.length > 0 && i.text.length < 80);
        }""")

        # Capture form inputs on current view
        def capture_fields():
            return page.evaluate("""() => {
                const inputs = document.querySelectorAll('input, select, textarea');
                return Array.from(inputs).map(el => ({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    class: el.className || '',
                    label: (() => {
                        if (el.id) {
                            const lbl = document.querySelector('label[for="' + el.id + '"]');
                            if (lbl) return lbl.textContent.trim();
                        }
                        const parent = el.closest('.form-item, .el-form-item, .form-group, tr, .field');
                        if (parent) {
                            const lbl = parent.querySelector('label, th, td:first-child, .label');
                            if (lbl && lbl !== el) return lbl.textContent.trim();
                        }
                        return '';
                    })()
                }));
            }""")

        results['initial_fields'] = capture_fields()

        # Try to find and click each tab in the left menu
        results['tabs'] = {}

        # First, identify all tab/menu items by text
        tab_texts = page.evaluate("""() => {
            // Look for sidebar or left panel items
            const allEls = document.querySelectorAll('*');
            const candidates = [];
            allEls.forEach(el => {
                const text = el.textContent.trim();
                if (text.length > 1 && text.length < 30 &&
                    (el.tagName === 'LI' || el.tagName === 'A' ||
                     el.className.includes('tab') || el.className.includes('menu') ||
                     el.className.includes('nav') || el.className.includes('item'))) {
                    if (!el.querySelector('li, a')) {  // leaf nodes only
                        candidates.push({
                            text: text,
                            tag: el.tagName,
                            class: el.className.substring(0, 100),
                            id: el.id
                        });
                    }
                }
            });
            return [...new Map(candidates.map(c => [c.text, c])).values()];
        }""")
        results['tab_texts'] = tab_texts

        # Now try clicking tabs and capturing fields
        # Common tab names for this type of system
        known_tabs = [
            '个人承诺', '基本信息', '学历情况', '外语', '继续教育', '学术', '其他',
            '人员信息', '申报信息', '工作经历', '奖惩情况', '论文', '著作'
        ]

        # Try clicking by text
        for tab_text in known_tabs:
            try:
                page.click(f'text="{tab_text}"', timeout=3000)
                time.sleep(1.5)
                fields = capture_fields()
                if fields:
                    results['tabs'][tab_text] = {
                        'fields': fields,
                        'url': page.url
                    }
                    print(f"Tab '{tab_text}': captured {len(fields)} fields")
            except Exception as e:
                print(f"Could not click tab '{tab_text}': {e}")

        browser.close()

    return results

if __name__ == "__main__":
    results = crawl()
    out_path = os.path.join(os.path.dirname(__file__), "dom_structure.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out_path}")
    print(f"Screenshots saved to /tmp/")
    print(f"\nQuick summary:")
    print(f"  URL: {results.get('url', 'N/A')}")
    print(f"  Tabs found: {list(results.get('tabs', {}).keys())}")
    print(f"  Menu items: {len(results.get('all_menu_items', []))}")
