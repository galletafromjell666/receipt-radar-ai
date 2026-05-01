import os
import sys
import json
from openai import OpenAI
from dotenv import load_dotenv

from src.utils import get_expense_extraction_prompt, check_connections

load_dotenv()

def test_deepseek_connection(custom_email=None):
    if not check_connections():
        return

    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL")
    model = os.getenv("DEEPSEEK_MODEL")

    client = OpenAI(api_key=api_key, base_url=base_url)

    if custom_email:
        print(f"🚀 Testing expense extraction from custom email using {model}...")
        prompt = get_expense_extraction_prompt(custom_email)
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts expense data from emails into JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            print("\n✅ Success! Extracted JSON:")
            print(json.dumps(json.loads(response.choices[0].message.content), indent=2))
        except Exception as e:
            print(f"\n❌ Extraction failed: {e}")
    else:
        print(f"🚀 Testing simple connection to DeepSeek at {base_url} using {model}...")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Say 'Hello World! DeepSeek connection is working.'"}
                ],
                stream=False
            )
            print("\n✅ Success! Response:")
            print(response.choices[0].message.content)
        except Exception as e:
            print(f"\n❌ Connection failed: {e}")

if __name__ == "__main__":
    # Test with the specific email provided by the user if requested
    import sys as system_sys
    if len(system_sys.argv) > 1 and system_sys.argv[1] == "--email":
        sample_email = """From: notificaciones@bancocuscatlan.com 
Date: 2026-04-29 21:24:00
Subject: Compra con Tarjeta de Credito Titular 

Content: 
1213 
Estimado Cliente: GIOVANNI
Se ha realizado una compra con su tarjeta titular de Banco CUSCATLAN XXXXXXXXXX1111 por USD 5.30 en DeepSeek el día 2026-04-29 21:24. Consultas al 22122000."""
        test_deepseek_connection(custom_email=sample_email)
    else:
        test_deepseek_connection()
