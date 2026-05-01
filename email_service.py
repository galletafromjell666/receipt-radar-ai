import os
from imap_tools import MailBox, AND, NOT
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils import format_email_for_ai

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
FETCH_DAYS_LIMIT = int(os.getenv("FETCH_DAYS_LIMIT", "30"))

def get_unprocessed_emails():
    results = []
    # Use environment variable for search queries (comma-separated)
    queries_env = os.getenv("SEARCH_QUERIES")
    if not queries_env:
        print("❌ Error: SEARCH_QUERIES not found in environment.")
        return []
    
    queries = [q.strip() for q in queries_env.split(",")]
    
    # Calculate date limit
    date_limit = (datetime.now() - timedelta(days=FETCH_DAYS_LIMIT)).date()
    
    try:
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASSWORD) as mailbox:
            # We'll use a dictionary to deduplicate emails if they match multiple queries
            seen_uids = set()
            
            for query in queries:
                # Search for emails matching the query AND date AND NOT processed
                # Move NOT to the front to avoid Python's "positional after keyword" error
                criteria = AND(NOT(keyword='$Processed'), date_gte=date_limit, text=query)
                
                # Fetch up to 20 per query (reverse order)
                for msg in mailbox.fetch(criteria, limit=20, reverse=True):
                    if msg.uid in seen_uids:
                        continue
                    
                    seen_uids.add(msg.uid)
                    full_content = format_email_for_ai(msg)
                    
                    results.append({
                        "email_id": msg.uid,
                        "subject": msg.subject,
                        "body": full_content,
                        "sender": msg.from_
                    })
    except Exception as e:
        print(f"Error fetching emails: {e}")
    
    return results

def mark_as_processed(email_uid):
    """Mark email with a custom $Processed flag to avoid re-fetching it."""
    try:
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASSWORD) as mailbox:
            # We use a custom flag $Processed instead of \Seen to be independent of user reading habits
            mailbox.flag(email_uid, '$Processed', True)
            # We also mark as seen just to keep the inbox clean
            mailbox.flag(email_uid, '\\Seen', True)
    except Exception as e:
        print(f"Error marking email {email_uid} as processed: {e}")
