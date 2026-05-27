import json
import random
import time
import requests
from datetime import datetime
import re
from config import ACCESS_TOKEN, IG_USER_ID

from drive_helper import (
    list_files,
    get_subfolder,
    get_text_content
)


# ==========================================
# LOAD VIDEOS JSON
# ==========================================

with open("../videos_master.json", "r", encoding="utf-8") as f:
    videos = json.load(f)


# ==========================================
# GET PENDING INSTAGRAM VIDEOS
# ==========================================

pending_videos = [
    v for v in videos
    if not v["platforms"]["instagram"]["uploaded"]
]

random.shuffle(pending_videos)

video_data = pending_videos[0] if pending_videos else None


if not video_data:
    print("No pending Instagram uploads.")
    exit()


# ==========================================
# ROOT FOLDER
# ==========================================

root_folder_id = video_data["google_drive"]["root_folder_id"]

print(f"Processing: {video_data['unique_key']}")


# ==========================================
# FIND VIDEO FILE
# ==========================================

root_files = list_files(root_folder_id)

video_file = None

for file in root_files:

    filename = file["title"].lower()

    if filename.endswith(".mp4"):

        video_file = file
        break


if not video_file:

    print("Video file not found.")

    video_data["platforms"]["instagram"]["error"] = "Video file missing"

    with open("../videos_master.json", "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

    exit()


video_file_id = video_file["id"]

video_url = f"https://drive.google.com/uc?id={video_file_id}"

print("Video Found:", video_file["title"])


# ==========================================
# FIND INSTAGRAM METADATA FOLDER
# ==========================================

instagram_folder = get_subfolder(
    root_folder_id,
    "instagram"
)


if not instagram_folder:

    print("Instagram metadata folder missing.")

    video_data["platforms"]["instagram"]["error"] = "Instagram folder missing"

    with open("../videos_master.json", "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

    exit()


print("Instagram Folder Found")


# ==========================================
# READ INSTAGRAM METADATA FILES
# ==========================================

instagram_files = list_files(instagram_folder["id"])

caption = ""
hashtags = ""
hook = ""

for file in instagram_files:

    filename = file["title"].lower()

    if filename == "caption.txt":

        caption = get_text_content(file).strip()

    elif filename == "hashtags.txt":

        hashtags = get_text_content(file).strip()

    elif filename == "hooks.txt":
        hook = get_text_content(file).strip()
        hook = re.sub(
                    r'^\s*\d+[\.\)]\s*',
                    '',
                    hook
                ).strip()


# ==========================================
# FALLBACKS
# ==========================================

if not caption:
    caption = video_data["unique_key"].replace("_", " ")

final_caption = f"{hook}\n{caption}\n\n{hashtags}".strip()

print("Caption Ready")


# ==========================================
# CREATE INSTAGRAM MEDIA CONTAINER
# ==========================================

create_url = f"https://graph.facebook.com/v23.0/{IG_USER_ID}/media"

payload = {
    "media_type": "REELS",
    "video_url": video_url,
    "caption": final_caption,
    "access_token": ACCESS_TOKEN
}

print("Creating Instagram media container...")

response = requests.post(
    create_url,
    data=payload
)

result = response.json()

print("CREATE RESPONSE:")
print(result)


# ==========================================
# HANDLE CREATE ERRORS
# ==========================================

if "id" not in result:

    video_data["platforms"]["instagram"]["error"] = str(result)

    video_data["workflow"]["updated_at"] = datetime.utcnow().isoformat()

    with open("../videos_master.json", "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

    print("Failed creating media container.")

    exit()


creation_id = result["id"]

print(f"Container Created: {creation_id}")


# ==========================================
# WAIT FOR INSTAGRAM PROCESSING
# ==========================================

print("Waiting for Instagram processing...")

time.sleep(45)


# ==========================================
# PUBLISH INSTAGRAM REEL
# ==========================================

publish_url = f"https://graph.facebook.com/v23.0/{IG_USER_ID}/media_publish"

publish_payload = {
    "creation_id": creation_id,
    "access_token": ACCESS_TOKEN
}

print("Publishing Reel...")

publish_response = requests.post(
    publish_url,
    data=publish_payload
)

publish_result = publish_response.json()

print("PUBLISH RESPONSE:")
print(publish_result)


# ==========================================
# SUCCESS
# ==========================================

if "id" in publish_result:

    print("Instagram Reel Uploaded Successfully!")

    video_data["platforms"]["instagram"]["uploaded"] = True

    video_data["platforms"]["instagram"]["post_id"] = publish_result["id"]

    video_data["platforms"]["instagram"]["uploaded_at"] = datetime.utcnow().isoformat()

    video_data["platforms"]["instagram"]["error"] = ""

    video_data["workflow"]["status"] = "instagram_uploaded"

    video_data["workflow"]["updated_at"] = datetime.utcnow().isoformat()

    with open("videos.json", "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

else:

    print("Publish Failed")

    video_data["platforms"]["instagram"]["error"] = str(publish_result)

    video_data["workflow"]["updated_at"] = datetime.utcnow().isoformat()

    with open("../videos_master.json", "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)