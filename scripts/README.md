# Utility Scripts

This folder contains scripts to test and verify the different components of the expense tracker.

## Scripts

### 1. AI Connection Test ([ai_test.py](ai_test.py))
Verifies the connection to the DeepSeek API and ensures the model is responding.

**Usage:**
```bash
python scripts/ai_test.py
```

### 2. Gmail Connection Test ([gmail_test.py](gmail_test.py))
Verifies the IMAP connection to Gmail, allowing you to list recent emails or fetch specific content.

**Usage:**
- **List recent emails:**
  ```bash
  python scripts/gmail_test.py
  ```
- **Search by keyword (Sender, Subject, or Body):**
  ```bash
  python scripts/gmail_test.py --query "amazon"
  ```
- **Show raw email content by ID:**
  ```bash
  python scripts/gmail_test.py --id <EMAIL_ID>
  ```
- **Show email content + LLM cleaned version:**
  ```bash
  python scripts/gmail_test.py --id <EMAIL_ID> --llm
  ```

## Configuration
Both scripts rely on the `.env` file in the project root. Ensure you have the following variables set:
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `EMAIL_USER`
- `EMAIL_PASSWORD`
