import json
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from src import models
from src.ai_service import extract_expense_from_email
from src.database import engine, get_db
from src.email_service import get_unprocessed_emails, mark_as_processed
from src.utils import check_connections

# Create tables on startup (simple for now)
try:
    print("🗄️ Connecting to Database...")
    models.Base.metadata.create_all(bind=engine)
    print("✅ Database tables verified/created.")
    db = next(get_db())
    try:
        models.seed_categories(db)
        print("✅ Categories seeded.")
    finally:
        db.close()
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

    active_categories = (
        db.query(models.Category)
        .filter(models.Category.is_active.is_(True))
        .order_by(models.Category.id)
        .all()
    )
    if not active_categories:
        print("❌ No categories found in DB. Seed the categories first.")
        return 0

    default_other = db.query(models.Category).filter_by(name="Other").first()
    category_names = [c.name for c in active_categories]
    print(f"🏷️  Categories sent to LLM: {', '.join(category_names)}")

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
            
            extracted_data = extract_expense_from_email(
                email_data["body"], available_categories=category_names
            )
            
            print("✨ AI Extracted Data:")
            print(json.dumps(extracted_data, indent=2))

            # Resolve category: match LLM output to a known category
            category_name = extracted_data.get("category", "Other")
            matched = db.query(models.Category).filter(
                func.lower(models.Category.name) == func.lower(category_name.strip()),
                models.Category.is_active.is_(True),
            ).first()
            if matched:
                category_id = matched.id
            else:
                print(
                    f"⚠️ Unknown category '{category_name}', falling back to 'Other'"
                )
                category_id = default_other.id if default_other else 1
            
            # 2. Save to DB
            extracted_date = extracted_data.get("date")
            try:
                if extracted_date:
                    # Parse the ISO date
                    dt = datetime.fromisoformat(extracted_date.replace("Z", "+00:00"))
                    
                    # If the date has no timezone (naive), assume it is the local bank timezone
                    # (configured via TIMEZONE_OFFSET, e.g., -6 for El Salvador)
                    # and convert it to UTC (GMT)
                    if dt.tzinfo is None:
                        tz_offset = int(os.getenv("TIMEZONE_OFFSET", "-6"))
                        dt = dt.replace(tzinfo=timezone(timedelta(hours=tz_offset)))
                    
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
                category_id=category_id,
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


