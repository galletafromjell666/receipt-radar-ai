# Receipt Radar AI

An AI-powered automated expense tracker that extracts data from bank emails using DeepSeek and stores it directly in a Neon PostgreSQL database.

## Overview

This project is a standalone worker designed to automate the process of tracking financial expenses. It polls your email inbox, identifies new transaction notifications, uses a Large Language Model (DeepSeek) to extract structured data, and saves the results to your database.

## Key Features

- **Smart Extraction**: Uses DeepSeek-v4-flash to extract amount, currency, merchant, category, and source (bank/card) from raw email content.
- **Robust Deduplication**: 
    - Uses a custom IMAP flag (`$Processed`) to track which emails have been handled, independent of whether you've read them on your phone.
    - Secondary database-level check using unique `email_id` (IMAP UID) to prevent duplicate entries and redundant AI costs.
- **Data Normalization**: Automatically cleans HTML and normalizes Spanish special characters to ASCII for consistent reporting.
- **Standalone Execution**: Designed to run as a simple cron job or local script, with no heavy web-server overhead.
- **Direct DB Architecture**: The worker handles ingestion and processing, while the frontend is designed to query the database directly.

## Project Structure

```text
x/
├── src/                # Core logic (AI, Email, Database)
├── scripts/            # Testing and setup utilities
├── main.py             # Main entry point
├── .env                # Local configuration (ignored)
├── pyproject.toml      # Project metadata and dependencies
└── uv.lock             # Locked dependencies
```

## Getting Started

### 1. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd receipt-radar-ai

# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates .venv and installs everything)
uv sync
```

### 2. Configuration
Copy `.env.example` to `.env` and fill in your credentials:
- `DATABASE_URL`: Your Neon PostgreSQL connection string.
- `DEEPSEEK_API_KEY`: Your API key for DeepSeek.
- `EMAIL_USER` / `EMAIL_PASSWORD`: Your Gmail address and an [App Password](https://myaccount.google.com/apppasswords).
- `FETCH_DAYS_LIMIT`: How many days back to look for emails (default: 30).

### 3. Usage
To trigger a synchronization:
```bash
uv run python main.py
```

## Linting & Formatting

The project uses **Ruff** for fast linting and formatting.

```bash
# Check for errors and unused imports
uv run ruff check .

# Automatically fix fixable errors
uv run ruff check --fix .

# Format the codebase
uv run ruff format .
```

## Testing & Utilities

For verifying components individually, check the [scripts/](scripts/) directory:
- `gmail_test.py`: Verify your connection and preview what content is sent to the LLM.
- `ai_test.py`: Test the DeepSeek connection and verify the extraction prompt with sample data.

See the [scripts/README.md](scripts/README.md) for detailed CLI usage.

## Database Schema

The worker populates an `expenses` table with the following fields:
- `amount`: Float value of the transaction.
- `currency`: 3-letter currency code (e.g., USD, EUR).
- `merchant`: Name of the business.
- `category`: Automatically assigned category (e.g., Food, Transport).
- `source`: The bank or financial institution.
- `account`: Specific card or account identifier (e.g., last 4 digits).
- `date`: The transaction timestamp (extracted from email body or metadata fallback).
- `email_id`: Unique IMAP UID for deduplication.
