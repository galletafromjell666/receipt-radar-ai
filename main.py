import functions_framework
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine
import models
from ai_service import extract_expense_from_email

# Create tables on startup (simple for now)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

from email_service import get_unprocessed_emails, mark_as_processed

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/sync")
def trigger_sync(db: Session = Depends(get_db)):
    """
    Manually or via Cron trigger a sync with the email server.
    """
    emails = get_unprocessed_emails()
    processed_count = 0
    
    for email_data in emails:
        # Check if already processed in DB
        existing = db.query(models.Expense).filter(models.Expense.email_id == email_data["email_id"]).first()
        if existing:
            continue
            
        try:
            # 1. Extract data using AI
            extracted_data = extract_expense_from_email(email_data["body"])
            
            # 2. Save to DB
            new_expense = models.Expense(
                email_id=email_data["email_id"],
                amount=extracted_data.get("amount"),
                currency=extracted_data.get("currency", "USD"),
                category=extracted_data.get("category"),
            merchant=extracted_data.get("merchant"),
            source=extracted_data.get("source"),
            account=extracted_data.get("account"),
            description=extracted_data.get("description")
        )
            
            db.add(new_expense)
            db.commit()
            
            # 3. Mark as processed on email server
            mark_as_processed(email_data["email_id"])
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing email {email_data['email_id']}: {e}")
            continue
            
    return {"status": "success", "processed": processed_count}


import base64
import json

@functions_framework.http
def handle_http(request):
    """Entry point for HTTP triggers (Cloud Scheduler, Manual)."""
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    method = request.method
    path = request.path
    headers = dict(request.headers)
    body = request.get_data()
    
    response = client.request(
        method=method,
        url=path,
        headers=headers,
        content=body
    )
    
    return (response.content, response.status_code, response.headers.items())

@functions_framework.cloud_event
def handle_pubsub(cloud_event):
    """
    Entry point for Pub/Sub triggers (Gmail Push Notifications).
    Gmail sends a message to Pub/Sub -> Pub/Sub triggers this function.
    """
    # The Pub/Sub message data is base64 encoded
    # data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
    # For Gmail push, the data contains the email address and historyId.
    # We just use it as a signal to trigger our sync logic.
    
    from sqlalchemy.orm import Session
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        print("Triggering sync from Pub/Sub event...")
        result = trigger_sync(db)
        print(f"Sync completed: {result}")
    finally:
        db.close()


