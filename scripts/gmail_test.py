import os
import argparse
import sys
# Add parent directory to sys.path to allow importing from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from imap_tools import MailBox, AND
from dotenv import load_dotenv
from utils import format_email_for_ai, clean_html

load_dotenv()

def test_gmail_connection(query=None, email_id=None):
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
                msgs = list(mailbox.fetch(AND(uid=email_id)))
                if not msgs:
                    print(f"❌ No email found with UID: {email_id}")
                    return
                
                msg = msgs[0]
                formatted_content = format_email_for_ai(msg)
                
                print("\n--- CONTENT SENT TO LLM ---")
                print(formatted_content)
                print("--- END OF CONTENT ---")
                print(f"Length: {len(formatted_content)} characters")
            else:
                # Search for emails using the query across multiple fields
                criteria = AND(text=query) if query else 'ALL'
                print(f"🔍 Searching emails (Query: {query if query else 'None'})...")
                
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
    parser.add_argument("--query", help="Search query (matches sender, subject, or body)")
    parser.add_argument("--id", help="Fetch and show content for a specific email UID")
    
    args = parser.parse_args()
    test_gmail_connection(query=args.query, email_id=args.id)
