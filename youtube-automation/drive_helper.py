import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

SERVICE_ACCOUNT_FILE = 'auth/service_account.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

drive_service = build(
    'drive',
    'v3',
    credentials=credentials
)

def download_file(file_id, output_path):
    request = drive_service.files().get_media(
        fileId=file_id
    )

    fh = io.FileIO(output_path, 'wb')

    downloader = MediaIoBaseDownload(
        fh,
        request
    )

    done = False

    while not done:
        status, done = downloader.next_chunk()

        if status:
            print(
                f'Download {int(status.progress() * 100)}%'
            )

def get_file_content(file_id):
    request = drive_service.files().get_media(
        fileId=file_id
    )

    data = request.execute()

    return data.decode("utf-8")

def get_file_id_by_name(folder_id, filename):
    query = (
        f"'{folder_id}' in parents and "
        f"name='{filename}' and trashed=false"
    )

    results = drive_service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()

    files = results.get('files', [])

    if not files:
        raise Exception(
            f"{filename} not found in folder"
        )

    return files[0]['id']