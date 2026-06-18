"""
Crawl the Guangxi Professional Title website to extract DOM selectors for each tab.
Run: python automation/dom_crawler.py
Output: automation/dom_structure.json
"""
import json, time, os
from datetime import datetime
from playwright.sync_api import sync_playwright

LOGIN_URL = "https://my.gxrczc.com/Login"

SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "screenshots")


def _log(level, msg):
    return json.dumps({"level": level, "msg": msg}, ensure_ascii=False)


def crawl_with_log(username, password, headless=True):
    """Generator that yields JSON log lines and saves dom_structure.json on completion."""
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    yield _log("info", f"启动浏览器（headless={headless}）...")

    results = {
        "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tabs": {},
        "field_mapping": {},
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
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

            # ── Step 1: Login ─────────────────────────────────────────────
            yield _log("info", f"正在打开登录页面 {LOGIN_URL} ...")
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=20000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_login.png"))

            # Click 密码登录 tab if present
            try:
                page.click('text=密码登录', timeout=5000)
                time.sleep(1)
            except Exception:
                pass

            # Fill username
            filled_user = False
            for sel in ['input[name="username"]', 'input[name="loginName"]', '#loginName',
                        'input[placeholder*="账号"]', 'input[placeholder*="用户名"]',
                        'input[placeholder*="身份证"]', 'input[type="text"]:first-of-type']:
                try:
                    page.fill(sel, username, timeout=3000)
                    yield _log("info", f"已填写账号（选择器: {sel}）")
                    filled_user = True
                    break
                except Exception:
                    continue
            if not filled_user:
                yield _log("warn", "未能自动填写账号，请检查页面结构")

            # Fill password
            filled_pwd = False
            for sel in ['input[name="password"]', 'input[name="loginPassword"]', '#loginPassword',
                        'input[type="password"]']:
                try:
                    page.fill(sel, password, timeout=3000)
                    yield _log("info", f"已填写密码（选择器: {sel}）")
                    filled_pwd = True
                    break
                except Exception:
                    continue
            if not filled_pwd:
                yield _log("warn", "未能自动填写密码")

            # Check agreement checkbox
            try:
                page.check('input[type="checkbox"]', timeout=3000)
                yield _log("info", "已勾选用户协议")
            except Exception:
                pass

            # Click login button
            clicked_login = False
            for sel in ['button[type="submit"]', 'button:has-text("登录")', '.login-btn', '#loginBtn']:
                try:
                    page.click(sel, timeout=3000)
                    yield _log("info", f"已点击登录按钮（选择器: {sel}）")
                    clicked_login = True
                    break
                except Exception:
                    continue
            if not clicked_login:
                yield _log("warn", "未找到登录按钮")

            page.wait_for_load_state("networkidle", timeout=20000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_after_login.png"))
            yield _log("info", f"登录后URL: {page.url}")

            # ── Step 2: Handle popups ─────────────────────────────────────
            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_popup_check.png"))

            for sel in ['text=个人用户进入', 'button:has-text("个人用户")', '.personal-enter',
                        ':has-text("个人用户进入")']:
                try:
                    page.click(sel, timeout=5000)
                    yield _log("info", "已点击「个人用户进入」")
                    time.sleep(1)
                    break
                except Exception:
                    continue

            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_after_personal.png"))

            for sel in ['text=知道了', 'button:has-text("知道了")', '.confirm-btn']:
                try:
                    page.click(sel, timeout=5000)
                    yield _log("info", "已点击「知道了」")
                    time.sleep(1)
                    break
                except Exception:
                    continue

            time.sleep(2)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_after_popups.png"))
            yield _log("info", f"弹窗处理后URL: {page.url}")

            # ── Step 3: Navigate to 材料详情 ──────────────────────────────
            yield _log("info", "正在导航到职称评审...")
            for sel in ['text=职称评审', 'a:has-text("职称评审")', '.module:has-text("职称评审")']:
                try:
                    page.click(sel, timeout=5000)
                    yield _log("info", "已点击「职称评审」")
                    time.sleep(2)
                    break
                except Exception:
                    continue

            page.wait_for_load_state("networkidle", timeout=15000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_zhicheng.png"))

            for sel in ['text=进入', 'button:has-text("进入")', 'a:has-text("进入")']:
                try:
                    page.click(sel, timeout=5000)
                    yield _log("info", "已点击「进入」")
                    time.sleep(2)
                    break
                except Exception:
                    continue

            page.wait_for_load_state("networkidle", timeout=15000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_after_enter.png"))

            for sel in ['text=更多', 'button:has-text("更多")', 'a:has-text("更多")']:
                try:
                    page.click(sel, timeout=5000)
                    yield _log("info", "已点击「更多」")
                    time.sleep(2)
                    break
                except Exception:
                    continue

            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "08_after_more.png"))

            for sel in ['text=材料详情', 'a:has-text("材料详情")', 'button:has-text("材料详情")']:
                try:
                    page.click(sel, timeout=5000)
                    yield _log("info", "已点击「材料详情」")
                    time.sleep(2)
                    break
                except Exception:
                    continue

            page.wait_for_load_state("networkidle", timeout=15000)
            page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "09_material_detail.png"))
            yield _log("ok", f"已进入材料详情页面: {page.url}")

            # ── Step 4: Capture tab fields ────────────────────────────────
            def capture_fields():
                return page.evaluate("""() => {
                    const inputs = document.querySelectorAll('input, select, textarea');
                    return Array.from(inputs).map(el => ({
                        tag: el.tagName,
                        type: el.type || '',
                        name: el.name || '',
                        id: el.id || '',
                        placeholder: el.placeholder || '',
                        class: (el.className || '').substring(0, 100),
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
                    })).filter(f => f.type !== 'hidden');
                }""")

            def capture_tables():
                return page.evaluate("""() => {
                    const tables = document.querySelectorAll('table');
                    return Array.from(tables).map(t => {
                        const headers = Array.from(t.querySelectorAll('th')).map(th => th.textContent.trim()).filter(Boolean);
                        return headers;
                    }).filter(h => h.length > 0);
                }""")

            known_tabs = [
                '个人承诺', '1.基本信息', '2.学历情况', '3.职称证书',
                '4.职称外语计算机', '5.继续教育', '6.工作经历',
                '7.专业技术工作经历', '8.业绩成果', '9.学术成果',
                '10.专业技术工作总结', '11.其他材料',
                # fallback shorter names
                '基本信息', '学历情况', '外语', '继续教育', '工作经历',
                '论文', '著作', '人员信息', '申报信息', '奖惩情况',
            ]

            yield _log("info", "开始逐个点击左侧菜单Tab并抓取字段...")

            seen_tabs = set()
            for tab_text in known_tabs:
                if tab_text in seen_tabs:
                    continue
                try:
                    page.click(f'text="{tab_text}"', timeout=3000)
                    time.sleep(1.5)
                    fields_raw = capture_fields()
                    tables_raw = capture_tables()

                    # Build structured fields
                    fields = []
                    for f in fields_raw:
                        sel_parts = []
                        if f["id"]:
                            sel_parts.append(f"#{f['id']}")
                        elif f["name"]:
                            sel_parts.append(f"[name='{f['name']}']")
                        else:
                            sel_parts.append(f["tag"].lower())
                        selector = sel_parts[0] if sel_parts else ""
                        fields.append({
                            "label": f["label"],
                            "name": f["name"],
                            "id": f["id"],
                            "type": f["type"] or f["tag"].lower(),
                            "selector": selector,
                            "placeholder": f["placeholder"],
                        })

                    results["tabs"][tab_text] = {
                        "fields": fields,
                        "tables": tables_raw,
                    }
                    seen_tabs.add(tab_text)

                    # Screenshot for this tab
                    safe_name = tab_text.replace(".", "_").replace("/", "_")
                    page.screenshot(path=os.path.join(SCREENSHOTS_DIR, f"tab_{safe_name}.png"))

                    yield _log("ok", f"Tab「{tab_text}」: 捕获 {len(fields)} 个字段, {len(tables_raw)} 个表格")
                except Exception as e:
                    pass  # Tab not found on this page, skip silently

            # ── Step 5: Build field_mapping ───────────────────────────────
            # Map common DB fields to selectors based on label matching
            db_label_map = {
                "applicants.name":          ["姓名", "名字"],
                "applicants.id_card":        ["身份证号", "身份证"],
                "applicants.gender":         ["性别"],
                "applicants.birth_date":     ["出生日期", "出生年月"],
                "applicants.ethnicity":      ["民族"],
                "applicants.politics":       ["政治面貌"],
                "applicants.education":      ["学历"],
                "applicants.major":          ["专业", "所学专业"],
                "applicants.school":         ["毕业院校", "学校"],
                "applicants.graduation_year":["毕业年份", "毕业年"],
                "applicants.work_unit":      ["工作单位", "单位名称"],
                "applicants.work_unit_type": ["单位类型", "单位性质"],
                "applicants.current_position":["现任职务", "行政职务"],
                "applicants.title_level":    ["现任职称", "职称等级"],
                "applicants.title_year":     ["取得时间", "职称取得年"],
                "applicants.phone":          ["手机", "电话", "联系电话"],
                "applicants.native_place":   ["籍贯"],
                "applicants.former_name":    ["曾用名"],
            }

            field_mapping = {}
            for db_field, labels in db_label_map.items():
                for tab_name, tab_data in results["tabs"].items():
                    for field in tab_data["fields"]:
                        field_label = field.get("label", "")
                        for lbl in labels:
                            if lbl in field_label or field_label in labels:
                                if field.get("selector"):
                                    field_mapping[db_field] = {
                                        "tab": tab_name,
                                        "selector": field["selector"],
                                        "label": field_label,
                                    }
                                    break
                        if db_field in field_mapping:
                            break
                    if db_field in field_mapping:
                        break

            results["field_mapping"] = field_mapping

            browser.close()

    except Exception as e:
        yield _log("error", f"抓取异常: {str(e)}")
        yield _log("done", "[DONE]")
        return

    # ── Save results ──────────────────────────────────────────────────
    out_path = os.path.join(os.path.dirname(__file__), "dom_structure.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Summary
    tab_count = len(results["tabs"])
    total_fields = sum(len(v["fields"]) for v in results["tabs"].values())
    mapping_count = len(results["field_mapping"])
    yield _log("info", f"抓取完成：共 {tab_count} 个Tab，{total_fields} 个字段，{mapping_count} 个字段映射")
    yield _log("info", f"结果已保存到: {out_path}")
    yield _log("info", f"截图保存到: {SCREENSHOTS_DIR}/")

    tabs_summary = ", ".join(f"「{k}」({len(v['fields'])}个字段)" for k, v in results["tabs"].items())
    yield _log("ok", f"Tab列表: {tabs_summary}")
    yield _log("done", "[DONE]")


def crawl(username=None, password=None):
    """Original function — run synchronously and return results dict."""
    import sys
    _username = username or USERNAME if 'USERNAME' in dir() else ""
    _password = password or PASSWORD if 'PASSWORD' in dir() else ""

    results = {}
    log_lines = list(crawl_with_log(_username, _password, headless=True))
    # Load saved results
    out_path = os.path.join(os.path.dirname(__file__), "dom_structure.json")
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            results = json.load(f)
    return results


if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "450106198005310539"
    password = sys.argv[2] if len(sys.argv) > 2 else "Abc123@@"

    print("Starting DOM crawl...")
    for line in crawl_with_log(username, password, headless=True):
        try:
            d = json.loads(line)
            print(f"[{d['level'].upper()}] {d['msg']}")
        except Exception:
            print(line)
