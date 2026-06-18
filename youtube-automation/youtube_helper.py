import pickle

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def get_youtube_service():
    creds = Credentials.from_authorized_user_file(
        "auth/token.json",
        ["https://www.googleapis.com/auth/youtube.upload"]
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

        with open("auth/token.json", "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

def upload_video(video_path, title, description):
    youtube = get_youtube_service()

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=MediaFileUpload(
            video_path,
            resumable=True
        )
    )

    response = None

    while response is None:
        status, response = request.next_chunk()

        if status:
            print(f'Upload {int(status.progress() * 100)}%')

    return response["id"]
