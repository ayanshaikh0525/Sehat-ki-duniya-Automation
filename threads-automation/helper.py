# ==========================================
# HELPER FUNCTION
# READ TEXT FILE FROM GOOGLE DRIVE FOLDER
# ==========================================

def read_text_file_from_drive_folder(drive, folder_id, target_filename):

    file_list = drive.ListFile({
        'q': f"'{folder_id}' in parents and trashed=false"
    }).GetList()

    for file in file_list:

        filename = file["title"]

        if filename == target_filename:

            content = file.GetContentString()

            return content.strip()

    raise Exception(f"{target_filename} not found in folder {folder_id}")
