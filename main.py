from sqlalchemy.orm import Session
from database import get_db, engine
from datetime import datetime
import models
from email_service import get_unprocessed_emails, mark_as_processed, IMAP_SERVER, EMAIL_USER, EMAIL_PASSWORD
from ai_service import extract_expense_from_email, DEEPSEEK_API_KEY
from imap_tools import MailBox

# Create tables on startup (simple for now)
try:
    print("🗄️ Connecting to Database...")
    models.Base.metadata.create_all(bind=engine)
    print("✅ Database tables verified/created.")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    exit(1)

def check_connections():
    """Verify all external services are reachable before starting."""
    print("🔍 Pre-flight checks...")
    
    # 1. Check AI Key
    if not DEEPSEEK_API_KEY:
        print("❌ DEEPSEEK_API_KEY is missing!")
        return False

    # 2. Check Search Queries
    if not os.getenv("SEARCH_QUERIES"):
        print("❌ SEARCH_QUERIES is missing in environment!")
        return False
    
    # 3. Check Email Connection
    try:
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASSWORD) as mailbox:
            print("✅ Email connection successful.")
    except Exception as e:
        print(f"❌ Email connection failed: {e}")
        return False
    
    print("🚀 All systems green!")
    return True

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
            extracted_data = extract_expense_from_email(email_data["body"])
            
            # 2. Save to DB
            extracted_date = extracted_data.get("date")
            try:
                expense_date = datetime.fromisoformat(extracted_date.replace("Z", "+00:00")) if extracted_date else datetime.utcnow()
            except:
                expense_date = datetime.utcnow()

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


