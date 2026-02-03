import os
import json
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

def fetch_image_metadata(folder_id:str, retries:int = 3) -> list[dict]:
    """Fetches file metadata from a Google Drive folder based on a query.

    Args:
        folder_id (str): The ID of the Google Drive folder.
        retries (int): Number of retries in case of failure.

    Returns:
        list[dict]: A list of file metadata dictionaries.
    """

    SCOPES = ['https://www.googleapis.com/auth/drive']
    GOOGLE_CREDENTIALS_STR = os.getenv('GOOGLE_CREDENTIALS')
    if not GOOGLE_CREDENTIALS_STR:
        # IF NO CREDS, RETURN NONE
        print("No Google credentials found in environment variables.")
        return
    
    # CREDS FILE FOUND, PROCEED
    GOOGLE_CREDENTIALS_STR = GOOGLE_CREDENTIALS_STR.replace("\'", "\"")
    try:
        GOOGLE_CREDENTIALS_JSON = json.loads(GOOGLE_CREDENTIALS_STR)
    except:
        print("Failed to parse Google credentials JSON.")
        return
    creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS_JSON, SCOPES)

    # BUILD THE SERVICE OBJECT.
    service = build('drive', 'v3', credentials=creds)

    # GET LIST OF FILE METADATA FROM CORRECT FOLDER
    files_metadata: list[dict] = []
    next_page_token = None
    failure_number = 0
    while True and failure_number < retries:
        try:
            query = f"mimeType='image/png' and parents = '{folder_id}'"
            file_service = service.files()
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