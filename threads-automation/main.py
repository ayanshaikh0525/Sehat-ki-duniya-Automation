import json
import requests
import time
import os
import random
from datetime import datetime
from helper import read_text_file_from_drive_folder
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import json


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
# CONFIG
# ==========================================

ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

MASTER_JSON_PATH = "../videos_master.json"

# ==========================================
# LOAD MASTER JSON
# ==========================================

with open(MASTER_JSON_PATH, "r", encoding="utf-8") as f:
    videos = json.load(f)

# ==========================================
# FILTER NON-UPLOADED THREADS VIDEOS
# ==========================================

pending_videos = []

for video in videos:

    threads_data = video.get("platforms", {}).get("threads", {})

    if not threads_data.get("uploaded", False):
        pending_videos.append(video)

# ==========================================
# EXIT IF NOTHING TO UPLOAD
# ==========================================

if len(pending_videos) == 0:
    print("No pending Threads uploads found")
    exit()

# ==========================================
# SHUFFLE VIDEOS
# ==========================================

random.shuffle(pending_videos)

# ==========================================
# PICK RANDOM VIDEO
# ==========================================

data = pending_videos[0]

print(f"\nSelected Video ID: {data['id']}")
print(f"Folder: {data['folder_name']}")

# ==========================================
# GENERATE GOOGLE DRIVE VIDEO URL
# ==========================================

file_id = data["google_drive"]["video_file_id"]

video_url = f"https://drive.google.com/uc?id={file_id}&export=download"

print(f"\nVideo URL:")
print(video_url)

# ==========================================
# READ THREADS CONTENT
# ==========================================

# ==========================================
# THREADS FOLDER ID
# ==========================================

threads_folder_id = data["meta_folders"]["threads"]["folder_id"]

# ==========================================
# READ CONTENT FILES
# ==========================================

post_text = read_text_file_from_drive_folder(
    drive,
    threads_folder_id,
    "post.txt"
)

question_text = read_text_file_from_drive_folder(
    drive,
    threads_folder_id,
    "question.txt"
)

# ==========================================
# FINAL CAPTION
# ==========================================

caption = f"{post_text}\n\n{question_text}"

print("\nCAPTION:")
print(caption)

# ==========================================
# CREATE THREAD CONTAINER
# ==========================================

create_url = "https://graph.threads.net/v1.0/me/threads"

payload = {
    "media_type": "VIDEO",
    "video_url": video_url,
    "text": caption
}

print("\nCreating Threads container...")

response = requests.post(
    create_url,
    data=payload,
    params={
        "access_token": ACCESS_TOKEN
    }
)

result = response.json()

print("\nCREATE RESPONSE:")
print(result)

# ==========================================
# HANDLE CREATE ERROR
# ==========================================

if "id" not in result:

    data["platforms"]["threads"]["error"] = str(result)

    data["workflow"]["updated_at"] = datetime.utcnow().isoformat()

    with open(MASTER_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2)

    raise Exception("Failed to create Threads container")

creation_id = result["id"]

print(f"\nCreation ID: {creation_id}")

# ==========================================
# WAIT FOR VIDEO PROCESSING
# ==========================================

print("\nWaiting for video processing...")

time.sleep(25)

# ==========================================
# PUBLISH THREAD
# ==========================================

publish_url = "https://graph.threads.net/v1.0/me/threads_publish"

print("\nPublishing thread...")

publish_response = requests.post(
    publish_url,
    data={
        "creation_id": creation_id
    },
    params={
        "access_token": ACCESS_TOKEN
    }
)

publish_result = publish_response.json()

print("\nPUBLISH RESPONSE:")
print(publish_result)

# ==========================================
# UPDATE JSON STATUS
# ==========================================

if "id" in publish_result:

    data["platforms"]["threads"]["uploaded"] = True
    data["platforms"]["threads"]["post_id"] = publish_result["id"]
    data["platforms"]["threads"]["uploaded_at"] = datetime.utcnow().isoformat()
    data["platforms"]["threads"]["error"] = ""

    data["workflow"]["status"] = "threads_uploaded"

    print("\nThreads upload successful!")

else:

    data["platforms"]["threads"]["error"] = str(publish_result)

    print("\nThreads upload failed!")

# ==========================================
# UPDATE WORKFLOW METADATA
# ==========================================

data["workflow"]["updated_at"] = datetime.utcnow().isoformat()

# ==========================================
# SAVE UPDATED MASTER JSON
# ==========================================

with open(MASTER_JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(videos, f, indent=2)

print("\nmaster.json updated successfully")
