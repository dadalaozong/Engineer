"""DeepSeek AI 写作模块 — 根据申报人信息和项目数据生成三类文书。"""
from __future__ import annotations
from typing import Generator


DOCUMENT_TYPES = {
    "work_summary":   "工作总结",
    "masterwork_desc": "代表作说明书",
    "achievement_desc": "业绩描述",
}

_PROMPTS = {
    "work_summary": """\
你是一位专业的广西职称申报材料撰写专家。请根据以下信息，为申报人撰写一份专业、严谨、符合广西职称申报要求的工作总结。
工作总结应包含：个人基本情况、专业技术工作经历、主要业绩成果、今后工作展望，字数约1500-2000字。

申报人信息：
{info}

请直接输出工作总结正文，不要加多余的说明。""",

    "masterwork_desc": """\
你是一位专业的广西职称申报材料撰写专家。请根据以下工程项目信息，撰写一份符合广西职称申报要求的代表作说明书。
代表作说明书应包含：工程概况、申报人承担的工作内容及职责、技术难点及解决方案、取得的技术成果及社会效益，字数约1000-1500字。

项目信息：
{info}

请直接输出代表作说明书正文，不要加多余的说明。""",

    "achievement_desc": """\
你是一位专业的广西职称申报材料撰写专家。请根据以下业绩信息，撰写一段简洁、专业的业绩描述，用于职称申报业绩栏填写，字数150-300字。

业绩信息：
{info}

请直接输出业绩描述正文，不要加标题和多余的说明。""",
}


def stream_write(doc_type: str, fields: dict):
    """Module-level streaming entry point for routes/ai_writer.py."""
    from config import CONFIG
    api_key = CONFIG.get("ai_api_key", "")
    model   = CONFIG.get("ai_model", "deepseek-chat")
    base_url = CONFIG.get("ai_base_url", "https://api.deepseek.com")
    if not api_key:
        raise ValueError("AI API Key 未配置，请在系统设置中填写")

    # Build info string from fields
    info_lines = []
    label_map = {
        "name": "姓名", "work_unit": "工作单位", "education": "学历",
        "major": "专业", "title_level": "现有职称", "apply_level": "申报级别",
        "industry": "行业", "project_name": "代表性工程", "scale": "工程规模",
        "role": "担任职务", "start_date": "开工日期", "end_date": "竣工日期",
        "description": "项目描述", "work_start_year": "参加工作年份",
        "graduation_year": "毕业年份", "school": "毕业院校",
    }
    for k, v in fields.items():
        if v:
            label = label_map.get(k, k)
            info_lines.append(f"{label}：{v}")
    info = "\n".join(info_lines)

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    prompt_key = doc_type if doc_type in _PROMPTS else "work_summary"
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": _PROMPTS[prompt_key].format(info=info)}],
        temperature=0.7,
        max_tokens=3000,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta



    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        from openai import OpenAI
        self._client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        self.model = model

    def generate(self, doc_type: str, info: str) -> str:
        """Generate document text (blocking)."""
        prompt = _PROMPTS.get(doc_type, _PROMPTS["work_summary"])
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt.format(info=info)}],
            temperature=0.7,
            max_tokens=3000,
        )
        return resp.choices[0].message.content or ""

    def generate_stream(self, doc_type: str, info: str) -> Generator[str, None, None]:
        """Generate document text as streaming chunks."""
        prompt = _PROMPTS.get(doc_type, _PROMPTS["work_summary"])
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt.format(info=info)}],
            temperature=0.7,
            max_tokens=3000,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


def build_work_summary_info(applicant: dict, projects: list[dict]) -> str:
    """Assemble context string for work summary from DB records."""
    lines = [
        f"姓名：{applicant.get('name', '')}",
        f"工作单位：{applicant.get('work_unit', '')}",
        f"学历：{applicant.get('education', '')}，专业：{applicant.get('major', '')}",
        f"现有职称：{applicant.get('current_level', '')}",
        f"申报级别：{projects[0].get('apply_level', '') if projects else ''}",
        f"申报行业：{projects[0].get('industry', '') if projects else ''}",
        "",
        "参与的主要工程项目：",
    ]
    for i, p in enumerate(projects[:5], 1):
        name = p.get("project_name") or f"项目{i}"
        scale = p.get("scale") or ""
        lines.append(f"  {i}. {name} （{scale}）")
    note = applicant.get("note") or ""
    if note:
        lines.append(f"\n补充信息：{note}")
    return "\n".join(lines)


def build_masterwork_info(project: dict, achievement: dict | None = None) -> str:
    lines = [
        f"工程名称：{project.get('project_name', '（未填写）')}",
        f"工程规模：{project.get('scale') or '（未判断）'}",
        f"行业专业：{project.get('industry', '')}",
        f"申报级别：{project.get('apply_level', '')}",
    ]
    if achievement:
        lines += [
            f"申报人担任角色：{achievement.get('role', '')}",
            f"工程地点：{achievement.get('location', '')}",
            f"开工日期：{achievement.get('start_date', '')}",
            f"竣工日期：{achievement.get('end_date', '')}",
            f"补充说明：{achievement.get('description', '')}",
        ]
    note = project.get("note") or ""
    if note:
        lines.append(f"项目备注：{note}")
    return "\n".join(lines)


def build_achievement_info(achievement: dict) -> str:
    return "\n".join([
        f"项目名称：{achievement.get('title', '')}",
        f"担任角色：{achievement.get('role', '')}",
        f"工程规模：{achievement.get('scale', '')}",
        f"工程地点：{achievement.get('location', '')}",
        f"起止时间：{achievement.get('start_date', '')} 至 {achievement.get('end_date', '')}",
        f"补充描述：{achievement.get('description', '')}",
    ])
