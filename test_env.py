
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")

if api_key:
    print(f"✅ API Key loaded successfully!")
    print(f"Key starts with: {api_key[:10]}...")
else:
    print("❌ API Key not found. Check your .env file.")