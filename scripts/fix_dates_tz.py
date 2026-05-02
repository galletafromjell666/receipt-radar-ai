import os
from sqlalchemy import text
from src.database import engine
from dotenv import load_dotenv

load_dotenv()

def fix_existing_dates():
    """
    One-time script to convert existing dates in the database from GMT-6 to UTC.
    It adds 6 hours to all existing records.
    """
    print("🚀 Connecting to database to fix dates...")
    
    # SQL to update dates: Add 6 hours to every date in the expenses table
    # This assumes they were stored as local El Salvador time (GMT-6)
    update_query = text("UPDATE expenses SET date = date + interval '6 hours';")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(update_query)
            connection.commit()
            print(f"✅ Successfully updated {result.rowcount} records to UTC.")
    except Exception as e:
        print(f"❌ Error fixing dates: {e}")

if __name__ == "__main__":
    fix_existing_dates()
