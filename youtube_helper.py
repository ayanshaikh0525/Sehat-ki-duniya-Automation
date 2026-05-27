import pickle

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_youtube_service():
    with open("auth/token.pickle", "rb") as token:
        creds = pickle.load(token)

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