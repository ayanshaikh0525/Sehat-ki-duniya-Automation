import os
import json
import random
import requests
import re
from datetime import datetime

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# FACEBOOK ENV
# ==========================================

PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

# ==========================================
# GOOGLE AUTH
# ==========================================

with open("auth/service_account.json", "r") as f:
    service_account_info = json.load(f)

scopes = [
    "https://www.googleapis.com/auth/drive.readonly"
]

credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    service_account_info,
    scopes
)

gauth = GoogleAuth()
gauth.credentials = credentials

drive = GoogleDrive(gauth)

# ==========================================
# LOAD JSON
# ==========================================

with open("../videos_master.json", "r", encoding="utf-8") as f:
    videos = json.load(f)

# ==========================================
# FILTER FACEBOOK UNUPLOADED
# ==========================================

unused_videos = [
    v for v in videos
    if not v["platforms"]["facebook"]["uploaded"]
]

if not unused_videos:
    print("No Facebook videos left")
    exit()

# ==========================================
# RANDOM VIDEO
# ==========================================

video = random.choice(unused_videos)

print(f"Selected Video ID: {video['id']}")

# ==========================================
# VIDEO DOWNLOAD
# ==========================================

video_file_id = video["google_drive"]["video_file_id"]

video_path = "video.mp4"

print("Downloading video from Google Drive...")

video_file = drive.CreateFile({
    'id': video_file_id
})

video_file.GetContentFile(video_path)

print("Video downloaded")

# ==========================================
# FACEBOOK FOLDER
# ==========================================

fb_folder_id = video["meta_folders"]["facebook"]["folder_id"]

# ==========================================
# FUNCTION TO READ TXT FILE
# ==========================================

def read_txt_file(folder_id, filename):

    query = (
        f"'{folder_id}' in parents and "
        f"title='{filename}' and trashed=false"
    )

    file_list = drive.ListFile({
        'q': query
    }).GetList()

    if not file_list:
        raise Exception(f"{filename} not found")

    file = file_list[0]

    return file.GetContentString().strip()

# ==========================================
# READ META FILES
# ==========================================

print("Reading metadata files...")

hook = read_txt_file(
    fb_folder_id,
    "hooks.txt"
)

hook = re.sub(
    r'^\s*\d+[\.\)]\s*',
    '',
    hook
).strip()

caption = read_txt_file(
    fb_folder_id,
    "caption.txt"
)

hashtags = read_txt_file(
    fb_folder_id,
    "hashtags.txt"
)

# ==========================================
# FINAL CAPTION
# ==========================================

final_caption = (
    f"{hook}\n\n"
    f"{caption}\n\n"
    f"{hashtags}"
)

print("\n===== FINAL CAPTION =====\n")
print(final_caption)

# ==========================================
# FACEBOOK UPLOAD
# ==========================================

url = (
    f"https://graph-video.facebook.com/"
    f"v23.0/{PAGE_ID}/videos"
)

files = {
    "source": open(video_path, "rb")
}

data = {
    "access_token": ACCESS_TOKEN,
    "description": final_caption,
    "title": video["unique_key"]
}

print("\nUploading to Facebook...")

response = requests.post(
    url,
    files=files,
    data=data
)

response_json = response.json()

print(response_json)

# ==========================================
# SUCCESS
# ==========================================

if "id" in response_json:

    video["platforms"]["facebook"]["uploaded"] = True

    video["platforms"]["facebook"]["post_id"] = (
        response_json["id"]
    )

    video["platforms"]["facebook"]["uploaded_at"] = (
        datetime.now().isoformat()
    )

    video["platforms"]["facebook"]["error"] = ""

    video["workflow"]["status"] = (
        "facebook_uploaded"
    )

    video["workflow"]["updated_at"] = (
        datetime.now().isoformat()
    )

    print("\nFacebook upload success")

# ==========================================
# FAILURE
# ==========================================

else:

    error_message = (
        response_json
        .get("error", {})
        .get("message", "Unknown error")
    )

    video["platforms"]["facebook"]["error"] = (
        error_message
    )

    print("\nFacebook upload failed")

# ==========================================
# SAVE JSON
# ==========================================

with open("../videos_master.json", "w", encoding="utf-8") as f:
    json.dump(videos, f, indent=2)

print("\nvideo_master.json updated")