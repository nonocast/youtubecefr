import json
import logging
import os
import requests
import humanize
from openai import OpenAI
from datetime import datetime, timezone
from dateutil import parser 

logger = logging.getLogger(__name__)

def time_ago(published_at_str: str) -> str:
    dt = parser.parse(published_at_str).replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return humanize.naturaltime(now - dt)

def build_render_prompt(info: dict, analysis: dict) -> str:
    json_input = json.dumps({
        "title": info["title"],
        "channel_title": info["channel_title"],
        "published_at": time_ago(info["published_at"]),
        "view_count": info["view_count"],
        "like_count": info["like_count"],
        "comment_count": info["comment_count"],
        "duration_minutes": analysis.get("duration", 0),
        "category": analysis.get("category"),
        "keywords": analysis.get("keywords", []),
        "summary": analysis.get("summary", ""),
        "kPM": analysis.get("kPM"),
        "CEFR": analysis.get("CEFR")
    }, indent=2, ensure_ascii=False)

    return f"""
你是一个语言学习助手，请将以下 JSON 格式的视频信息，按照下面固定模板渲染为适合命令行显示的格式：

标题: {{title}}
摘要: {{summary}}  
作者: {{channel_title}}
发布时间: {{published_at}}
播放: {{view_count}} ｜👍 {{like_count}} ｜💬 {{comment_count}}  
时长: {{duration_minutes}} 分钟  
分类: {{category}}  
关键词: {{keywords}}（逗号分隔）  
语速: {{kPM}} WPM（请补充是否语速适中）  
等级: {{CEFR}}（请补充适合什么水平学习者）

请严格按照以上格式输出，不要添加任何解释或 Markdown 代码块。
以下是视频信息 JSON：
{json_input}
""".strip()


def render_with_openai(prompt: str) -> str:
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一个语言学习助手，请根据模板和视频数据返回内容。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def render_with_deepseek(prompt: str) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个语言学习助手，请根据模板和视频数据返回内容。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def render_with_llm(info: dict, analysis: dict, provider: str = "openai") -> str:
    prompt = build_render_prompt(info, analysis)
    if provider == "deepseek":
        logger.info("使用 DeepSeek 进行渲染")
        return render_with_deepseek(prompt)
    else:    
        logger.info("使用 OpenAI 进行渲染")
        return render_with_openai(prompt)


def render(info: dict, analysis: dict, provider: str = "deepseek") -> str:
    return render_with_llm(info, analysis, provider=provider)
