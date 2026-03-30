#!/usr/bin/env python3
"""Find which Gemini models are available in your API tier"""
import google.generativeai as genai
import os

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ GOOGLE_API_KEY not set")
    exit(1)

genai.configure(api_key=api_key)

print("=" * 70)
print("🔍 AVAILABLE MODELS IN YOUR API TIER")
print("=" * 70)

print("\nListing all available models...\n")

available_models = []
for model in genai.list_models():
    if "generateContent" in model.supported_generation_methods:
        available_models.append(model.name)
        # Extract just the model name (remove 'models/' prefix)
        display_name = model.name.replace("models/", "")
        print(f"✅ {display_name}")

print(f"\n{'='*70}")
print(f"Total available models: {len(available_models)}")
print(f"{'='*70}")

if available_models:
    print("\n✨ RECOMMENDED MODEL TO USE:")
    # Try to find the best model
    recommended = None
    if any("gemini-pro-vision" in m for m in available_models):
        recommended = "gemini-pro-vision"
    elif any("gemini-pro" in m for m in available_models):
        recommended = "gemini-pro"
    elif available_models:
        recommended = available_models[0].replace("models/", "")
    
    if recommended:
        print(f"  → {recommended}")
    
    print("\nFull list of available model names for code:")
    for m in available_models:
        clean_name = m.replace("models/", "")
        print(f"    - {clean_name}")
else:
    print("❌ No models available! Check your API key and project.")
