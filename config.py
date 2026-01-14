"""
Configuration file for gmail-to-sheets project.
Stores spreadsheet ID, sheet name, and state file path.
"""

# Google Sheets Configuration
SPREADSHEET_ID = "1xrLY1sOfNALMFFL4a4VjpQ6bhfKgZNtRn7lWWRgbxLg"  # Replace with your Google Sheet ID
SHEET_NAME = "Emails"  # Name of the sheet tab

# State persistence file path
STATE_FILE_PATH = "state/processed_emails.json"

# Gmail Configuration
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",  # Read and mark emails as read
]

SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

# API Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Optional: Subject filter (leave empty to fetch all emails)
SUBJECT_FILTER = ""  # Example: "noreply@" to filter specific subjects
