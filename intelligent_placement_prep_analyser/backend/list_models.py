#!/usr/bin/env python3
"""List all available Google Generative AI models for text generation"""

import os
from dotenv import load_dotenv

# Load .env from backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(backend_dir, '.env')
load_dotenv(env_file)

try:
    import google.generativeai as genai
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ No API key found in GOOGLE_API_KEY")
        exit(1)
    
    genai.configure(api_key=api_key)
    
    print("=" * 70)
    print("📋 AVAILABLE MODELS FOR TEXT GENERATION")
    print("=" * 70)
    
    models = genai.list_models()
    text_gen_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
    
    print(f"\nFound {len(text_gen_models)} available text generation models:\n")
    
    for model in text_gen_models:
        clean_name = model.name.replace("models/", "")
        print(f"  ✅ {clean_name}")
    
    print(f"\n{'='*70}")
    
    if text_gen_models:
        print("\n🎯 RECOMMENDATION:")
        # Try to pick the best one
        clean_names = [m.name.replace("models/", "") for m in text_gen_models]
        
        best = None
        for candidate in ["gemini-2.0-flash-exp", "gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-1.5-pro-latest", "gemini-1.5-pro", "gemini-pro"]:
            if candidate in clean_names:
                best = candidate
                break
        
        if not best and clean_names:
            best = clean_names[0]
        
        if best:
            print(f"  Use: {best}")
            print(f"\n  Update your code:")
            print(f'    model = genai.GenerativeModel("{best}")')
    else:
        print("\n❌ No text generation models available!")
        print("   This usually means:")
        print("   1. Your API key is invalid or doesn't have access")
        print("   2. You're using an older/limited API tier")
        print("   3. Your project needs to enable Generative AI API")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
