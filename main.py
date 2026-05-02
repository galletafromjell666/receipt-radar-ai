import os
import json
from sqlalchemy.orm import Session
from src.database import get_db, engine
from datetime import datetime, timezone, timedelta
from src import models
from src.email_service import get_unprocessed_emails, mark_as_processed
from src.ai_service import extract_expense_from_email
from src.utils import check_connections

# Create tables on startup (simple for now)
try:
    print("🗄️ Connecting to Database...")
    models.Base.metadata.create_all(bind=engine)
    print("✅ Database tables verified/created.")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    exit(1)

def run_sync(db: Session):
    """
    Core logic to sync emails with the database.
    Can be called locally or from a scheduler.
    """
    if not check_connections():
        print("🛑 Sync aborted due to connection failures.")
        return 0

    emails = get_unprocessed_emails()
    processed_count = 0
    
    for email_data in emails:
        # Check if already processed in DB
        existing = db.query(models.Expense).filter(models.Expense.email_id == email_data["email_id"]).first()
        if existing:
            continue
            
        try:
            # 1. Extract data using AI
            print(f"\n--- Sending to LLM (UID: {email_data['email_id']}) ---")
            print(email_data["body"])
            print("-" * 40)
            
            extracted_data = extract_expense_from_email(email_data["body"])
            
            print("✨ AI Extracted Data:")
            print(json.dumps(extracted_data, indent=2))
            
            # 2. Save to DB
            extracted_date = extracted_data.get("date")
            try:
                if extracted_date:
                    # Parse the ISO date
                    dt = datetime.fromisoformat(extracted_date.replace("Z", "+00:00"))
                    
                    # If the date has no timezone (naive), assume it is GMT-6 (El Salvador)
                    # and convert it to UTC (GMT)
                    if dt.tzinfo is None:
                        # GMT-6 to UTC: Add 6 hours
                        dt = dt.replace(tzinfo=timezone(timedelta(hours=-6)))
                    
                    expense_date = dt.astimezone(timezone.utc)
                else:
                    expense_date = datetime.now(timezone.utc)
            except Exception as e:
                print(f"⚠️ Date parsing failed: {e}. Using current UTC time.")
                expense_date = datetime.now(timezone.utc)

            # Ensure the date saved to DB is naive UTC for consistency if needed,
            # but usually keeping it as offset-aware UTC is better.
            # We'll strip tzinfo for DB compatibility if the column is TIMESTAMP WITHOUT TIME ZONE
            expense_date = expense_date.replace(tzinfo=None)

            new_expense = models.Expense(
                email_id=email_data["email_id"],
                amount=extracted_data.get("amount"),
                currency=extracted_data.get("currency", "USD"),
                category=extracted_data.get("category"),
                merchant=extracted_data.get("merchant"),
                source=extracted_data.get("source"),
                account=extracted_data.get("account"),
                description=extracted_data.get("description"),
                date=expense_date
            )
            
            db.add(new_expense)
            db.commit()
            
            # 3. Mark as processed on email server (using custom $Processed flag)
            mark_as_processed(email_data["email_id"])
            processed_count += 1
            print(f"✅ Processed email: {email_data['email_id']}")
            
        except Exception as e:
            print(f"❌ Error processing email {email_data['email_id']}: {e}")
            continue
            
    return processed_count

if __name__ == "__main__":
    # Local execution entry point
    print("🚀 Starting local sync...")
    with next(get_db()) as session:
        count = run_sync(session)
        print(f"🏁 Sync finished. Processed {count} emails.")


