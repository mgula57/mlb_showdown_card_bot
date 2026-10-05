import os
import json
import threading
from typing import Optional
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


class GoogleDriveClient:
    """Process-wide Google Drive access.

    Credentials are parsed once and shared, so the OAuth access token they hold is
    reused across requests instead of being re-fetched for every card.
    """

    SCOPES = ['https://www.googleapis.com/auth/drive']
    _credentials: Optional[ServiceAccountCredentials] = None
    _lock = threading.Lock()

    @classmethod
    def credentials(cls) -> Optional[ServiceAccountCredentials]:
        """Shared service account credentials, or None if GOOGLE_CREDENTIALS is missing/invalid."""
        if cls._credentials is None:
            with cls._lock:
                if cls._credentials is None:
                    cls._credentials = cls._load_credentials()
        return cls._credentials

    @classmethod
    def files_service(cls):
        """New Drive files resource built from the shared credentials.

        httplib2 is not thread-safe, so each thread needs its own resource. Building one
        is cheap (a few ms) and reuses the shared credentials' access token.

        Returns:
          Drive v3 files resource, or None if there are no valid credentials.
        """
        creds = cls.credentials()
        if creds is None:
            return None
        return build('drive', 'v3', credentials=creds).files()

    @classmethod
    def _load_credentials(cls) -> Optional[ServiceAccountCredentials]:
        GOOGLE_CREDENTIALS_STR = os.getenv('GOOGLE_CREDENTIALS')
        if not GOOGLE_CREDENTIALS_STR:
            return None
        GOOGLE_CREDENTIALS_STR = GOOGLE_CREDENTIALS_STR.replace("\'", "\"")
        try:
            GOOGLE_CREDENTIALS_JSON = json.loads(GOOGLE_CREDENTIALS_STR)
        except:
            return None
        return ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS_JSON, cls.SCOPES)


def fetch_image_metadata(folder_id:str, retries:int = 3) -> list[dict]:
    """Fetches file metadata from a Google Drive folder based on a query.

    Args:
        folder_id (str): The ID of the Google Drive folder.
        retries (int): Number of retries in case of failure.

    Returns:
        list[dict]: A list of file metadata dictionaries.
    """

    file_service = GoogleDriveClient.files_service()
    if file_service is None:
        print("No valid Google credentials found in environment variables.")
        return

    # GET LIST OF FILE METADATA FROM CORRECT FOLDER
    files_metadata: list[dict] = []
    next_page_token = None
    failure_number = 0
    while True and failure_number < retries:
        try:
            query = f"mimeType='image/png' and parents = '{folder_id}'"
            # Build request parameters conditionally
            request_params = {
                'q': query,
                'pageSize': 1000,
                'fields': "nextPageToken, files(id, name, modifiedTime, createdTime)",
                'orderBy': 'modifiedTime asc'
            }
            # Only include pageToken if it's not None
            if next_page_token:
                request_params['pageToken'] = next_page_token

            # Hit the API
            response = file_service.list(**request_params).execute()

            # Get file and next page token
            new_files_list = response.get('files', [])
            next_page_token = response.get('nextPageToken', None)
            files_metadata.extend(new_files_list)
            if not next_page_token:
                break
        except Exception as e:
            print("Error fetching file metadata from Google Drive:", e)
            failure_number += 1

    return files_metadata
