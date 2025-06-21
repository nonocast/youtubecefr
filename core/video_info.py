import os
import requests
import logging
from urllib.parse import urlparse, parse_qs

def extract_video_id(url: str) -> str:
    """提取 YouTube 视频 ID"""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("v", [None])[0]

def info(video_url: str) -> dict:
    """通过 YouTube Data API 获取视频基本信息"""
    video_id = extract_video_id(video_url)
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        logging.error("❌ 缺少环境变量 YOUTUBE_API_KEY")
        return {}

    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "id": video_id,
        "part": "snippet,statistics",
        "key": api_key
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        logging.error(f"❌ 获取视频信息失败: {response.text}")
        return {}

    items = response.json().get("items", [])
    if not items:
        logging.error("❌ 无法获取视频数据")
        return {}

    video_data = items[0]
    snippet = video_data["snippet"]
    stats = video_data.get("statistics", {})

    result = {
        "video_id": video_id,
        "url": video_url,
        "title": snippet.get("title"),
        "published_at": snippet.get("publishedAt"),
        "channel_title": snippet.get("channelTitle"),
        "view_count": int(stats.get("viewCount", 0)),
        "like_count": int(stats.get("likeCount", 0)),
        "comment_count": int(stats.get("commentCount", 0)),
    }

    logging.debug(f"📥 获取视频信息: {result}")
    return result
