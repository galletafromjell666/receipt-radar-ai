# AI-Powered Expense Tracker

An ephemeral expense tracker that extracts data from emails using DeepSeek AI and stores it in Neon PostgreSQL.

## Action Plan

### 1. Project Setup
- [x] Initialize Python environment.
- [x] Define dependencies in `requirements.txt`.
- [x] Create core project structure (`main.py`, `models.py`, `database.py`, `ai_service.py`).

### 2. Database Layer
- [x] Set up SQLAlchemy models for expenses.
- [x] Configure connection to Neon PostgreSQL.

### 3. AI Extraction
- [x] Integrate DeepSeek API via OpenAI-compatible client.
- [x] Implement prompt logic to extract structured JSON (amount, currency, category, merchant, etc.).

### 4. Email Ingestion (Polling)
- [x] Implemented IMAP polling in `email_service.py`.
- [x] Added logic to fetch unprocessed emails and avoid duplicates using `email_id`.
- [x] Created a `/sync` endpoint to trigger the process.
- [ ] Configure Google Cloud Scheduler to hit the `/sync` endpoint every 12 hours.

### 5. Frontend & Data Access
- [ ] Frontend connects directly to Neon PostgreSQL for data retrieval.
- [x] Python API focuses solely on email ingestion and AI processing.

### 6. Deployment & Triggers

You can trigger this service in two ways on Google Cloud:

#### Option A: Scheduled (Every 12 hours)
1. Deploy with an HTTP trigger:
   ```bash
   gcloud functions deploy handle_http --runtime python310 --trigger-http
   ```
2. Create a **Cloud Scheduler** job to hit the function's `/sync` URL every 12 hours.

#### Option B: Event-Driven (Real-time Gmail Events)
1. Create a **Google Cloud Pub/Sub** topic.
2. Deploy with a Pub/Sub trigger:
   ```bash
   gcloud functions deploy handle_pubsub --runtime python310 --trigger-topic YOUR_TOPIC_NAME
   ```
3. Configure **Gmail Push Notifications** to publish to your topic:
   - Go to Pub/Sub Topic -> Permissions -> Add `gmail-api-push@system.gserviceaccount.com` as **Pub/Sub Publisher**.
   - Run `python register_watch.py` to start the "watch" on your external Gmail account.
   - **Note**: You must run this script every 7 days to keep the watch active.

## Getting Started

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in your credentials.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
## Local Development & Testing

You can run the exact same logic locally that will run on Google Cloud.

### Option A: Running as a Web API (FastAPI)
This is the easiest way to test your endpoints:
```bash
uvicorn main:app --reload
```
Then trigger the sync:
```bash
curl -X POST http://localhost:8000/sync
```

### Option B: Running as a Cloud Function (Functions Framework)
To mimic the Google Cloud environment exactly, use the `functions-framework`:
```bash
functions-framework --target=handle_http --debug
```
This starts a server on port 8080. You can trigger it with:
```bash
curl -X POST http://localhost:8080/sync
```

## Testing AI Extraction
To verify that the AI is correctly parsing your emails, simply ensure your `.env` is configured and trigger a sync using one of the local methods above.
