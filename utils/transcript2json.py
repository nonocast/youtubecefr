import json
from pathlib import Path

# 设置视频 ID 和路径
video_id = "74i7daegNZE"
base_dir = Path("videos") / video_id

# 输入输出路径
input_path = base_dir / "transcript_plain.txt"
output_path = base_dir / "transcript.json"

# 标题（可手动调整）
title = "Alone but not Lonely // ep. 11 - YouTube"

# 读取段落内容
with input_path.open("r") as f:
    paragraphs = [line.strip() for line in f.readlines() if line.strip()]

# 写入 JSON 文件
data = {
    "title": title,
    "paragraphs": paragraphs
}

with output_path.open("w") as f:
    json.dump(data, f, indent=2)

print(f"✅ Saved: {output_path}")
