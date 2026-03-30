#!/usr/bin/env python3
import google.generativeai as genai
import os

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print("Testing different Gemini models...\n")

models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
    "gemini-1.5-flash-latest",
    "gemini-2.0-pro",
    "gemini-1.5-pro-latest"
]

for model_name in models_to_test:
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say OK")
        if response.text:
            print(f"✅ {model_name} - WORKING")
        else:
            print(f"⚠️  {model_name} - No response")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg:
            print(f"❌ {model_name} - Not available")
        elif "overloaded" in error_msg or "quota" in error_msg:
            print(f"⚠️  {model_name} - Quota/Overloaded (but available)")
        else:
            print(f"⚠️  {model_name} - Error: {error_msg[:80]}")
