import os
import logging
import time
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.api_core.exceptions import GoogleAPIError
import googleapiclient.discovery

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_FILE = "credentials/sheets_token.pickle"
CREDENTIALS_FILE = "credentials/credentials.json"


class SheetsService:
    def __init__(self):
        self.service = None
        self._authenticate()

    def _authenticate(self):
        creds = None

        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

        self.service = googleapiclient.discovery.build(
            "sheets", "v4", credentials=creds
        )
        logger.info("Google Sheets authentication successful")

    def append_email_row(self, spreadsheet_id, sheet_name, values, max_retries=3, retry_delay=2):
        body = {"values": [values]}
        range_name = f"{sheet_name}!A:D"

        for attempt in range(max_retries):
            try:
                self.service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    body=body,
                ).execute()
                logger.info("Successfully appended row to sheet")
                return True
            except GoogleAPIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to append row after {max_retries} attempts")
                    return False

        return False
