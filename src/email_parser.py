"""
Email parsing module.
Extracts sender, subject, date, and body from Gmail messages.
"""

import base64
import email
from email.mime.text import MIMEText
import logging
import re
import html2text

logger = logging.getLogger(__name__)


class EmailParser:
    """Parses Gmail messages to extract relevant data."""

    @staticmethod
    def parse_email(message):
        """
        Parse a Gmail message and extract sender, subject, date, and body.

        Args:
            message: Gmail message object from API

        Returns:
            Dictionary with keys: from, subject, date, content
        """
        try:
            headers = message["payload"]["headers"]
            sender = EmailParser._get_header(headers, "From")
            subject = EmailParser._get_header(headers, "Subject")
            date = EmailParser._get_header(headers, "Date")

            # Extract body
            body = EmailParser._get_email_body(message["payload"])

            return {
                "from": sender,
                "subject": subject,
                "date": date,
                "content": body,
            }
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None

    @staticmethod
    def _get_header(headers, name):
        """Extract a specific header value."""
        for header in headers:
            if header["name"] == name:
                return header["value"]
        return ""

    @staticmethod
    def _get_email_body(payload):
        """
        Extract email body from payload, handling both plain text and HTML.

        Args:
            payload: Message payload from Gmail API

        Returns:
            Plain text email body
        """
        body = ""

        if "parts" in payload:
            # Multipart message
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    if "data" in part["body"]:
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8"
                        )
                        break
                elif part["mimeType"] == "text/html":
                    if "data" in part["body"]:
                        html_body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8"
                        )
                        body = EmailParser._html_to_text(html_body)
                        # Continue to see if there's plain text version
        else:
            # Single part message
            if "data" in payload["body"]:
                body_data = payload["body"]["data"]
                body = base64.urlsafe_b64decode(body_data).decode("utf-8")

        return body.strip()

    @staticmethod
    def _html_to_text(html_content):
        """Convert HTML email content to plain text."""
        try:
            h = html2text.HTML2Text()
            h.ignore_links = False
            return h.handle(html_content)
        except Exception as e:
            logger.warning(f"Failed to convert HTML to text: {e}")
            # Fallback: remove HTML tags
            return re.sub(r"<[^>]+>", "", html_content)
