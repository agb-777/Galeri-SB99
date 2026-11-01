import json
import sys
from datetime import datetime

path = sys.argv[1] if len(sys.argv) > 1 else "url.json"

with open(path, encoding="utf-8") as file:
    data = json.load(file)

videos = data["videos"] if isinstance(data, dict) else data
now = datetime.now().astimezone().isoformat(timespec="minutes")
stamped = 0

for video in videos:
    if isinstance(video, dict) and not video.get("date"):
        video["date"] = now
        stamped += 1

with open(path, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)
    file.write("\n")

print(f"{stamped} video(s) stamped with {now}")
