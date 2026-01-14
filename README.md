## Author

**Udit Bansal**  
B.Tech IT (3rd Year)  
This project was designed and implemented as part of an internship assignment to demonstrate practical API integration, OAuth handling, and automation using Python.


# Gmail to Sheets Automation

A production-grade Python automation system that reads unread emails from Gmail and appends them to a Google Sheet with duplicate prevention.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Gmail to Sheets Workflow                  │
└─────────────────────────────────────────────────────────────┘

1. AUTHENTICATION
   ├─ Load cached OAuth tokens
   └─ Request new tokens if needed (user approval)

2. EMAIL FETCHING
   ├─ Query Gmail API for unread emails
   └─ Rate limiting & retry logic

3. DUPLICATE CHECK
   ├─ Load processed email IDs from state file
   ├─ Skip if email already processed
   └─ Prevent duplicates across multiple runs

4. EMAIL PARSING
   ├─ Extract: From, Subject, Date, Content
   ├─ Handle HTML → Plain Text conversion
   └─ Limit content to prevent sheet overflow

5. SHEET APPEND
   ├─ Append row to Google Sheet
   └─ Retry on API failures

6. STATE UPDATE
   ├─ Mark email as READ in Gmail
   ├─ Save processed email ID
   └─ Persist state to JSON file
```

## Project Structure

```
gmail-to-sheets/
├── src/
│   ├── gmail_service.py       # Gmail API: authentication, fetching, marking as read
│   ├── sheets_service.py      # Google Sheets API: authentication, appending rows
│   ├── email_parser.py        # Email parsing: extract sender, subject, date, body
│   └── main.py                # Main orchestration: coordinates services & state
├── credentials/
│   └── credentials.json       # OAuth credentials (Git ignored)
├── state/
│   └── processed_emails.json  # Processed email IDs (Git ignored)
├── logs/
│   └── gmail_to_sheets.log    # Application logs
├── config.py                  # Configuration: spreadsheet ID, sheet name
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Setup Instructions

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (name it "gmail-to-sheets")
3. Enable the following APIs:
   - Gmail API
   - Google Sheets API
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Select **Desktop application**
6. Download the credentials as JSON and save to `credentials/credentials.json`

### Step 2: Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new spreadsheet
3. Rename the first sheet to "Emails" (or your preferred name)
4. Add headers in the first row: `From | Subject | Date | Content`
5. Copy the spreadsheet ID from the URL (example: `1a2b3c4d5e6f7g8h9i0j`)

### Step 3: Update Configuration

Edit `config.py`:

```python
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"  
SHEET_NAME = "Emails"  
```

### Step 4: Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
```

### Step 5: Run the Script

```bash
python -m src.main
```

**First run:** You'll be prompted to authorize the app in your browser.
**Subsequent runs:** Uses cached tokens automatically.

## How It Works

### OAuth 2.0 Authentication Flow

1. **User Authorization**: First run opens a browser window for user to authorize access
2. **Token Exchange**: Google OAuth server returns an access token
3. **Token Caching**: Token stored locally in `credentials/token.pickle`
4. **Token Refresh**: Automatically refreshes token when expired using refresh token
5. **No Service Account**: Uses user-delegated permissions (safer than service accounts)

## Design Decisions

- Chose a JSON-based state file instead of a database to keep the solution simple and easy to audit.
- Used OAuth 2.0 instead of service accounts to follow Gmail security best practices.
- Split the code into multiple services to keep Gmail logic, Sheets logic, and parsing logic separate and readable.

### Duplicate Prevention Strategy

The system uses a **persistent state file** (`state/processed_emails.json`) to track processed emails:

1. **State Structure**:
   ```json
   {
     "processed_ids": ["msg_id_1", "msg_id_2", ...],
     "last_updated": "2024-01-15T10:30:00.123456"
   }
   ```

2. **Processing Logic**:
   - On startup: Load all processed email IDs from state file
   - For each unread email:
     - Check if ID is in processed set
     - If yes: Skip email
     - If no: Process and append to sheet
   - After successful append:
     - Add email ID to processed set
     - Save updated state to file

3. **Why This Approach**:
   - **Reliable**: Works offline and survives API failures
   - **Fast**: Uses a set internally, so duplicate checks are very quick
   - **Simple**: No database required
   - **Auditable**: Human-readable JSON format
   - **Recoverable**: Previous runs can be reconstructed from state file

### Email Processing Pipeline

```
Unread Email
    ↓
Parse Headers (From, Subject, Date)
    ↓
Extract Body (Plain text or HTML→Plain text conversion)
    ↓
Limit Content (Max 1000 chars to prevent sheet overflow)
    ↓
Append to Google Sheet
    ↓
Mark as READ in Gmail
    ↓
Save Email ID to State File
    ↓
Complete
```

## Challenge Faced During Development

One challenge I faced while building this project was handling API failures and partial execution. 
For example, if the Gmail API succeeds but the Google Sheets API fails due to rate limits, it could lead to inconsistent data.

To solve this, I implemented a retry mechanism and ensured that an email is marked as processed only after it is successfully appended to the Google Sheet. 
This way, the script can safely resume processing without data loss or duplication.


## Features

- ✅ OAuth 2.0 authentication (no hardcoded passwords)
- ✅ Unread email fetching from Gmail Inbox
- ✅ Sender, subject, date, and body extraction
- ✅ HTML to plain text conversion
- ✅ Duplicate prevention via state persistence
- ✅ Automatic email marking as READ
- ✅ Retry logic for API failures
- ✅ Comprehensive logging
- ✅ Production-grade error handling

## Known Limitations

1. **Content Truncation**: Email bodies limited to 1000 characters (configurable)
2. **Inbox Only**: Fetches from Inbox label only (not all labels)
3. **Plain Text Only**: Rich formatting is lost in conversion to plain text
4. **Single Sheet**: Appends to one sheet (could be extended to multiple sheets)
5. **No Scheduling**: Manual runs only (can be combined with cron or task scheduler)
6. **Gmail API Limits**: 10,000 requests/minute per user
7. **OAuth Expiry**: Refresh tokens expire after 6 months of inactivity

This project can be further improved with scheduling and better attachment handling, which I plan to explore as a future enhancement.

## Optional Enhancements

- Add cron job or Windows Task Scheduler for periodic runs
- Implement subject-based email filtering
- Support for multiple Google Sheets destinations
- Email attachment downloading
- Slack notifications on errors
- GraphQL API for historical email queries
- Docker container for deployment

## Troubleshooting

### "File not found: credentials.json"
Ensure you downloaded OAuth credentials and saved to `credentials/credentials.json`

### "Invalid spreadsheet ID"
Check `config.py` and paste the correct spreadsheet ID from your Google Sheet URL

### "Permission denied"
Ensure you authorized all scopes when prompted in the browser

### "No module named 'google'"
Run `pip install -r requirements.txt`

## License

MIT License - Free to use and modify

---

**Questions?** Check the logs in `logs/gmail_to_sheets.log` for detailed error messages.
