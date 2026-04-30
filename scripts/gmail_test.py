import os
import argparse
import sys
# Add parent directory to sys.path to allow importing from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from imap_tools import MailBox, AND
from dotenv import load_dotenv
from utils import clean_html

load_dotenv()

def test_gmail_connection(sender_filter=None, email_id=None, clean=False):
    imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not email_user or not email_password:
        print("❌ Error: EMAIL_USER or EMAIL_PASSWORD not found in .env file.")
        return

    print(f"🚀 Connecting to {imap_server}...")
    
    try:
        with MailBox(imap_server).login(email_user, email_password) as mailbox:
            print("✅ Login successful!")

            if email_id:
                print(f"📄 Fetching content for Email UID: {email_id}...")
                msgs = list(mailbox.fetch(AND(uid=email_id)))
                if not msgs:
                    print(f"❌ No email found with UID: {email_id}")
                    return
                
                msg = msgs[0]
                body = msg.text if not clean else clean_html(msg.html if msg.html else msg.text)
                
                print("-" * 50)
                print(f"From: {msg.from_}")
                print(f"Date: {msg.date}")
                print(f"Subject: {msg.subject}")
                print("-" * 50)
                print("BODY:")
                print(body)
                print("-" * 50)
                print(f"Original length: {len(body)} characters")
            else:
                criteria = AND(from_=sender_filter) if sender_filter else 'ALL'
                print(f"🔍 Searching emails (Filter: {sender_filter if sender_filter else 'None'})...")
                
                msgs = list(mailbox.fetch(criteria, limit=5, reverse=True))
                
                if not msgs:
                    print("ℹ️ No emails found matching the criteria.")
                else:
                    print(f"\n📬 Showing last {len(msgs)} emails:")
                    print("-" * 50)
                    for msg in msgs:
                        print(f"UID: {msg.uid} | From: {msg.from_} | Subject: {msg.subject}")

    except Exception as e:
        print(f"\n❌ Failed to connect to Gmail: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Gmail connection and fetch emails using imap-tools.")
    parser.add_argument("--filter", help="Filter emails by sender domain or address")
    parser.add_argument("--id", help="Fetch and show content for a specific email UID")
    parser.add_argument("--clean", action="store_true", help="Strip HTML tags using BeautifulSoup")
    
    args = parser.parse_args()
    test_gmail_connection(sender_filter=args.filter, email_id=args.id, clean=args.clean)
