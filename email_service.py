import os
from imap_tools import MailBox, AND
from dotenv import load_dotenv
from utils import format_email_for_ai

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def get_unprocessed_emails():
    results = []
    try:
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASSWORD) as mailbox:
            # Fetch last 20 emails from INBOX
            for msg in mailbox.fetch(limit=20, reverse=True):
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
    """Mark email as seen/processed using its UID."""
    try:
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASSWORD) as mailbox:
            mailbox.flag(email_uid, '\\Seen', True)
    except Exception as e:
        print(f"Error marking email {email_uid} as processed: {e}")
