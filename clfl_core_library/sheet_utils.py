from googleapiclient.discovery import build
from .drive_utils import DriveManager

class SheetsManager:
    def __init__(self, credentials):
        self.sheets_service = build("sheets", "v4", credentials=credentials)

    def create_spreadsheet(self, title: str, initial_data: list = None) -> str:
        """
        Creates a new Google Spreadsheet.
        Returns: {"spreadsheet_id": "...", "spreadsheet_url": "..."}
        """
        body = {"properties": {"title": title}}
        
        # Optionally add initial sheets/data
        if initial_data:
            body["sheets"] = [{
                "properties": {"title": "Sheet1"},
                "data": [{"rowData": initial_data}]
            }]
        
        result = self.sheets_service.spreadsheets().create(body=body).execute()
        return {
            "spreadsheet_id": result["spreadsheetId"],
            "spreadsheet_url": result["spreadsheetUrl"]
        }

    def append_rows(self, spreadsheet_id: str, range: str, values: list):
        """
        Appends rows of values to the specified range in a spreadsheet.
        Values are inserted as-is (RAW). Raises on API error so the caller knows it failed.
        """
        try:
            body = {"values": values}
            return (self.sheets_service
                        .spreadsheets()
                        .values()
                        .append(spreadsheetId=spreadsheet_id, range=range, valueInputOption="RAW", body=body)
                        .execute()
                    )
        except Exception as e:
            raise Exception(f"Failed to append rows to {range}: {str(e)}")

    def get_values(self, spreadsheet_id: str, range: str) -> list:
        """
        Retrieves values from the specified range in a spreadsheet.
        Returns a list of rows (empty list if range has no data). Raises on API error.
        """
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range
            ).execute()
            return result.get('values', [])
        except Exception as e:
            raise Exception(f"Failed to read {range}: {str(e)}")

    def batch_get_values(self, spreadsheet_id: str, ranges: list) -> list:
        """
        Retrieves values from multiple ranges in a spreadsheet in a single API call.
        Returns a list of ValueRange objects. Raises on API error.
        """
        try:
            result = self.sheets_service.spreadsheets().values().batchGet(
                spreadsheetId=spreadsheet_id, ranges=ranges
            ).execute()
            return result.get('valueRanges', [])
        except Exception as e:
            raise Exception(f"Failed to batch read ranges: {str(e)}")
