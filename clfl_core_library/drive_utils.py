from googleapiclient.discovery import build
from .shipment_utils import extract_year_from_shipment
import io
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
import logging

class DriveManager:
    """
    Manages Google Drive Operations for CLFL Shared Drives
    """

    def __init__(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    def get_shared_drive_by_year(self, year: str) -> str | None:
        """
        Find the id of the appropriate shared drive for the given year.
        Matches by drive name containing the year string (e.g. '2026').
        """
        results = self.service.drives().list(
            q=f"name contains '{year}'",
            pageSize=100
        ).execute()
        drives = results.get('drives', [])
        if drives:
            return drives[0]['id']
        return None

    def find_shipment_folder(self, shipment_number: str) -> dict | None:
        """
        Find the folder for the given shipment number in the appropriate shared drive.
        Returns the folder dict {id, name, shared_drive_id} if exactly one match is found, else None.
        """
        year = extract_year_from_shipment(shipment_number)
        drive_id = self.get_shared_drive_by_year(year)
        if not drive_id:
            return None

        query = (
            "mimeType = 'application/vnd.google-apps.folder' "
            f"and name contains '{shipment_number}' "
            "and trashed = false"
        )
        results = self.service.files().list(
            q=query,
            corpora='drive',
            driveId=drive_id,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields='files(id, name)'
        ).execute()

        folders = results.get('files', [])
        if len(folders) == 1:
            return {**folders[0], 'shared_drive_id': drive_id}
        return None  # 0 = not found, >1 = ambiguous — send to review

    def list_shipment_files(self, folder_id: str, drive_id: str) -> list[dict]:
        """
        Lists ALL files in a shipment folder.
        Returns file metadata: id, name, mimeType.
        """
        query = f"'{folder_id}' in parents and trashed = false"
        all_files = []
        page_token = None

        while True:
            results = self.service.files().list(
                q=query,
                corpora='drive',
                driveId=drive_id,
                fields='files(id, name, mimeType), nextPageToken',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                pageToken=page_token
            ).execute()
            all_files.extend(results.get('files', []))
            page_token = results.get('nextPageToken')
            if not page_token:
                break

        return all_files

    def download_file_content(self, file_id: str, file_mime_type: str) -> bytes | None:
        """
        Download the raw content of a file from Google Drive. 
        Uses export_media for Google Workspace files.
        Uses get_media for other file types.
        Returns bytes that can be base64 encoded for Gemini API input.
        """

        GOOGLE_EXPORT_TYPES = {
            "application/vnd.google-apps.spreadsheet": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx"
            ),
            "application/vnd.google-apps.document": (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".docx"
            ),
        }

        try:
            if file_mime_type in GOOGLE_EXPORT_TYPES:
                export_mime_type, _ = GOOGLE_EXPORT_TYPES[file_mime_type]
                request = self.service.files().export_media(fileId=file_id, mimeType=export_mime_type)
            else:
                request = self.service.files().get_media(fileId=file_id)
            
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False

            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    logging.info(f"Download progress: {int(status.progress() * 100)}%")
            
            return file.getvalue()
            
        except HttpError as error:
            logging.error(f"Smart download failed for file {file_id}: {error}")
            return None


    
    def create_file_in_folder(self, folder_id: str, title: str, mime_type: str) -> str:
        """
        Creates an empty file with specified MIME type in folder.
        """
        file_metadata = {"name": title, "parents": [folder_id], "mimeType": mime_type}
        return self.service.files().create(body=file_metadata, fields="id").execute().get("id")

    def move_file_to_folder(self, file_id: str, folder_id: str):
        """
        Moves an existing file into a folder.
        """
        # Get current parents
        file = self.service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents', []))
        
        # Move to new folder
        self.service.files().update(
            fileId=file_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
    
    def create_spreadsheet(self, title: str, folder_id: str = None) -> dict:
        """
        Creates a new Google Spreadsheet via Drive API (bypasses Sheets API permission restriction).
        If folder_id provided, places it directly in that folder.
        Returns {spreadsheet_id, spreadsheet_url}
        """
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.spreadsheet',
        }
        
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        result = self.service.files().create(
            body=file_metadata,
            fields='id, webViewLink',
            supportsAllDrives=True,
        ).execute()

        return {
            "spreadsheet_id": result["id"],
            "spreadsheet_url": result["webViewLink"]
        }