import os
from imap_tools import MailBox, AND
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def clean_html(html_content):
    """Use BeautifulSoup for robust HTML to text conversion."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    # Get text and clean up whitespace
    text = soup.get_text(separator=' ')
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

def get_unprocessed_emails():
    results = []
    try:
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASSWORD) as mailbox:
            # Fetch last 20 emails from INBOX
            # In production, you might filter by 'UNSEEN' or specific criteria
            for msg in mailbox.fetch(limit=20, reverse=True):
                body = msg.text if msg.text else clean_html(msg.html)
                
                results.append({
                    "email_id": msg.uid,
                    "subject": msg.subject,
                    "body": body,
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
