import google.generativeai as genai
from decouple import config
import os

# 1. Load Key
api_key = config('GEMINI_API_KEY', default=None)

if not api_key:
    print("❌ Error: API Key not found in .env")
else:
    print(f"✅ Key loaded: {api_key[:5]}...")
    
    # 2. Configure
    genai.configure(api_key=api_key)

    # 3. List Models
    print("\n🔍 Checking available models for this key...")
    try:
        count = 0
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"   - {m.name}")
                count += 1
        
        if count == 0:
            print("⚠️ No models found. Ensure 'Generative Language API' is enabled in Google Console.")
    except Exception as e:
        print(f"❌ Error listing models: {e}")