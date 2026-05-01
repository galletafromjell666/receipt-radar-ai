import os
from imap_tools import MailBox, AND
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
    # Calculate date limit
    date_limit = (datetime.now() - timedelta(days=FETCH_DAYS_LIMIT)).date()
    
    try:
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASSWORD) as mailbox:
            # Filter by date and exclude emails already marked with our custom $Processed flag
            # This is more robust than checking 'seen' status, which might be triggered by a phone app
            criteria = AND(date_gte=date_limit, keyword_not='$Processed')
            
            # Fetch last 20 emails from INBOX
            for msg in mailbox.fetch(criteria, limit=20, reverse=True):
                # Use the new formatter to include subject and sender in the content
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
