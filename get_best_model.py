import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. Setup
load_dotenv("sec.env")
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: No API Key found in sec.env")
    exit()

# Clean key
api_key = api_key.strip().replace("[", "").replace("]", "")
genai.configure(api_key=api_key)

print("🔎 Scanning for available models...")

try:
    # 2. Get all models that support generating text
    my_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            my_models.append(m.name)
            print(f"   Found: {m.name}")

    # 3. Logic to pick the "Best" one automatically
    # We prefer 1.5 Pro > 1.5 Flash > 1.0 Pro
    best_model = None
    
    # Check for specific priority models
    if "models/gemini-1.5-pro-latest" in my_models:
        best_model = "gemini-1.5-pro-latest"
    elif "models/gemini-1.5-pro" in my_models:
        best_model = "gemini-1.5-pro"
    elif "models/gemini-1.5-flash" in my_models:
        best_model = "gemini-1.5-flash"
    elif "models/gemini-pro" in my_models:
        best_model = "gemini-pro"
    else:
        # Fallback: just take the first one found
        if my_models:
            best_model = my_models[0].replace("models/", "")

    # 4. Save to file
    if best_model:
        with open("latest-model.txt", "w") as f:
            f.write(best_model)
        
        print("\n✅ SUCCESS!")
        print(f"   Selected Model: {best_model}")
        print(f"   Saved to: latest-model.txt")
    else:
        print("❌ Error: No valid Gemini models found for this key.")

except Exception as e:
    print(f"❌ Connection Error: {e}")