import json
import os
from datetime import datetime

from drive_helper import download_video
from youtube_helper import upload_video

TEMP_VIDEO = "temp/video.mp4"

os.makedirs("temp", exist_ok=True)

# Load videos
with open("videos.json", "r") as f:
    videos = json.load(f)

# Find next pending YouTube upload
video_data = next(
    (
        video for video in videos
        if not video["platforms"]["youtube"]["uploaded"]
    ),
    None
)

if video_data is None:
    print("No pending YouTube uploads")
    raise SystemExit

print(f'Selected: {video_data["unique_key"]}')

# Read YouTube metadata files
youtube_meta = video_data["meta_folders"]["youtube"]

title_path = os.path.join(youtube_meta, "title.txt")
description_path = os.path.join(youtube_meta, "description.txt")
hashtags_path = os.path.join(youtube_meta, "hashtags.txt")

with open(title_path, "r", encoding="utf-8") as f:
    title = f.read().strip()

with open(description_path, "r", encoding="utf-8") as f:
    description = f.read().strip()

with open(hashtags_path, "r", encoding="utf-8") as f:
    hashtags = f.read().strip()

final_description = f"{description}\n\n{hashtags}"

# Download video
print("Downloading video from Drive...")

download_video(
    video_data["drive_file_id"],
    TEMP_VIDEO
)

# Upload
print("Uploading to YouTube...")

video_id = upload_video(
    TEMP_VIDEO,
    title,
    final_description
)

print(f"Uploaded successfully: {video_id}")

# Update tracking
video_data["platforms"]["youtube"]["uploaded"] = True

video_data["platforms"]["youtube"]["video_id"] = video_id

video_data["platforms"]["youtube"]["uploaded_at"] = (
    datetime.utcnow().isoformat()
)

video_data["platforms"]["youtube"]["error"] = ""

video_data["workflow"]["updated_at"] = (
    datetime.utcnow().isoformat()
)

# Save updated JSON
with open("videos.json", "w") as f:
    json.dump(videos, f, indent=2)

# Cleanup
if os.path.exists(TEMP_VIDEO):
    os.remove(TEMP_VIDEO)

print("Workflow completed")