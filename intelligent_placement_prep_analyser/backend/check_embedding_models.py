#!/usr/bin/env python3
"""Check available embedding models from Google Generative AI"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory
backend_dir = Path(__file__).parent
env_file = backend_dir / ".env"
load_dotenv(env_file)

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    import google.generativeai as genai
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env")
        exit(1)
    
    print("🔍 Attempting to connect to Google Generative AI API...")
    genai.configure(api_key=api_key)
    
    print("\n📋 Listing all available models:")
    print("-" * 80)
    
    try:
        models = genai.list_models()
        
        embedding_models = []
        for model in models:
            # Check if this is an embedding model
            if 'embedding' in model.name.lower() or 'embed' in model.name.lower():
                embedding_models.append(model)
                print(f"\n✓ {model.name}")
                if hasattr(model, 'display_name'):
                    print(f"  Display: {model.display_name}")
                if hasattr(model, 'supported_generation_methods'):
                    print(f"  Methods: {model.supported_generation_methods}")
                if hasattr(model, 'description'):
                    print(f"  Description: {model.description}")
        
        if not embedding_models:
            print("\n⚠️  No specific embedding models found. Showing ALL available models:")
            print("-" * 80)
            for model in models:
                print(f"  - {model.name}")
                if hasattr(model, 'supported_generation_methods'):
                    print(f"    Methods: {model.supported_generation_methods}")
        
        print("\n" + "-" * 80)
        print(f"\nTotal embedding models found: {len(embedding_models)}")
        
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        print("\nTrying alternative approach with direct API call...")
        
        # Try direct API call
        from google.ai.generativelanguage_v1beta.services.generative_service import GenerativeServiceClient
        client = GenerativeServiceClient(api_key=api_key)
        try:
            response = client.list_models()
            print(f"Found {len(response.models)} models")
            for model in response.models:
                print(f"  - {model.name}")
        except Exception as e2:
            print(f"Alternative approach also failed: {e2}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
