import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com" # Placeholder, check actual DeepSeek endpoint

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

def extract_expense_from_email(email_content: str):
    prompt = f"""
    Extract expense information from the following email content.
    Return the result as a JSON object with these keys:
    - amount (float)
    - currency (string, 3-letter code)
    - category (string, e.g., Food, Transport, Utilities, Entertainment, etc.)
    - merchant (string)
    - description (string)
    - date (string, ISO format if possible)

    Email content:
    {email_content}
    """

    response = client.chat.completions.create(
        model="deepseek-chat", # or deepseek-reasoner/flash
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts expense data from emails into JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
