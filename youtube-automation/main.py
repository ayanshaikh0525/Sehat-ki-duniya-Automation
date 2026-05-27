import json
import os

from drive_helper import download_video
from youtube_helper import upload_video

TEMP_VIDEO = "temp/video.mp4"

os.makedirs("temp", exist_ok=True)

# Load videos
with open("../videos_master.json", "r") as f:
    videos = json.load(f)

# Find next pending video
video_data = next(
    (video for video in videos if not video["platforms"]["youtube"]["uploaded"]),
    None
)

# Exit if nothing pending
if video_data is None:
    print("No pending videos found")
    raise SystemExit

print(f'Selected Video ID: {video_data["id"]}')

# Download video from Google Drive
print("Downloading video from Google Drive...")

download_video(
    video_data["drive_file_id"],
    TEMP_VIDEO
)

# Build description
hashtags = " ".join(video_data["hashtags"])

description = (
    f'{video_data["description"]}\n\n{hashtags}'
)

# Upload to YouTube
print("Uploading to YouTube...")

video_id = upload_video(
    TEMP_VIDEO,
    video_data["title"],
    description
)

print(f'Upload successful: {video_id}')

# Update JSON status
video_data["uploaded"] = True
video_data["youtube_video_id"] = video_id

# Save updated JSON
with open("videos.json", "w") as f:
    json.dump(videos, f, indent=2)

# Cleanup temp file
if os.path.exists(TEMP_VIDEO):
    os.remove(TEMP_VIDEO)

print("videos.json updated successfully")