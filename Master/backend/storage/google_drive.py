import io

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from config import GOOGLE_SERVICE_ACCOUNT_FILE, GOOGLE_DRIVE_FOLDER_ID
from storage.base import StorageBackend

SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleDriveStorage(StorageBackend):
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        self._service = build("drive", "v3", credentials=credentials, cache_discovery=False)

    def upload(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=content_type, resumable=True)
        metadata = {"name": filename, "parents": [GOOGLE_DRIVE_FOLDER_ID]}
        request = self._service.files().create(body=metadata, media_body=media, fields="id")

        response = None
        while response is None:
            _, response = request.next_chunk()
        file_id = response["id"]

        # Public link-viewable so workers/Streamlit can fetch it without a
        # separate OAuth flow. Only do this for non-sensitive task data —
        # anyone with the link can read the file.
        self._service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

        return f"https://drive.google.com/uc?id={file_id}&export=download"

    def delete(self, reference: str) -> None:
        file_id = reference.split("id=")[1].split("&")[0]
        self._service.files().delete(fileId=file_id).execute()
