#!/usr/bin/env python3
"""List available Google Generative AI embedding models"""

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
    
    print("📋 Available embedding models:")
    print("-" * 60)
    
    models = genai.list_models()
    embedding_models = [m for m in models if 'embed' in m.name.lower()]
    
    if not embedding_models:
        print("No embedding models found. All models:")
        for model in models:
            print(f"  - {model.name}")
    else:
        for model in embedding_models:
            print(f"  ✓ {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"    Methods: {model.supported_generation_methods}")
    
    print("-" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
