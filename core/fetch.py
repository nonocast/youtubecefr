import os
import requests
import logging
from urllib.parse import urlparse, parse_qs
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url: str) -> str:
    """从 YouTube URL 中提取视频 ID"""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return query.get("v", [None])[0]

def save_as_vtt(transcript_list, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, entry in enumerate(transcript_list):
            start = format_timestamp(entry['start'])
            end = format_timestamp(entry['start'] + entry['duration'])
            text = entry['text'].replace('\n', ' ').strip()
            f.write(f"{start} --> {end}\n{text}\n\n")

    # 自动生成 play.sh 脚本
    video_dir = os.path.dirname(output_path)
    video_id = os.path.basename(video_dir)
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    play_script_path = os.path.join(video_dir, "play.sh")

    with open(play_script_path, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write(f'mpv "{video_url}" --sub-file="subtitles.vtt"\n')

    os.chmod(play_script_path, 0o755)

def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"

def download_transcript(video_url: str, base_dir: str = "videos"):
    video_id = extract_video_id(video_url)
    output_dir = os.path.join(base_dir, video_id)
    os.makedirs(output_dir, exist_ok=True)

    path_plain = os.path.join(output_dir, "transcript_plain.txt")
    path_time = os.path.join(output_dir, "transcript_with_time.txt")
    if os.path.exists(path_plain) and os.path.exists(path_time):
        logging.debug("⏭️ 已存在字幕文件，跳过下载")
        return

    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])

    with open(path_time, "w") as f:
        for entry in transcript_list:
            f.write(f"{entry['start']:.2f}s: {entry['text']}\n")

    with open(path_plain, "w") as f:
        buffer = ""
        for entry in transcript_list:
            text = entry['text'].strip()
            if text and not text.startswith("["):
                buffer += " " + text
                if text.endswith((".", "!", "?")):
                    f.write(buffer.strip() + "\n")
                    buffer = ""
        if buffer.strip():
            f.write(buffer.strip() + "\n")

    save_as_vtt(transcript_list, os.path.join(output_dir, "subtitles.vtt"))

    logging.info(f"✅ 字幕已保存至 {path_plain} 和 {path_time}")

def download_english_audio(video_url: str, base_dir: str = "videos"):
    """下载英文原声音频，保存为 audio.m4a"""
    video_id = extract_video_id(video_url)
    output_dir = os.path.join(base_dir, video_id)
    os.makedirs(output_dir, exist_ok=True)

    audio_path = os.path.join(output_dir, "audio.m4a")
    if os.path.exists(audio_path):
        logging.debug("⏭️ 已存在音频文件，跳过下载")
        return

    ydl_opts = {"quiet": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        english_format = None
        for fmt in info["formats"]:
            if (
                fmt.get("vcodec") == "none"
                and fmt.get("acodec", "").startswith("mp4a")
                and fmt.get("language") == "en-US"
                and "original" in fmt.get("format_note", "").lower()
            ):
                english_format = fmt["format_id"]
                break

    if not english_format:
        logging.warning("❌ 找不到英文原声音频格式")
        return

    logging.debug(f"🎯 下载音频 format: {english_format}")
    ydl_opts = {
        "format": english_format,
        "outtmpl": os.path.join(output_dir, "audio.%(ext)s"),
        "quiet": False,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    logging.info(f"✅ 音频保存为: {audio_path}")

def download_thumbnail(video_url: str, base_dir: str = "videos"):
    """下载封面图，保存为 cover.jpg"""
    video_id = extract_video_id(video_url)
    output_path = os.path.join(base_dir, video_id, "cover.jpg")
    if os.path.exists(output_path):
        logging.debug("⏭️ 已存在封面图，跳过下载")
        return

    with YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(video_url, download=False)
        thumbnail_url = info.get("thumbnail")
        if not thumbnail_url:
            logging.warning("❌ 未找到缩略图 URL")
            return

    response = requests.get(thumbnail_url)
    if not response.ok:
        logging.warning("❌ 下载封面失败")
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)

    logging.info(f"✅ 封面图保存为: {output_path}")

def fetch(video_url: str, base_dir: str = "videos"):
    """统一下载 transcript、audio、thumbnail"""
    download_transcript(video_url, base_dir)
    # download_english_audio(video_url, base_dir)
    # download_thumbnail(video_url, base_dir)
