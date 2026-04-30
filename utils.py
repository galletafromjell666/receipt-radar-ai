def format_email_for_ai(msg):
    """
    Consolidates subject, sender, and cleaned body into a single string for the AI.
    """
    from bs4 import BeautifulSoup
    
    subject = msg.subject
    sender = msg.from_
    
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

    return f"From: {sender}\nSubject: {subject}\n\nContent:\n{body}"

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
