"""
Google Sheets API service module.
Handles authentication and appending rows to a Google Sheet.
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.api_core.exceptions import GoogleAPIError
import googleapiclient.discovery
import logging
import time
import pickle

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_FILE = "credentials/sheets_token.pickle"
CREDENTIALS_FILE = "credentials/credentials.json"


class SheetsService:
    """Handles Google Sheets API operations."""

    def __init__(self):
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Sheets API using OAuth 2.0."""
        creds = None

        # Load existing token if available
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)

        # Refresh or create new credentials
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for future runs
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

        self.service = googleapiclient.discovery.build(
            "sheets", "v4", credentials=creds
        )
        logger.info("Google Sheets authentication successful")

    def append_email_row(self, spreadsheet_id, sheet_name, values, max_retries=3, retry_delay=2):
        """
        Append a row to the Google Sheet.

        Args:
            spreadsheet_id: ID of the target spreadsheet
            sheet_name: Name of the sheet tab
            values: List of values to append [from, subject, date, content]
            max_retries: Number of times to retry on failure
            retry_delay: Delay in seconds between retries

        Returns:
            True if successful, False otherwise
        """
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
                logger.info(f"Successfully appended row to sheet")
                return True
            except GoogleAPIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to append row after {max_retries} attempts")
                    return False

        return False
