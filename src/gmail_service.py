"""
Gmail API service module.
Handles authentication, fetching unread emails, and marking emails as read.
"""

import os
import pickle
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.api_core.exceptions import GoogleAPIError
import googleapiclient.discovery
import logging
import time

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_FILE = "credentials/token.pickle"
CREDENTIALS_FILE = "credentials/credentials.json"


class GmailService:
    """Handles Gmail API operations."""

    def __init__(self):
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth 2.0."""
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

        self.service = googleapiclient.discovery.build("gmail", "v1", credentials=creds)
        logger.info("Gmail authentication successful")

    def get_unread_emails(self, max_retries=3, retry_delay=2):
        """
        Fetch unread emails from Gmail Inbox.

        Args:
            max_retries: Number of times to retry on failure
            retry_delay: Delay in seconds between retries

        Returns:
            List of email dictionaries with message IDs
        """
        query = "is:unread"
        emails = []

        for attempt in range(max_retries):
            try:
                results = (
                    self.service.users()
                    .messages()
                    .list(userId="me", q=query, maxResults=100)
                    .execute()
                )
                messages = results.get("messages", [])
                logger.info(f"Found {len(messages)} unread emails")
                return messages
            except GoogleAPIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise

        return emails

    def get_email_details(self, message_id):
        """
        Get full email details including subject, sender, date, and body.

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with email details
        """
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            return message
        except GoogleAPIError as e:
            logger.error(f"Failed to get email {message_id}: {e}")
            return None

    def mark_email_as_read(self, message_id):
        """
        Mark an email as read by removing the UNREAD label.

        Args:
            message_id: Gmail message ID

        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            logger.info(f"Marked email {message_id} as read")
            return True
        except GoogleAPIError as e:
            logger.error(f"Failed to mark email {message_id} as read: {e}")
            return False
