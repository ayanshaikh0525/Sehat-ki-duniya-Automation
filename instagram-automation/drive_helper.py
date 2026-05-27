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
# LIST FILES IN FOLDER
# ==========================================

def list_files(folder_id):

    query = f"'{folder_id}' in parents and trashed=false"

    return drive.ListFile(
        {'q': query}
    ).GetList()


# ==========================================
# FIND SUBFOLDER
# ==========================================

def get_subfolder(parent_folder_id, folder_name):

    query = (
        f"'{parent_folder_id}' in parents "
        f"and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )

    folders = drive.ListFile(
        {'q': query}
    ).GetList()

    for folder in folders:

        if folder['title'].lower() == folder_name.lower():
            return folder

    return None


# ==========================================
# GET TEXT FILE CONTENT
# ==========================================

def get_text_content(file):

    return file.GetContentString()