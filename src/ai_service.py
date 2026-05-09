import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.utils import get_expense_extraction_prompt

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL")

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

def extract_expense_from_email(email_content: str):
    prompt = get_expense_extraction_prompt(email_content)
    
    # Initialize client inside function or ensure global is ready
    # Since we validated in main.py, we just use the global client
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts expense data from emails into JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
