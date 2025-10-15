from dotenv import load_dotenv
import os

load_dotenv()
print(f"Current directory: {os.getcwd()}")
print(f"API Key found: {os.environ.get('GROQ_API_KEY') is not None}")
print(f".env file exists: {os.path.exists('.env')}")