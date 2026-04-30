import imaplib
import email
from email.header import decode_header
import os
import re
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

IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
PROCESSED_LABEL = "PROCESSED"

def connect_to_email():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASSWORD)
    return mail

def get_unprocessed_emails():
    mail = connect_to_email()
    mail.select("inbox")
    
    # Search for all emails in inbox
    # In a real scenario, we might search for emails NOT tagged with PROCESSED
    # but IMAP labels/tags vary by provider. For Gmail, we can use X-GM-LABELS.
    # For simplicity, let's search for UNSEEN or just all and we will check 
    # against our DB email_id later.
    status, messages = mail.search(None, 'ALL')
    
    email_ids = messages[0].split()
    results = []

    for e_id in email_ids[-20:]: # Limit to last 20 for now
        res, msg = mail.fetch(e_id, "(RFC822)")
        for response in msg:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                
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
                        except:
                            continue
                    
                    if not body and html_body:
                        body = clean_html(html_body) # Fallback to cleaned HTML
                else:
                    try:
                        charset = msg.get_content_charset() or "utf-8"
                        body = msg.get_payload(decode=True).decode(charset, errors="replace")
                    except:
                        body = ""

                results.append({
                    "email_id": e_id.decode(),
                    "subject": subject,
                    "body": body,
                    "sender": msg.get("From")
                })
    
    mail.logout()
    return results

def mark_as_processed(email_id):
    # This is provider specific. For generic IMAP, we can move it to a folder 
    # or add a keyword. 
    mail = connect_to_email()
    mail.select("inbox")
    # Add 'PROCESSED' keyword if supported, or just flag it
    mail.store(email_id, '+FLAGS', '\\Seen') 
    # If Gmail, we could do: mail.store(email_id, '+X-GM-LABELS', PROCESSED_LABEL)
    mail.logout()
