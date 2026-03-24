
from app.services.gemini_service import ask_gemini
from app.services.vector_service import search_resume

def generate_question():
    docs=search_resume("skills")
    context=docs[0].page_content if docs else ""

    prompt=f'''
Generate a technical interview question based on:

{context}
'''
    return ask_gemini(prompt)

def evaluate_answer(answer):
    prompt=f'''
Evaluate this interview answer

Answer:
{answer}

Provide:
Score out of 10
Strengths
Weakness
Improvement tips
'''
    return ask_gemini(prompt)
