from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json

def append_to_sheet(spreadsheet_id, row_data):
    creds_dict = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
    creds = service_account.Credentials.from_service_account_info(creds_dict)
    service = build("sheets", "v4", credentials=creds)

    sheet = service.spreadsheets()
    sheet.values().append(
        spreadsheetId=spreadsheet_id,
        range="A1",
        valueInputOption="RAW",
        body={"values": [row_data]}
    ).execute()
