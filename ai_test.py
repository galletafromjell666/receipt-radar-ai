import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_deepseek_connection():
    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    if not api_key:
        print("❌ Error: DEEPSEEK_API_KEY not found in .env file.")
        return

    print(f"🚀 Connecting to DeepSeek at {base_url} using {model}...")
    
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say 'Hello World! DeepSeek connection is working.'"}
            ],
            stream=False
        )
        
        print("\n✅ Success! Response from DeepSeek:")
        print(f"---")
        print(response.choices[0].message.content)
        print(f"---")
        
    except Exception as e:
        print(f"\n❌ Failed to connect to DeepSeek: {e}")

if __name__ == "__main__":
    test_deepseek_connection()
