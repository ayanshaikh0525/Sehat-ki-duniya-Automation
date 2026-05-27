import json
import os
import re
from datetime import datetime
from drive_helper import (
    download_file,
    get_file_content,
    get_file_id_by_name
)

from youtube_helper import upload_video

TEMP_VIDEO = "temp/video.mp4"

os.makedirs("temp", exist_ok=True)

# Load workflow JSON
with open("../videos_master.json", "r", encoding="utf-8") as f:
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

# -----------------------------
# GOOGLE DRIVE IDS
# -----------------------------

video_file_id = (
    video_data["google_drive"]["video_file_id"]
)

youtube_folder_id = (
    video_data["meta_folders"]["youtube"]["folder_id"]
)

# -----------------------------
# FETCH METADATA FILE IDS
# -----------------------------

title_file_id = get_file_id_by_name(
    youtube_folder_id,
    "titles.txt"
)


description_file_id = get_file_id_by_name(
    youtube_folder_id,
    "description.txt"
)

hashtags_file_id = get_file_id_by_name(
    youtube_folder_id,
    "hashtags.txt"
)

# -----------------------------
# READ FILE CONTENTS
# -----------------------------

title = get_file_content(
    title_file_id
).strip()

title = re.sub(
    r'^\s*\d+[\.\)]\s*',
    '',
    title
).strip()

description = get_file_content(
    description_file_id
).strip()

hashtags = get_file_content(
    hashtags_file_id
).strip()

final_description = (
    f"{description}\n\n{hashtags}"
)

# -----------------------------
# DOWNLOAD VIDEO
# -----------------------------

print("Downloading video...")

download_file(
    video_file_id,
    TEMP_VIDEO
)

# -----------------------------
# UPLOAD TO YOUTUBE
# -----------------------------

print("Uploading to YouTube...")

video_id = upload_video(
    TEMP_VIDEO,
    title,
    final_description
)

print(f'Uploaded successfully: {video_id}')

# -----------------------------
# UPDATE JSON STATUS
# -----------------------------

youtube_platform = (
    video_data["platforms"]["youtube"]
)

youtube_platform["uploaded"] = True

youtube_platform["video_id"] = video_id

youtube_platform["uploaded_at"] = (
    datetime.utcnow().isoformat()
)

youtube_platform["error"] = ""

video_data["workflow"]["updated_at"] = (
    datetime.utcnow().isoformat()
)

video_data["workflow"]["status"] = (
    "youtube_uploaded"
)

# -----------------------------
# SAVE UPDATED JSON
# -----------------------------

with open("../videos_master.json", "w", encoding="utf-8") as f:
    json.dump(
        videos,
        f,
        indent=2,
        ensure_ascii=False
    )

# -----------------------------
# CLEANUP
# -----------------------------

if os.path.exists(TEMP_VIDEO):
    os.remove(TEMP_VIDEO)

print("Workflow completed successfully")