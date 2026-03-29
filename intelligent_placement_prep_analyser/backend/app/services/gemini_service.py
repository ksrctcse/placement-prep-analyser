
import google.generativeai as genai
from app.config.settings import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

def ask_gemini(prompt):
    response=model.generate_content(prompt)
    return response.text
