import os
import re
import json
import threading
from dataclasses import dataclass, field
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials


class GoogleDriveClient:
    """Process-wide Google Drive access.

    Credentials are parsed once and shared, so the OAuth access token they hold is
    reused across requests instead of being re-fetched for every card.
    """

    CREDENTIALS_ENV_VAR = 'GOOGLE_CREDENTIALS'
    SCOPES = ['https://www.googleapis.com/auth/drive']
    _credentials: Optional[ServiceAccountCredentials] = None
    _lock = threading.Lock()

    @classmethod
    def credentials(cls) -> Optional[ServiceAccountCredentials]:
        """Shared service account credentials, or None if the credentials env var is missing/invalid."""
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
    def service_account_email(cls) -> Optional[str]:
        """Email users share folders with, or None if there are no valid credentials."""
        creds = cls.credentials()
        return creds.service_account_email if creds else None

    @classmethod
    def _load_credentials(cls) -> Optional[ServiceAccountCredentials]:
        GOOGLE_CREDENTIALS_STR = os.getenv(cls.CREDENTIALS_ENV_VAR)
        if not GOOGLE_CREDENTIALS_STR:
            return None
        GOOGLE_CREDENTIALS_STR = GOOGLE_CREDENTIALS_STR.replace("\'", "\"")
        try:
            GOOGLE_CREDENTIALS_JSON = json.loads(GOOGLE_CREDENTIALS_STR)
        except:
            return None
        return ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS_JSON, cls.SCOPES)


class UserDriveClient(GoogleDriveClient):
    """Read-only Drive access for folders users share with the bot.

    Separate service account from GoogleDriveClient so a leaked key or bug can't touch
    the bot's own image library, and user traffic doesn't eat into its quota.
    """

    CREDENTIALS_ENV_VAR = 'GOOGLE_USER_DRIVE_CREDENTIALS'
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    # OWN CACHE + LOCK, OTHERWISE THE LOOKUP FALLS THROUGH TO GoogleDriveClient's CREDENTIALS
    _credentials: Optional[ServiceAccountCredentials] = None
    _lock = threading.Lock()


class UserDriveFolderError(Exception):
    """User-facing reason a shared folder can't be used."""


@dataclass
class UserDriveFolderSummary:
    folder_id: str
    name: str
    can_edit: bool
    image_files: list[dict] = field(default_factory=list)
    other_files: list[dict] = field(default_factory=list)


class UserDriveFolder:
    """A user's image folder, shared (Viewer) with the UserDriveClient service account."""

    FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder'
    # SUPPORT FOLDERS INSIDE SHARED DRIVES, NOT JUST "MY DRIVE"
    ALL_DRIVES_PARAMS = {'supportsAllDrives': True}
    ALL_DRIVES_LIST_PARAMS = {'supportsAllDrives': True, 'includeItemsFromAllDrives': True}

    def __init__(self, folder_id_or_url: str):
        self.folder_id = self.parse_folder_id(folder_id_or_url)

    @staticmethod
    def parse_folder_id(folder_id_or_url: str) -> str:
        """Pull the folder id out of a Drive folder URL, or return the id as-is.

        Handles drive.google.com/drive/folders/<id>, .../drive/u/0/folders/<id>, and ?id=<id> links.
        """
        value = (folder_id_or_url or '').strip()
        match = re.search(r'/folders/([\w-]+)', value) or re.search(r'[?&]id=([\w-]+)', value)
        if match:
            return match.group(1)
        if re.fullmatch(r'[\w-]{10,}', value):
            return value
        raise UserDriveFolderError(f"'{folder_id_or_url}' doesn't look like a Google Drive folder link or id.")

    def verify(self) -> UserDriveFolderSummary:
        """Confirm the folder is shared with the bot (read-only) and list its direct children.

        Raises:
          UserDriveFolderError: Folder is missing, not shared, not a folder, or shared with edit access.
        """
        files_service = UserDriveClient.files_service()
        if files_service is None:
            raise UserDriveFolderError(f"No valid {UserDriveClient.CREDENTIALS_ENV_VAR} found in environment variables.")

        try:
            folder = files_service.get(
                fileId=self.folder_id,
                fields='id, name, mimeType, capabilities(canEdit)',
                **self.ALL_DRIVES_PARAMS,
            ).execute()
        except HttpError as err:
            if err.resp.status == 404:
                raise UserDriveFolderError(
                    f"Folder not found. Make sure it's shared with {UserDriveClient.service_account_email()} as a Viewer. "
                    "Work/school accounts may block sharing outside the organization."
                ) from err
            raise UserDriveFolderError(f"Google Drive error ({err.resp.status}): {err}") from err

        if folder.get('mimeType') != self.FOLDER_MIME_TYPE:
            raise UserDriveFolderError(f"'{folder.get('name')}' is a file, not a folder.")

        summary = UserDriveFolderSummary(
            folder_id=self.folder_id,
            name=folder.get('name'),
            can_edit=folder.get('capabilities', {}).get('canEdit', False),
        )
        if summary.can_edit:
            raise UserDriveFolderError(f"'{summary.name}' is shared with edit access. Please share it as Viewer only.")

        for file in self._list_children(files_service):
            is_image = file.get('mimeType', '').startswith('image/')
            (summary.image_files if is_image else summary.other_files).append(file)
        return summary

    def _list_children(self, files_service) -> list[dict]:
        """All non-trashed direct children of the folder (subfolders are not searched)."""
        files: list[dict] = []
        page_token = None
        while True:
            response = files_service.list(
                q=f"'{self.folder_id}' in parents and trashed = false",
                pageSize=1000,
                pageToken=page_token,
                fields='nextPageToken, files(id, name, mimeType, md5Checksum, modifiedTime)',
                **self.ALL_DRIVES_LIST_PARAMS,
            ).execute()
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            if not page_token:
                return files


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
