# Utility Scripts

This folder contains scripts to test and verify the different components of the expense tracker.

## Scripts

### 1. AI Connection Test ([ai_test.py](ai_test.py))
Verifies the connection to the DeepSeek API and ensures the model is responding.

**Usage:**
- **Simple Hello World:**
  ```bash
  python3 scripts/ai_test.py
  ```
- **Test with sample banking email:**
  ```bash
  python3 scripts/ai_test.py --email
  ```

**All Arguments:**
- `--email`: Optional flag to run an extraction test using a hardcoded sample email instead of a simple "Hello World" message.

### 2. Gmail Connection Test ([gmail_test.py](gmail_test.py))
Verifies the IMAP connection to Gmail, allowing you to list recent emails or fetch specific content.

**Usage:**
- **List recent emails (default limit 10):**
  ```bash
  python3 scripts/gmail_test.py
  ```
- **List emails from the last X days:**
  ```bash
  python3 scripts/gmail_test.py --days 7
  ```
- **Set a custom fetch limit:**
  ```bash
  python3 scripts/gmail_test.py --limit 20
  ```
- **Search by keyword (Sender, Subject, or Body):**
  ```bash
  python3 scripts/gmail_test.py --query "amazon"
  ```
- **Show raw email content by UID:**
  ```bash
  python3 scripts/gmail_test.py --id <EMAIL_ID>
  ```
- **Show email content + AI cleaned version:**
  ```bash
  python3 scripts/gmail_test.py --id <EMAIL_ID> --llm
  ```

**All Arguments:**
- `--query`: Search string to filter emails.
- `--id`: Specific email UID to fetch and display.
- `--llm`: Flag to show the cleaned content exactly as it would be sent to the AI.
- `--days`: Number of days back to search (e.g., `--days 30`).
- `--limit`: Maximum number of emails to display (default: 10).

## Configuration
Both scripts rely on the `.env` file in the project root. Ensure you have the following variables set:
- `DEEPSEEK_API_KEY`: Your API key.
- `DEEPSEEK_BASE_URL`: API base URL (e.g., `https://api.deepseek.com`).
- `DEEPSEEK_MODEL`: Model name (e.g., `deepseek-chat`).
- `EMAIL_USER`: Your Gmail address.
- `EMAIL_PASSWORD`: Your Gmail App Password.
- `IMAP_SERVER`: The IMAP server address (e.g., `imap.gmail.com`).
