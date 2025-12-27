import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load your key
load_dotenv("sec.env")
api_key = os.getenv("GOOGLE_API_KEY")

# Clean key (just in case)
if api_key:
    api_key = api_key.strip().replace("[", "").replace("]", "")
    genai.configure(api_key=api_key)

    print("🔎 Checking available models for your key...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ AVAILABLE: {m.name}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ No API Key found in sec.env")