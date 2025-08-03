
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

def append_to_sheet(spreadsheet_id, values):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(spreadsheet_id).sheet1
    sheet.append_row(values)
