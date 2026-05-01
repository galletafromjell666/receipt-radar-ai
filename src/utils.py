def get_expense_extraction_prompt(email_content):
    """
    Returns the standard prompt used for extracting expense data from email content.
    """
    return f"""
    Extract expense information from the following email content.
    Return the result as a JSON object with these keys:
    - amount (float)
    - currency (string, 3-letter code)
    - category (string, e.g., Food, Transport, Utilities, Entertainment, etc.)
    - merchant (string)
    - source (string, the bank or financial institution, e.g., Banco Cuscatlan)
    - account (string, the specific card or account identifier, e.g., XXXXXXXXXX9104, we just need the last 4 digits without the Xs or whatever is available)
    - description (string)
    - date (string, ISO format. If no date is mentioned in the content, use the "Date:" field provided in the metadata)

    Constraint: Use only ASCII. Replace accented letters (á->a, ñ->n) and remove other special characters from string values.

    Email content:
    {email_content}
    """

def format_email_for_ai(msg):
    """
    Consolidates subject, sender, date, and cleaned body into a single string for the AI.
    """
    from bs4 import BeautifulSoup
    
    subject = msg.subject
    sender = msg.from_
    # msg.date is a datetime object in imap-tools
    date_str = msg.date.strftime("%Y-%m-%d %H:%M:%S") if hasattr(msg, 'date') and msg.date else "Unknown"
    
    # Get the raw content (prefer plain text, fallback to HTML)
    raw_content = msg.text if msg.text else msg.html
    
    if msg.html and not msg.text:
        # Clean HTML if only HTML is available
        soup = BeautifulSoup(raw_content, "html.parser")
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        body = '\n'.join(chunk for chunk in chunks if chunk)
    else:
        body = raw_content

    return f"From: {sender}\nDate: {date_str}\nSubject: {subject}\n\nContent:\n{body}"

def clean_html(html_content):
    """Use BeautifulSoup for robust HTML to text conversion."""
    from bs4 import BeautifulSoup
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
