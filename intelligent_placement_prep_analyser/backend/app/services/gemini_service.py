
import google.generativeai as genai
from app.config.settings import settings
import json

genai.configure(api_key=settings.GOOGLE_API_KEY)
# Use gemini-2.5-flash (newest, fastest, and available in your API tier)
# Available options in your account: gemini-2.5-flash, gemini-2.0-flash, gemini-2.5-pro
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
except:
    # Fallback to gemini-2.0-flash if 2.5 not available
    model = genai.GenerativeModel("gemini-2.0-flash")

def ask_gemini(prompt):
    response=model.generate_content(prompt)
    return response.text


def generate_mcq_questions(content: str, topic_title: str, num_questions: int = 5):
    """
    Generate MCQ questions from topic content using Gemini
    
    Args:
        content: The topic/passage content to generate questions from
        topic_title: Title of the topic
        num_questions: Number of MCQ questions to generate
    
    Returns:
        List of MCQ dictionaries with question, options, and correct answer
    """
    prompt = f"""
    Based on the following content about "{topic_title}", generate {num_questions} multiple choice questions.
    
    Content:
    {content}
    
    For each question, provide:
    1. A clear question
    2. Four options (A, B, C, D)
    3. The correct option (A, B, C, or D)
    4. A brief explanation
    
    Return the response as a JSON array with this structure:
    [
        {{
            "question": "Question text?",
            "option_a": "Option A",
            "option_b": "Option B",
            "option_c": "Option C",
            "option_d": "Option D",
            "correct_option": "A",
            "explanation": "Why A is correct..."
        }}
    ]
    
    Only return valid JSON, no additional text.
    """
    
    try:
        response = ask_gemini(prompt)
        # Parse JSON response
        mcqs = json.loads(response)
        return mcqs if isinstance(mcqs, list) else [mcqs]
    except json.JSONDecodeError:
        # If JSON parsing fails, create placeholder MCQ
        return [{
            "question": f"What is a key concept in {topic_title}?",
            "option_a": "Sample answer 1",
            "option_b": "Sample answer 2",
            "option_c": "Sample answer 3",
            "option_d": "Sample answer 4",
            "correct_option": "A",
            "explanation": f"This relates to the content of {topic_title}"
        }]
    except Exception as e:
        print(f"Error generating MCQs: {e}")
        return []

