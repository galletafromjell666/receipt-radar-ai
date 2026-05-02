import os
from sqlalchemy import text
from src.database import engine
from dotenv import load_dotenv

load_dotenv()

def fix_existing_dates():
    """
    One-time script to convert existing dates in the database from local time to UTC.
    It reads TIMEZONE_OFFSET from .env (e.g., -6 for El Salvador) and adjusts the records.
    """
    print("🚀 Connecting to database to fix dates...")
    
    tz_offset = int(os.getenv("TIMEZONE_OFFSET", "-6"))
    # If offset is -6, we need to add 6 hours to reach UTC
    hours_to_add = -tz_offset
    
    # SQL to update dates: Add the necessary hours to every date in the expenses table
    update_query = text(f"UPDATE expenses SET date = date + interval '{hours_to_add} hours';")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(update_query)
            connection.commit()
            print(f"✅ Successfully updated {result.rowcount} records to UTC.")
    except Exception as e:
        print(f"❌ Error fixing dates: {e}")

if __name__ == "__main__":
    fix_existing_dates()
