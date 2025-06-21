import sys
import os
import logging
import json
from core import fetch, info, analyze, render

# 读取日志级别环境变量，默认 INFO
LOGGER_LEVEL = os.getenv("LOGGER_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOGGER_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# 读取 LLM 提供方环境变量，默认 openai，可设置为 deepseek
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek").lower()

def main():
    if len(sys.argv) != 2:
        logger.warning("Usage: uv run main.py <YouTube URL>")
        sys.exit(0)

    url = sys.argv[1]
    logger.info(f"🚀 分析视频: {url}")

    fetch(url)
    info_result = info(url)
    analyze_result = analyze(url, provider=LLM_PROVIDER)

    logger.info(f"Info Result: {json.dumps(info_result, indent=2, ensure_ascii=False)}")
    logger.info(f"Analyze Result: {json.dumps(analyze_result, indent=2, ensure_ascii=False)}")

    output = render(info_result, analyze_result, provider=LLM_PROVIDER)
    print(output)

if __name__ == "__main__":
    main()
