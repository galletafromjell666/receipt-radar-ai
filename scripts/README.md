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

### 2. Gmail Connection Test ([gmail_test.py](gmail_test.py))
Verifies the IMAP connection to Gmail, allowing you to list recent emails or fetch specific content.

**Usage:**
- **List recent emails (default 10):**
  ```bash
  python3 scripts/gmail_test.py
  ```
- **List emails from the last 7 days with a limit of 5:**
  ```bash
  python3 scripts/gmail_test.py --days 7 --limit 5
  ```
- **Search by keyword (Sender, Subject, or Body):**
  ```bash
  python3 scripts/gmail_test.py --query "amazon"
  ```
- **Show raw email content by ID:**
  ```bash
  python3 scripts/gmail_test.py --id <EMAIL_ID>
  ```
- **Show email content + LLM cleaned version:**
  ```bash
  python3 scripts/gmail_test.py --id <EMAIL_ID> --llm
  ```

## Configuration
Both scripts rely on the `.env` file in the project root. Ensure you have the following variables set:
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `EMAIL_USER`
- `EMAIL_PASSWORD`
