SPREADSHEET_ID = "1WRPcfdu-b-fn0YDCiZH-UwsKAP5ckbR8bePEZMNqqTk"
SHEET_NAME = "Emails"

STATE_FILE_PATH = "state/processed_emails.json"

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
]

SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

MAX_RETRIES = 3
RETRY_DELAY = 2

SUBJECT_FILTER = ""
