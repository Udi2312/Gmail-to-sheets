"""
Main orchestration script.
Coordinates Gmail and Sheets services to automate email to sheet transfer.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from src.gmail_service import GmailService
from src.sheets_service import SheetsService
from src.email_parser import EmailParser
from config import SPREADSHEET_ID, SHEET_NAME, STATE_FILE_PATH, MAX_RETRIES, RETRY_DELAY, SUBJECT_FILTER

# Setup logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/gmail_to_sheets.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class EmailProcessor:
    """Main orchestrator for Gmail to Sheets automation."""

    def __init__(self):
        self.gmail_service = GmailService()
        self.sheets_service = SheetsService()
        self.processed_ids = self._load_state()

    def _load_state(self):
        """Load previously processed email IDs from state file."""
        if not os.path.exists(STATE_FILE_PATH):
            return set()

        try:
            with open(STATE_FILE_PATH, "r") as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data.get('processed_ids', []))} previously processed emails")
                return set(data.get("processed_ids", []))
        except Exception as e:
            logger.error(f"Error loading state file: {e}")
            return set()

    def _save_state(self):
        """Save processed email IDs to state file."""
        try:
            os.makedirs(os.path.dirname(STATE_FILE_PATH), exist_ok=True)
            with open(STATE_FILE_PATH, "w") as f:
                json.dump(
                    {"processed_ids": list(self.processed_ids), "last_updated": datetime.now().isoformat()},
                    f,
                    indent=2,
                )
            logger.info("State file saved")
        except Exception as e:
            logger.error(f"Error saving state file: {e}")

    def process_emails(self):
        """Main processing loop."""
        logger.info("Starting email processing...")

        try:
            # Fetch unread emails
            emails = self.gmail_service.get_unread_emails(MAX_RETRIES, RETRY_DELAY)

            if not emails:
                logger.info("No unread emails found")
                return

            logger.info(f"Processing {len(emails)} unread emails")
            processed_count = 0
            skipped_count = 0

            for email_data in emails:
                message_id = email_data["id"]

                # Check if already processed
                if message_id in self.processed_ids:
                    logger.info(f"Skipping already processed email: {message_id}")
                    skipped_count += 1
                    continue

                # Get full email details
                message = self.gmail_service.get_email_details(message_id)
                if not message:
                    continue

                # Parse email
                parsed = EmailParser.parse_email(message)
                if not parsed:
                    logger.warning(f"Failed to parse email {message_id}")
                    continue

                # Optional: Apply subject filter
                if SUBJECT_FILTER and SUBJECT_FILTER not in parsed["subject"]:
                    logger.info(f"Skipping email due to subject filter: {parsed['subject']}")
                    skipped_count += 1
                    continue

                # Append to Google Sheet
                values = [
                    parsed["from"],
                    parsed["subject"],
                    parsed["date"],
                    parsed["content"][:1000],  # Limit content to 1000 chars
                ]

                if self.sheets_service.append_email_row(
                    SPREADSHEET_ID, SHEET_NAME, values, MAX_RETRIES, RETRY_DELAY
                ):
                    # Mark as read
                    self.gmail_service.mark_email_as_read(message_id)

                    # Add to processed set
                    self.processed_ids.add(message_id)
                    processed_count += 1
                    logger.info(f"Successfully processed email: {parsed['subject']}")
                else:
                    logger.error(f"Failed to append email to sheet: {parsed['subject']}")

            # Save state
            self._save_state()

            logger.info(
                f"Email processing complete. Processed: {processed_count}, Skipped: {skipped_count}"
            )

        except Exception as e:
            logger.error(f"Error during email processing: {e}")
            raise


def main():
    """Entry point for the script."""
    try:
        os.makedirs("logs", exist_ok=True)
        processor = EmailProcessor()
        processor.process_emails()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
