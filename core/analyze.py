import os
import json
import re
import logging
import requests
from openai import OpenAI
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

def extract_video_id(url: str) -> str:
    query = parse_qs(urlparse(url).query)
    return query.get("v", [None])[0]

def read_transcript_plain(video_id: str, base_dir: str = "videos") -> str:
    path = os.path.join(base_dir, video_id, "transcript_plain.txt")
    if not os.path.exists(path):
        logging.error("❌ 找不到 transcript_plain.txt")
        return ""
    with open(path, "r") as f:
        return f.read().strip()

def read_transcript_duration(video_id: str, base_dir: str = "videos") -> float:
    path = os.path.join(base_dir, video_id, "transcript_with_time.txt")
    if not os.path.exists(path):
        logging.error("❌ 找不到 transcript_with_time.txt")
        return 0.0
    try:
        last_line = list(open(path))[-1]
        last_time = float(last_line.split("s:")[0].strip().replace("s", ""))
        return round(last_time / 60, 2)
    except Exception as e:
        logging.error(f"❌ 解析时长失败: {e}")
        return 0.0

def build_prompt(text: str, duration: float) -> str:
    return f"""
You are an English language level expert.

Please analyze the following English transcript from a YouTube vlog and return a JSON result with the following format:

{{
    "category": 请根据transcript内容判断其类别（如 vlog / interview / documentary / etc.）,
    "keywords": 请提取出5个关键词（英文）, 后续用来做关键词搜索,
    "summary": 请用中文总结内容, 让人快速了解视频大意,
    "duration": 请用分钟表示视频时长 (保留小数后一位),
    "kPM": 根据duration和transcript计算每分钟词数（整数）,
    "CEFR": 请根据内容判断其 CEFR 语言等级（如 A1 / A2 / B1 / B2 / C1 / C2）,
    "justification": 请用中文解释为什么你认为这个视频属于这个 CEFR 语言等级
}}

Transcript duration: {duration} minutes

Transcript:
{text}
""".strip()

def analyze_with_openai(prompt: str) -> dict:
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一个语言学习助手，专注于判断英语材料的CEFR语言等级"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content.strip()

    match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        content = match.group(1)
    elif content.startswith("```"):
        content = content.removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(content)
    except Exception as e:
        logging.error(f"❌ 无法解析 JSON: {e}")
        return {}

def analyze_with_deepseek(prompt: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个语言学习助手，专注于判断英语材料的CEFR语言等级"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
    }

    response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload)
    content = response.json()["choices"][0]["message"]["content"].strip()

    match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        content = match.group(1)
    elif content.startswith("```"):
        content = content.removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(content)
    except Exception as e:
        logging.error(f"❌ 无法解析 JSON: {e}")
        return {}

def analyze(video_url: str, provider: str = "deepseek") -> dict:
    video_id = extract_video_id(video_url)
    text = read_transcript_plain(video_id)
    duration = read_transcript_duration(video_id)
    prompt = build_prompt(text, duration)

    if not text or not duration:
        logging.warning("⚠️ 跳过分析，字幕或时长缺失")
        return {}

    if provider == "deepseek":
        logger.info("使用 DeepSeek 进行分析")
        return analyze_with_deepseek(prompt)
    else:
        logger.info("使用 OpenAI 进行分析")
        return analyze_with_openai(prompt)
