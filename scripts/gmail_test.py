import os
import imaplib
import email
import re
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

def clean_html(html_content):
    """Basic HTML tag stripping to save tokens and clean up content for AI."""
    # Remove script and style elements
    clean = re.sub(r'<(script|style).*?>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    # Remove all other tags
    clean = re.sub(r'<.*?>', ' ', clean)
    # Remove multiple whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def get_email_body(msg, clean=False):
    body = ""
    html_body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            try:
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True)
                
                if payload:
                    part_body = payload.decode(charset, errors="replace")
                    
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        body = part_body
                        break 
                    elif content_type == "text/html" and "attachment" not in content_disposition:
                        html_body = part_body
            except Exception as e:
                continue
        
        if not body and html_body:
            body = clean_html(html_body) if clean else html_body
    else:
        try:
            charset = msg.get_content_charset() or "utf-8"
            body = msg.get_payload(decode=True).decode(charset, errors="replace")
        except:
            body = "[Could not decode body]"
            
    return body.strip()

def test_gmail_connection(sender_filter=None, email_id=None, clean=False):
    imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not email_user or not email_password:
        print("❌ Error: EMAIL_USER or EMAIL_PASSWORD not found in .env file.")
        return

    print(f"🚀 Connecting to {imap_server}...")
    
    try:
        # Connect to the server
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, email_password)
        print("✅ Login successful!")

        # Select the inbox
        mail.select("inbox")

        if email_id:
            print(f"📄 Fetching content for Email ID: {email_id}...")
            res, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    from_ = msg.get("From")
                    date = msg.get("Date")
                    body = get_email_body(msg, clean=clean)
                    
                    print("-" * 50)
                    print(f"From: {from_}")
                    print(f"Date: {date}")
                    print(f"Subject: {subject}")
                    print("-" * 50)
                    print("BODY:")
                    print(body)
                    print("-" * 50)
                    print(f"Original length: {len(body)} characters")
        else:
            # Search for emails
            if sender_filter:
                print(f"🔍 Searching for emails from: {sender_filter}...")
                status, messages = mail.search(None, f'FROM "{sender_filter}"')
            else:
                print("🔍 Fetching the last 5 emails...")
                status, messages = mail.search(None, 'ALL')

            email_ids = messages[0].split()
            
            if not email_ids:
                print("ℹ️ No emails found matching the criteria.")
            else:
                # Get the last 5 email IDs
                last_5_ids = email_ids[-5:]
                print(f"\n📬 Found {len(email_ids)} emails. Showing last {len(last_5_ids)}:")
                print("-" * 50)

                for e_id in reversed(last_5_ids):
                    res, msg_data = mail.fetch(e_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            # Decode subject
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else "utf-8")
                            
                            # Get sender
                            from_ = msg.get("From")
                            date = msg.get("Date")
                            
                            print(f"ID: {e_id.decode()} | From: {from_} | Subject: {subject}")

        # Logout
        mail.logout()
        print("\n✅ Connection closed.")

    except Exception as e:
        print(f"\n❌ Failed to connect to Gmail: {e}")

if __name__ == "__main__":
    # Usage:
    # python gmail_test.py --filter "amazon.com"
    # python gmail_test.py --id 123
    import argparse
    parser = argparse.ArgumentParser(description="Test Gmail connection and fetch emails.")
    parser.add_argument("--filter", help="Filter emails by sender domain or address")
    parser.add_argument("--id", help="Fetch and show content for a specific email ID")
    parser.add_argument("--clean", action="store_true", help="Strip HTML tags from the body")
    
    args = parser.parse_args()
    test_gmail_connection(sender_filter=args.filter, email_id=args.id, clean=args.clean)
