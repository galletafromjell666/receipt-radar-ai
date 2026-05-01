import os
import argparse
import sys
from datetime import datetime, timedelta

from imap_tools import MailBox, AND
from dotenv import load_dotenv
from src.utils import format_email_for_ai, check_connections

load_dotenv()

def test_gmail_connection(query=None, email_id=None, show_llm=False, days=None, limit=10):
    if not check_connections():
        return

    imap_server = os.getenv("IMAP_SERVER")
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")

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
                
                print("\n" + "="*60)
                print("RAW EMAIL DETAILS")
                print("="*60)
                print(f"From:    {msg.from_}")
                print(f"Date:    {msg.date}")
                print(f"Subject: {msg.subject}")
                print("-" * 60)
                print("BODY:")
                # Show raw text if available, otherwise raw html
                print(msg.text if msg.text else msg.html)
                print("-" * 60)
                print(f"Raw Length: {len(msg.text if msg.text else msg.html)} characters")

                if show_llm:
                    formatted_content = format_email_for_ai(msg)
                    print("\n" + "*"*60)
                    print("PREVIEW: CONTENT SENT TO LLM")
                    print("*"*60)
                    print(formatted_content)
                    print("*"*60)
                    print(f"LLM Content Length: {len(formatted_content)} characters")
                else:
                    print("\n💡 Tip: Use --llm flag to see the cleaned version sent to the AI.")
                
                print("="*60 + "\n")
            else:
                # Search for emails using the query and optional date limit
                criteria_parts = []
                if query:
                    criteria_parts.append(AND(text=query))
                
                if days:
                    date_limit = (datetime.now() - timedelta(days=days)).date()
                    criteria_parts.append(AND(date_gte=date_limit))
                    print(f"📅 Filtering emails since: {date_limit} ({days} days ago)")

                criteria = AND(*criteria_parts) if criteria_parts else 'ALL'
                print(f"🔍 Searching emails (Query: {query if query else 'None'})...")
                
                msgs = list(mailbox.fetch(criteria, limit=limit, reverse=True))
                
                if not msgs:
                    print("ℹ️ No emails found matching the criteria.")
                else:
                    print(f"\n📬 Showing last {len(msgs)} emails (Limit: {limit}):")
                    print("-" * 50)
                    for msg in msgs:
                        print(f"UID: {msg.uid} | Date: {msg.date.date()} | From: {msg.from_} | Subject: {msg.subject}")

    except Exception as e:
        print(f"\n❌ Failed to connect to Gmail: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Gmail connection and fetch emails using imap-tools.")
    parser.add_argument("--query", help="Search query (matches sender, subject, or body)")
    parser.add_argument("--id", help="Fetch and show content for a specific email UID")
    parser.add_argument("--llm", action="store_true", help="Show the cleaned version sent to the AI")
    parser.add_argument("--days", type=int, help="Number of days back to search")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of emails to fetch (default: 10)")
    
    args = parser.parse_args()
    test_gmail_connection(query=args.query, email_id=args.id, show_llm=args.llm, days=args.days, limit=args.limit)
