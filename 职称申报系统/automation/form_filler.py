"""自动填报任务 — 驱动 BrowserManager 完成登录 + 表单填写全流程。
SSE流式日志输出，供 routes/auto_fill.py 使用。

Tab结构（按广西职称网左侧菜单）：
  个人承诺
  Tab1·基本信息
  Tab2·学历情况
  Tab3-1·现任专业技术资格
  Tab3-2·破格/直接申报
  Tab4·职称外语和计算机
  Tab5·继续教育
  Tab6-1·工作简历
  Tab6-2·个人社保缴纳记录
  Tab7-1·专业技术工作经历
  Tab7-2·学术团体及社会兼职
  Tab8-1·业绩成果
  Tab8-2·获奖情况
  Tab9·学术成果
  Tab10·专业技术工作总结
  Tab11·其他材料
"""
from __future__ import annotations
import json, time
from datetime import datetime, date
from automation.browser import BrowserManager


SITE_URL = "https://my.gxrczc.com/Login"


def _emit(msg: str, level: str = "info") -> str:
    return json.dumps({"level": level, "msg": msg}, ensure_ascii=False)


def _try_click(page, selectors: list[str], timeout: int = 3000) -> bool:
    """Try clicking each selector in order; return True on first success."""
    for sel in selectors:
        try:
            page.click(sel, timeout=timeout)
            return True
        except Exception:
            continue
    return False


def _try_fill(page, selectors: list[str], value: str, timeout: int = 3000) -> bool:
    """Try filling each selector in order; return True on first success."""
    if not value:
        return False
    for sel in selectors:
        try:
            page.fill(sel, str(value), timeout=timeout)
            return True
        except Exception:
            continue
    return False


def _try_select(page, selectors: list[str], label: str, timeout: int = 3000) -> bool:
    """Try select_option by label, then by value, for each selector."""
    if not label:
        return False
    for sel in selectors:
        for method in ("label", "value"):
            try:
                if method == "label":
                    page.select_option(sel, label=label, timeout=timeout)
                else:
                    page.select_option(sel, value=label, timeout=timeout)
                return True
            except Exception:
                continue
    return False


def _click_tab(page, tab_text: str, timeout: int = 5000) -> bool:
    """Click a left-menu tab by its Chinese text label."""
    selectors = [
        f'.el-menu-item:has-text("{tab_text}")',
        f'li:has-text("{tab_text}")',
        f'a:has-text("{tab_text}")',
        f'span:has-text("{tab_text}")',
        f'[class*="menu-item"]:has-text("{tab_text}")',
        f'[class*="nav-item"]:has-text("{tab_text}")',
        f'text="{tab_text}"',
    ]
    ok = _try_click(page, selectors, timeout=timeout)
    if ok:
        time.sleep(1)
    return ok


def _click_add_button(page, timeout: int = 5000) -> bool:
    """Click the '新增' / '+' button to add a row in a list tab."""
    return _try_click(page, [
        'button:has-text("新增")',
        'button:has-text("添加")',
        'button:has-text("+ 新增")',
        '.el-button:has-text("新增")',
        '.add-btn',
        'button[class*="add"]',
    ], timeout=timeout)


def _click_save_button(page, timeout: int = 5000) -> bool:
    """Click the '保存' / '确定' button in a dialog or form."""
    return _try_click(page, [
        'button:has-text("保存")',
        'button:has-text("确定")',
        '.el-button--primary:has-text("保存")',
        '.el-button--primary:has-text("确定")',
        '.dialog-footer button:has-text("保存")',
        '.dialog-footer button:has-text("确定")',
    ], timeout=timeout)


def _wait_net(page, timeout: int = 10000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass


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
            password = pwd_raw

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

        # ── 步骤1：登录 ───────────────────────────────────────────
        yield _emit(f"正在访问 {SITE_URL}…")
        try:
            browser.goto(SITE_URL)
            _wait_net(page, 20000)
        except Exception as e:
            yield _emit(f"页面加载超时：{e}", "warn")

        # 切换到密码登录tab（如有）
        _try_click(page, ['text=密码登录', '.login-tab:has-text("密码登录")'], timeout=3000)
        time.sleep(0.5)

        # 填用户名（身份证号）
        filled_user = _try_fill(page, [
            'input[name="username"]',
            'input[name="loginName"]',
            '#loginName',
            'input[placeholder*="身份证"]',
            'input[placeholder*="账号"]',
            'input[placeholder*="用户名"]',
            'input[type="text"]:first-of-type',
        ], username)
        yield _emit(f"填写账号：{'成功' if filled_user else '未找到账号输入框'}", "ok" if filled_user else "warn")

        # 填密码
        filled_pwd = _try_fill(page, [
            'input[name="password"]',
            'input[name="loginPassword"]',
            '#loginPassword',
            'input[type="password"]',
        ], password)
        yield _emit(f"填写密码：{'成功' if filled_pwd else '未找到密码输入框'}", "ok" if filled_pwd else "warn")

        # 勾选同意协议
        _try_click(page, ['input[type="checkbox"]', '.agreement-check', '#agree'], timeout=2000)

        # 点击登录
        clicked_login = _try_click(page, [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("登录")',
            '.login-btn',
            '#loginBtn',
        ])
        yield _emit(f"点击登录：{'成功' if clicked_login else '未找到登录按钮'}", "ok" if clicked_login else "warn")

        _wait_net(page, 15000)
        time.sleep(2)

        # ── 步骤2：处理弹窗 ──────────────────────────────────────
        # 选择"个人用户进入"
        if _try_click(page, [
            'text=个人用户进入',
            'button:has-text("个人用户进入")',
            '.personal-enter',
            '[class*="personal"]:has-text("进入")',
        ], timeout=5000):
            yield _emit("已点击「个人用户进入」")
            time.sleep(1)

        # 关闭"知道了"警告
        if _try_click(page, [
            'button:has-text("知道了")',
            'text=知道了',
            '.el-button:has-text("知道了")',
        ], timeout=5000):
            yield _emit("已关闭提示弹窗")
            time.sleep(1)

        cur = page.url
        login_ok = "login" not in cur.lower() and "Login" not in cur
        yield _emit(
            f"登录结果：{'成功，当前URL: ' + cur if login_ok else '可能失败，当前URL：' + cur}",
            "ok" if login_ok else "error"
        )
        if not login_ok:
            return

        # ── 步骤3：进入材料详情 ──────────────────────────────────
        yield _emit("正在导航到材料详情页面…")

        # 点击「职称评审」模块
        if _try_click(page, [
            'text=职称评审',
            'a:has-text("职称评审")',
            '.module:has-text("职称评审")',
            '[class*="module"]:has-text("职称评审")',
        ], timeout=8000):
            yield _emit("已点击「职称评审」")
            _wait_net(page, 10000)
            time.sleep(1)

        # 点击「进入」
        if _try_click(page, [
            'button:has-text("进入")',
            'a:has-text("进入")',
            '.enter-btn',
            'text=进入',
        ], timeout=5000):
            yield _emit("已点击「进入」")
            _wait_net(page, 10000)
            time.sleep(1)

        # 点击「更多」
        if _try_click(page, [
            'text=更多',
            'button:has-text("更多")',
            'a:has-text("更多")',
            '.more-btn',
        ], timeout=5000):
            yield _emit("已点击「更多」")
            time.sleep(1)

        # 点击「材料详情」
        if _try_click(page, [
            'text=材料详情',
            'a:has-text("材料详情")',
            'button:has-text("材料详情")',
            '[class*="detail"]:has-text("材料")',
        ], timeout=5000):
            yield _emit("已点击「材料详情」")
            _wait_net(page, 10000)
            time.sleep(2)

        yield _emit(f"当前页面：{page.url}")

        # ── 步骤4：个人承诺（勾选承诺书）────────────────────────
        yield _emit("处理「个人承诺」…")
        if _click_tab(page, "个人承诺"):
            time.sleep(1)
            # 勾选承诺书复选框
            for sel in [
                'input[type="checkbox"]',
                '.el-checkbox__input',
                '.promise-check',
                '[class*="agree"] input',
            ]:
                try:
                    page.check(sel, timeout=3000)
                    break
                except Exception:
                    continue
            # 点保存/确认
            _click_save_button(page)
            yield _emit("个人承诺：已勾选确认", "ok")
        else:
            yield _emit("个人承诺：未找到菜单项，跳过", "warn")

        # ── 步骤5：Tab1·基本信息 ─────────────────────────────────
        yield _emit("填写「Tab1·基本信息」…")
        yield from self._fill_tab1(page, applicant, project)

        # ── 步骤6：Tab2·学历情况 ─────────────────────────────────
        yield _emit("填写「Tab2·学历情况」…")
        yield from self._fill_tab2(page, applicant)

        # ── 步骤7：Tab3-1·现任专业技术资格 ───────────────────────
        yield _emit("填写「Tab3-1·现任专业技术资格」…")
        yield from self._fill_tab3_1(page, applicant)

        # ── 步骤8：Tab3-2·破格/直接申报 ─────────────────────────
        yield _emit("填写「Tab3-2·破格/直接申报」…")
        yield from self._fill_tab3_2(page, applicant, project)

        # ── 步骤9：Tab4·职称外语和计算机 ─────────────────────────
        yield _emit("填写「Tab4·职称外语和计算机」…")
        yield from self._fill_tab4(page, applicant, project)

        # ── 步骤10：Tab5·继续教育 ────────────────────────────────
        yield _emit("填写「Tab5·继续教育」…")
        yield from self._fill_tab5(page, applicant_id=applicant.get("id", 0))

        # ── 步骤11：Tab6-1·工作简历 ──────────────────────────────
        yield _emit("填写「Tab6-1·工作简历」…")
        yield from self._fill_tab6_1(page, applicant_id=applicant.get("id", 0))

        # ── 步骤12：Tab6-2·个人社保缴纳记录 ─────────────────────
        yield _emit("填写「Tab6-2·个人社保缴纳记录」…")
        yield from self._fill_tab6_2(page, applicant_id=applicant.get("id", 0))

        # ── 步骤13：Tab7-1·专业技术工作经历 ─────────────────────
        yield _emit("填写「Tab7-1·专业技术工作经历」…")
        yield from self._fill_tab7_1(page, applicant_id=applicant.get("id", 0))

        # ── 步骤14：Tab7-2·学术团体及社会兼职 ───────────────────
        yield _emit("填写「Tab7-2·学术团体及社会兼职」…")
        yield from self._fill_tab7_2(page, applicant_id=applicant.get("id", 0))

        # ── 步骤15：Tab8-1·业绩成果 ──────────────────────────────
        yield _emit("填写「Tab8-1·业绩成果」…")
        yield from self._fill_tab8_1(page, applicant_id=applicant.get("id", 0))

        # ── 步骤16：Tab8-2·获奖情况 ──────────────────────────────
        yield _emit("填写「Tab8-2·获奖情况」…")
        yield from self._fill_tab8_2(page, applicant_id=applicant.get("id", 0))

        # ── 步骤17：Tab9·学术成果 ────────────────────────────────
        yield _emit("填写「Tab9·学术成果」…")
        yield from self._fill_tab9(page, applicant_id=applicant.get("id", 0))

        # ── 截图存档 ──────────────────────────────────────────────
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

    # ────────────────────────────────────────────────────────────────
    # Tab 填写方法
    # ────────────────────────────────────────────────────────────────

    def _fill_tab1(self, page, applicant: dict, project: dict):
        """Tab1·基本信息 — 单页表单，直接填写各字段。"""
        if not _click_tab(page, "基本信息"):
            yield _emit("Tab1·基本信息：未找到菜单项", "warn"); return
        time.sleep(1.5)

        a = applicant
        p = project

        # 计算专业技术工作年限
        work_start = a.get("work_start_date") or str(a.get("work_start_year", "") or "")
        work_age = ""
        if work_start:
            try:
                start_year = int(str(work_start)[:4])
                work_age   = str(date.today().year - start_year)
            except Exception:
                pass

        fields = [
            # 文本输入框：(label_hint, selectors, value)
            ("姓名",         ['input[placeholder*="姓名"]', '#name', 'input[name="name"]'],
                             a.get("name", "")),
            ("证件号码",     ['input[placeholder*="证件"]', 'input[placeholder*="身份证"]',
                              '#idCard', 'input[name="idCard"]'],
                             a.get("id_card", "")),
            ("曾用名",       ['input[placeholder*="曾用名"]', '#formerName', 'input[name="formerName"]'],
                             a.get("former_name", "")),
            ("联系电话",     ['input[placeholder*="联系电话"]', 'input[placeholder*="手机"]',
                              '#phone', 'input[name="phone"]'],
                             a.get("phone", "")),
            ("电子邮箱",     ['input[placeholder*="邮箱"]', '#email', 'input[name="email"]'],
                             a.get("email", "")),
            ("籍贯",         ['input[placeholder*="籍贯"]', '#nativePlace', 'input[name="nativePlace"]'],
                             a.get("native_place", "")),
            ("联系地址",     ['input[placeholder*="联系地址"]', 'input[placeholder*="地址"]',
                              '#address', 'input[name="address"]'],
                             a.get("address", "")),
            ("档案所在地机构名称", ['input[placeholder*="档案"]', '#archiveOrg', 'input[name="archiveOrg"]'],
                             a.get("archive_org", "")),
            ("专业技术工作年限", ['input[placeholder*="工作年限"]', '#workAge', 'input[name="workAge"]'],
                             work_age),
            ("曾申报次数",   ['input[placeholder*="申报次数"]', '#applyCount', 'input[name="applyCount"]'],
                             str(a.get("apply_count", "0") or "0")),
            ("从事技术技能工作年限", ['input[placeholder*="技能工作年限"]', '#skillWorkYears'],
                             str(a.get("skill_work_years", "") or "")),
            ("行政职务任命时间", ['input[placeholder*="任命时间"]', '#adminPositionDate'],
                             a.get("admin_position_date", "")),
            ("行政职务说明", ['input[placeholder*="职务说明"]', '#adminPositionNote'],
                             a.get("admin_position_note", "") if hasattr(a, "get") else ""),
        ]

        ok_count = 0
        for label, selectors, value in fields:
            if _try_fill(page, selectors, value):
                ok_count += 1

        # 下拉选择框
        dropdown_fields = [
            ("性别",     ['select[name="gender"]', '#gender', '.el-select:near(:text("性别")) select'],
                         a.get("gender", "")),
            ("民族",     ['select[name="ethnicity"]', '#ethnicity'],
                         a.get("ethnicity", "")),
            ("政治面貌", ['select[name="politics"]', '#politics'],
                         a.get("politics", "")),
            ("个人身份性质", ['select[name="identityType"]', '#identityType'],
                         a.get("identity_type", "")),
            ("是否第一次申报", ['select[name="isFirstApply"]', '#isFirstApply'],
                         a.get("is_first_apply", "")),
            ("参加乡村振兴定向评价", ['select[name="ruralRevitalization"]', '#ruralRevitalization'],
                         a.get("rural_revitalization", "")),
            ("是否高技能人才", ['select[name="isSkilledTalent"]', '#isSkilledTalent'],
                         a.get("is_skilled_talent", "")),
            ("单位级别", ['select[name="unitLevel"]', '#unitLevel'],
                         a.get("unit_level", "")),
            ("行政职务", ['select[name="adminPosition"]', '#adminPosition'],
                         a.get("admin_position", "")),
            ("申报方式", ['select[name="applyMethod"]', '#applyMethod'],
                         p.get("apply_method", "")),
            ("拟评职称系列", ['select[name="titleSeries"]', '#titleSeries'],
                         p.get("title_series", "")),
            ("拟评级别", ['select[name="applyLevel"]', '#applyLevel'],
                         p.get("apply_level", "")),
            ("拟评专业技术资格", ['select[name="applyTitle"]', '#applyTitle'],
                         p.get("apply_title", "")),
            ("拟评专业", ['select[name="specialty"]', '#specialty'],
                         p.get("specialty", "")),
            ("学科",     ['select[name="discipline"]', '#discipline'],
                         p.get("discipline", "")),
        ]

        for label, selectors, value in dropdown_fields:
            if _try_select(page, selectors, value):
                ok_count += 1

        # 日期类字段（用 fill 输入，格式 YYYY-MM 或 YYYY-MM-DD）
        date_fields = [
            ("出生年月",     ['input[placeholder*="出生"]', '#birthDate', 'input[name="birthDate"]'],
                             a.get("birth_date", "")),
            ("参加工作时间", ['input[placeholder*="参加工作"]', '#workStartDate', 'input[name="workStartDate"]'],
                             a.get("work_start_date", "") or str(a.get("work_start_year", "") or "")),
            ("上一次申报时间", ['input[placeholder*="上一次申报"]', '#lastApplyDate'],
                             a.get("last_apply_date", "")),
        ]
        for label, selectors, value in date_fields:
            if _try_fill(page, selectors, value):
                ok_count += 1

        yield _emit(f"Tab1·基本信息：填写完成（{ok_count} 个字段）", "ok")

    def _fill_tab2(self, page, applicant: dict):
        """Tab2·学历情况 — 点新增，填写学历弹窗，保存。"""
        if not _click_tab(page, "学历情况"):
            yield _emit("Tab2·学历情况：未找到菜单项", "warn"); return
        time.sleep(1.5)

        a = applicant

        # 点新增按钮
        if not _click_add_button(page):
            yield _emit("Tab2：未找到新增按钮", "warn"); return
        time.sleep(1)

        # 在弹窗中填写
        edu_map = {"高中/中专": "中专", "大专": "专科", "本科": "本科", "硕士": "硕士研究生", "博士": "博士研究生"}
        study_mode_map = {"全日制": "全日制", "在职": "在职", "函授": "函授"}
        degree_map = {"": "无", "学士": "学士", "硕士": "硕士", "博士": "博士"}

        edu_val   = edu_map.get(a.get("education", ""), a.get("education", ""))
        study_val = study_mode_map.get(a.get("study_mode", ""), a.get("study_mode", ""))
        degree_val = degree_map.get(a.get("degree", ""), a.get("degree", ""))

        grad_month = a.get("grad_month", "")
        grad_date  = f"{a.get('graduation_year','')} - {str(grad_month).zfill(2) if grad_month else ''}"

        fields = [
            (['input[placeholder*="毕业时间"]', '#gradDate', 'input[name="gradDate"]'],           grad_date),
            (['select[name="education"]', '#education', 'select[placeholder*="学历"]'],             edu_val),
            (['input[placeholder*="毕业学校"]', '#school', 'input[name="school"]'],                a.get("school", "")),
            (['input[placeholder*="专业"]', '#major', 'input[name="major"]'],                      a.get("major", "")),
            (['select[name="studyMode"]', '#studyMode'],                                           study_val),
            (['input[placeholder*="学制"]', '#studyYears', 'input[name="studyYears"]'],            ""),
            (['input[placeholder*="学历证书编号"]', '#eduCertNo', 'input[name="eduCertNo"]'],      a.get("edu_cert_no", "")),
            (['select[name="degree"]', '#degree'],                                                  degree_val),
            (['input[placeholder*="学位证书编号"]', '#degreeCertNo', 'input[name="degreeCertNo"]'], a.get("degree_cert_no", "")),
            (['input[placeholder*="学位授予单位"]', '#degreeSchool', 'input[name="degreeSchool"]'], a.get("degree_school", "")),
        ]

        ok_count = 0
        for selectors, value in fields:
            if value:
                if selectors[0].startswith("select") or "select" in selectors[0]:
                    if _try_select(page, selectors, value):
                        ok_count += 1
                else:
                    if _try_fill(page, selectors, value):
                        ok_count += 1

        _click_save_button(page)
        time.sleep(1)
        yield _emit(f"Tab2·学历情况：新增行完成（{ok_count} 个字段）", "ok")

    def _fill_tab3_1(self, page, applicant: dict):
        """Tab3-1·现任专业技术资格 — 点新增，填写职称证书信息。"""
        if not _click_tab(page, "现任专业技术资格"):
            # Try alternate menu text
            if not _click_tab(page, "职业资格"):
                yield _emit("Tab3-1：未找到菜单项", "warn"); return
        time.sleep(1.5)

        a = applicant
        if not _click_add_button(page):
            yield _emit("Tab3-1：未找到新增按钮", "warn"); return
        time.sleep(1)

        # 格式：YYYY-MM
        title_date = ""
        if a.get("title_year"):
            m = str(a.get("title_month", "1") or "1").zfill(2)
            title_date = f"{a['title_year']}-{m}"

        fields = [
            (['select[name="qualificationType"]', '#qualificationType'],  "职称证书"),
            (['input[placeholder*="现任专业技术职务"]', '#currentTitle'],  a.get("current_specialty", "")),
            (['input[placeholder*="专业"]', '#titleSpecialty'],            a.get("title_specialty", "")),
            (['input[placeholder*="资格取得时间"]', '#titleDate'],         title_date),
            (['input[placeholder*="证书编号"]', '#titleCertNo'],           a.get("title_cert_no", "")),
            (['input[placeholder*="管理号"]', '#titleManageNo'],           a.get("title_manage_no", "")),
            (['input[placeholder*="批准机关"]', '#titleIssuer'],           a.get("title_issuer", "")),
            (['input[placeholder*="适用范围"]', '#titleScope'],            a.get("title_scope", "")),
        ]

        ok_count = 0
        for selectors, value in fields:
            if value:
                if selectors[0].startswith("select"):
                    if _try_select(page, selectors, value):
                        ok_count += 1
                else:
                    if _try_fill(page, selectors, value):
                        ok_count += 1

        # 是否以该资格申报 → 是
        _try_select(page, ['select[name="isApplyBase"]', '#isApplyBase'], "是")

        _click_save_button(page)
        time.sleep(1)
        yield _emit(f"Tab3-1·现任专业技术资格：完成（{ok_count} 个字段）", "ok")

    def _fill_tab3_2(self, page, applicant: dict, project: dict):
        """Tab3-2·破格/直接申报 — 单页Radio/Select。"""
        if not _click_tab(page, "破格"):
            if not _click_tab(page, "直接申报"):
                yield _emit("Tab3-2：未找到菜单项，跳过", "warn"); return
        time.sleep(1.5)

        a = applicant
        apply_exception = a.get("apply_exception", "否") or "否"

        _try_select(page, ['select[name="applyException"]', '#applyException'], apply_exception)
        _try_select(page, ['select[name="langCompRequire"]', '#langCompRequire'],
                    a.get("lang_comp_require", "不作要求") or "不作要求")
        _try_select(page, ['select[name="langExamResult"]', '#langExamResult'],
                    a.get("lang_exam_result", "不作要求") or "不作要求")

        yield _emit("Tab3-2·破格/直接申报：完成", "ok")

    def _fill_tab4(self, page, applicant: dict, project: dict):
        """Tab4·职称外语和职称计算机 — 多个下拉选择，通常为"不作要求"。"""
        if not _click_tab(page, "职称外语"):
            if not _click_tab(page, "外语"):
                yield _emit("Tab4：未找到菜单项，跳过", "warn"); return
        time.sleep(1.5)

        a = applicant
        default = "不作要求"

        selects = [
            ['select[name="langCompRequire"]', '#langCompRequire',   'select:near(:text("职称外语计算机要求"))'],
            ['select[name="langExamResult"]', '#langExamResult',     'select:near(:text("外语考试合格情况"))'],
            ['select[name="compExamResult"]', '#compExamResult',     'select:near(:text("计算机考试"))'],
            ['select[name="langCompCheck"]',  '#langCompCheck'],
            ['select[name="langCompOtherProv"]', '#langCompOtherProv'],
        ]
        values = [
            a.get("lang_comp_require", default) or default,
            a.get("lang_exam_result",  default) or default,
            a.get("comp_exam_result",  default) or default,
            a.get("lang_comp_check",   default) or default,
            a.get("lang_comp_other_prov", default) or default,
        ]
        ok_count = sum(1 for s, v in zip(selects, values) if _try_select(page, s, v))

        yield _emit(f"Tab4·职称外语计算机：完成（{ok_count} 个字段）", "ok")

    def _fill_tab5(self, page, applicant_id: int):
        """Tab5·继续教育 — 按年度逐行新增。"""
        if not _click_tab(page, "继续教育"):
            yield _emit("Tab5：未找到菜单项，跳过", "warn"); return
        time.sleep(1.5)

        try:
            from database.models import list_edu_trainings
            rows = list_edu_trainings(applicant_id)
        except Exception:
            rows = []

        if not rows:
            yield _emit("Tab5·继续教育：数据库无继续教育记录，跳过", "warn"); return

        ok_rows = 0
        for row in rows:
            if not _click_add_button(page):
                break
            time.sleep(0.8)

            fields = [
                (['input[placeholder*="年度"]', '#year', 'input[name="year"]'],          str(row.get("year", ""))),
                (['input[placeholder*="公需必修"]', '#requiredHours'],                   str(row.get("required_hours", "0") or "0")),
                (['input[placeholder*="公需选修"]', '#electiveHours'],                   str(row.get("elective_hours", "0") or "0")),
                (['input[placeholder*="行业内数据共享学分"]', '#shareCredits'],          str(row.get("share_credits", "0") or "0")),
                (['input[placeholder*="行业内数据共享学时"]', '#shareHours'],            str(row.get("share_hours", "0") or "0")),
                (['input[placeholder*="专业学时"]', '#profHours'],                       str(row.get("prof_hours", "0") or "0")),
                (['input[placeholder*="总学时"]', '#totalHours'],                        str(row.get("total_hours", "0") or "0")),
            ]
            ok_count = sum(1 for s, v in fields if _try_fill(page, s, v))
            _click_save_button(page)
            time.sleep(0.5)
            ok_rows += 1

        yield _emit(f"Tab5·继续教育：完成 {ok_rows} 行", "ok")

    def _fill_tab6_1(self, page, applicant_id: int):
        """Tab6-1·工作简历 — 按段逐行新增。"""
        if not _click_tab(page, "工作简历"):
            yield _emit("Tab6-1：未找到菜单项，跳过", "warn"); return
        time.sleep(1.5)

        try:
            from database.models import list_work_experiences
            rows = list_work_experiences(applicant_id)
        except Exception:
            rows = []

        if not rows:
            yield _emit("Tab6-1·工作简历：无数据，跳过", "warn"); return

        ok_rows = 0
        for row in rows:
            if not _click_add_button(page):
                break
            time.sleep(0.8)

            fields = [
                (['input[placeholder*="开始时间"]', '#startDate'],  row.get("start_date", "")),
                (['input[placeholder*="截止时间"]', '#endDate'],    row.get("end_date", "")),
                (['input[placeholder*="工作单位"]', '#workUnit'],   row.get("work_unit", "")),
                (['input[placeholder*="职务"]', '#position'],       row.get("position", "")),
            ]
            ok_count = sum(1 for s, v in fields if _try_fill(page, s, v))
            _click_save_button(page)
            time.sleep(0.5)
            ok_rows += 1

        yield _emit(f"Tab6-1·工作简历：完成 {ok_rows} 行", "ok")

    def _fill_tab6_2(self, page, applicant_id: int):
        """Tab6-2·个人社保缴纳记录 — 逐行新增。"""
        if not _click_tab(page, "社保"):
            if not _click_tab(page, "社保缴纳"):
                yield _emit("Tab6-2：未找到菜单项，跳过", "warn"); return
        time.sleep(1.5)

        try:
            from database.models import list_social_insurance
            rows = list_social_insurance(applicant_id)
        except Exception:
            rows = []

        if not rows:
            yield _emit("Tab6-2·社保记录：无数据，跳过", "warn"); return

        ok_rows = 0
        for row in rows:
            if not _click_add_button(page):
                break
            time.sleep(0.8)

            fields = [
                (['input[placeholder*="缴纳开始时间"]', '#insStartDate'],   row.get("start_date", "")),
                (['input[placeholder*="缴纳结束时间"]', '#insEndDate'],     row.get("end_date", "")),
                (['input[placeholder*="缴纳社保机构"]', '#insOrg'],          row.get("ins_org", "")),
                (['input[placeholder*="缴纳单位"]', '#insUnit'],             row.get("ins_unit", "")),
            ]
            ok_count = sum(1 for s, v in fields if _try_fill(page, s, v))
            _click_save_button(page)
            time.sleep(0.5)
            ok_rows += 1

        yield _emit(f"Tab6-2·社保记录：完成 {ok_rows} 行", "ok")

    def _fill_tab7_1(self, page, applicant_id: int):
        """Tab7-1·专业技术工作经历。"""
        if not _click_tab(page, "专业技术工作经历"):
            yield _emit("Tab7-1：未找到菜单项，跳过", "warn"); return
        time.sleep(1.5)

        # list_work_experiences reused; model may differ
        # Try from a dedicated list if available
        rows = []
        try:
            from database.models import list_work_experiences
            rows = [r for r in list_work_experiences(applicant_id)
                    if r.get("exp_type") == "technical"]
        except Exception:
            pass

        if not rows:
            yield _emit("Tab7-1：无专业技术工作经历数据，跳过", "warn"); return

        ok_rows = 0
        for row in rows:
            if not _click_add_button(page):
                break
            time.sleep(0.8)

            fields = [
                (['input[placeholder*="开始时间"]', '#startDate'],        row.get("start_date", "")),
                (['input[placeholder*="截止时间"]', '#endDate'],          row.get("end_date", "")),
                (['input[placeholder*="工作单位"]', '#workUnit'],         row.get("work_unit", "")),
                (['input[placeholder*="项目名称"]', '#projectName'],      row.get("project_name", "")),
                (['input[placeholder*="任职"]', '#role'],                 row.get("role", "")),
            ]
            ok_count = sum(1 for s, v in fields if _try_fill(page, s, v))
            _click_save_button(page)
            time.sleep(0.5)
            ok_rows += 1

        yield _emit(f"Tab7-1·专业技术工作经历：完成 {ok_rows} 行", "ok")

    def _fill_tab7_2(self, page, applicant_id: int):
        """Tab7-2·学术团体及社会兼职。"""
        if not _click_tab(page, "学术团体"):
            yield _emit("Tab7-2：未找到菜单项，跳过", "warn"); return
        time.sleep(1.5)

        rows = []
        try:
            # Try getting from a dedicated function or fallback
            from database.models import list_work_experiences
            rows = [r for r in list_work_experiences(applicant_id)
                    if r.get("exp_type") == "academic_org"]
        except Exception:
            pass

        if not rows:
            yield _emit("Tab7-2：无学术团体数据，跳过", "warn"); return

        ok_rows = 0
        for row in rows:
            if not _click_add_button(page):
                break
            time.sleep(0.8)

            fields = [
                (['input[placeholder*="开始时间"]', '#startDate'],    row.get("start_date", "")),
                (['input[placeholder*="截止时间"]', '#endDate'],      row.get("end_date", "")),
                (['input[placeholder*="学术团体名称"]', '#orgName'],  row.get("org_name", "")),
                (['input[placeholder*="在何职"]', '#orgRole'],        row.get("org_role", "")),
            ]
            ok_count = sum(1 for s, v in fields if _try_fill(page, s, v))
            _click_save_button(page)
            time.sleep(0.5)
            ok_rows += 1

        yield _emit(f"Tab7-2·学术团体：完成 {ok_rows} 行", "ok")

    def _fill_tab8_1(self, page, applicant_id: int):
        """Tab8-1·业绩成果。"""
        if not _click_tab(page, "业绩成果"):
            yield _emit("Tab8-1：未找到菜单项，跳过", "warn"); return
        time.sleep(1.5)

        rows = []
        try:
            from database.models import list_achievements
            rows = list_achievements(applicant_id)
        except Exception:
            pass

        if not rows:
            yield _emit("Tab8-1：无业绩成果数据，跳过", "warn"); return

        ok_rows = 0
        for row in rows:
            if not _click_add_button(page):
                break
            time.sleep(0.8)

            fields = [
                (['input[placeholder*="开始时间"]', '#startDate'],          row.get("start_date", "")),
                (['input[placeholder*="截止时间"]', '#endDate'],            row.get("end_date", "")),
                (['input[placeholder*="业绩成果"]', '#achieveName'],        row.get("achieve_name", "")),
                (['select[name="projectLevel"]', '#projectLevel'],          row.get("project_level", "")),
                (['input[placeholder*="个人排名"]', '#personalRank'],       str(row.get("personal_rank", "") or "")),
            ]
            ok_count = 0
            for s, v in fields:
                if isinstance(s[0], str) and s[0].startswith("select"):
                    if _try_select(page, s, v): ok_count += 1
                else:
                    if _try_fill(page, s, v): ok_count += 1

            _click_save_button(page)
            time.sleep(0.5)
            ok_rows += 1

        yield _emit(f"Tab8-1·业绩成果：完成 {ok_rows} 行", "ok")

    def _fill_tab8_2(self, page, applicant_id: int):
        """Tab8-2·获奖情况。"""
        if not _click_tab(page, "获奖"):
            yield _emit("Tab8-2：未找到菜单项，跳过", "warn"); return
        time.sleep(1.5)

        rows = []
        try:
            from database.models import list_awards
            rows = list_awards(applicant_id)
        except Exception:
            pass

        if not rows:
            yield _emit("Tab8-2：无获奖数据，跳过", "warn"); return

        ok_rows = 0
        for row in rows:
            if not _click_add_button(page):
                break
            time.sleep(0.8)

            fields = [
                (['input[placeholder*="授奖时间"]', '#awardDate'],            row.get("award_date", "")),
                (['input[placeholder*="名称与内容"]', '#awardName'],          row.get("award_name", "")),
                (['select[name="awardLevel"]', '#awardLevel'],                row.get("award_level", "")),
                (['input[placeholder*="授奖机关"]', '#awardOrg'],             row.get("award_org", "")),
                (['input[placeholder*="个人排名"]', '#personalRank'],         str(row.get("personal_rank", "") or "")),
            ]
            ok_count = 0
            for s, v in fields:
                if s[0].startswith("select"):
                    if _try_select(page, s, v): ok_count += 1
                else:
                    if _try_fill(page, s, v): ok_count += 1

            _click_save_button(page)
            time.sleep(0.5)
            ok_rows += 1

        yield _emit(f"Tab8-2·获奖情况：完成 {ok_rows} 行", "ok")

    def _fill_tab9(self, page, applicant_id: int):
        """Tab9·学术成果（论文/著作）。"""
        if not _click_tab(page, "学术成果"):
            yield _emit("Tab9：未找到菜单项，跳过", "warn"); return
        time.sleep(1.5)

        rows = []
        try:
            from database.models import list_papers
            rows = list_papers(applicant_id)
        except Exception:
            pass

        if not rows:
            yield _emit("Tab9：无学术成果数据，跳过", "warn"); return

        ok_rows = 0
        for row in rows:
            if not _click_add_button(page):
                break
            time.sleep(0.8)

            fields = [
                (['input[placeholder*="发表时间"]', '#publishDate'],          row.get("publish_date", "")),
                (['select[name="achieveType"]', '#achieveType'],              row.get("achieve_type", "")),
                (['input[placeholder*="学术成果名称"]', '#achieveName'],      row.get("paper_title", "")),
                (['input[placeholder*="登载刊物"]', '#journal'],              row.get("journal", "")),
                (['select[name="role"]', '#role'],                            row.get("role", "")),
                (['select[name="isRepresent"]', '#isRepresent'],              row.get("is_represent", "")),
            ]
            ok_count = 0
            for s, v in fields:
                if s[0].startswith("select"):
                    if _try_select(page, s, v): ok_count += 1
                else:
                    if _try_fill(page, s, v): ok_count += 1

            _click_save_button(page)
            time.sleep(0.5)
            ok_rows += 1

        yield _emit(f"Tab9·学术成果：完成 {ok_rows} 行", "ok")
