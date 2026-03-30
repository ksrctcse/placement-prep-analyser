"""
MCQ Generation Agent - Generates MCQ questions from topic content using Gemini AI
Uses vector search to find relevant content from embedded topic chunks
"""

import json
import google.generativeai as genai
from app.config.settings import settings
from app.services.vector_service import search_topic
from sqlalchemy.orm import Session
from app.database.models import Topic, StudentProfile
from typing import List, Dict, Optional

genai.configure(api_key=settings.GOOGLE_API_KEY)
# Use gemini-2.5-flash (newest, fastest, and available in your API tier)
# Available options in your account: gemini-2.5-flash, gemini-2.0-flash, gemini-2.5-pro
try:
    model = genai.GenerativeModel("gemini-2.5-flash")
except:
    # Fallback to gemini-2.0-flash if 2.5 not available
    model = genai.GenerativeModel("gemini-2.0-flash")


def extract_json_from_response(text: str) -> Optional[List[Dict]]:
    """
    Extract JSON array from Gemini response text.
    Handles cases where JSON is wrapped in markdown code blocks.
    """
    try:
        # Try direct JSON parse first
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from markdown code blocks
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end > start:
            try:
                return json.loads(text[start:end].strip())
            except json.JSONDecodeError:
                pass
    
    # Try to extract from regular backticks
    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            try:
                return json.loads(text[start:end].strip())
            except json.JSONDecodeError:
                pass
    
    # Try to find JSON array in the text
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    
    return None


def generate_mcqs_from_topics(
    db: Session,
    topic_ids: List[int],
    student_id: int,
    num_questions: int = 10,
    min_questions: int = 10,
    max_questions: int = 10
) -> Dict:
    """
    Generate MCQ questions from selected topics using AI agent.
    Uses embedded chunks from indexed PDFs for high-quality content.
    ENFORCES MINIMUM 10 AND MAXIMUM 10 QUESTIONS from embeddings.
    
    Args:
        db: Database session
        topic_ids: List of topic IDs to generate questions from
        student_id: Student ID creating the test
        num_questions: Target number of questions (default 10, enforced at 10)
        min_questions: Minimum questions to generate (default 10 - MINIMUM ENFORCED for embeddings)
        max_questions: Maximum questions to generate (default 10 - MAXIMUM ENFORCED)
    
    Returns:
        Dictionary with generated MCQs and metadata
    """
    
    # ENFORCE MINIMUM 10 AND MAXIMUM 10 QUESTIONS FOR EMBEDDINGS
    # Always request 10 questions when generating from indexed PDFs
    max_questions = 10
    min_questions = 10
    num_questions = 10
    
    print(f"\n📊 MCQ Generation Configuration:")
    print(f"   Min Questions (enforced): {min_questions}")
    print(f"   Target Questions: {num_questions}")
    print(f"   Max Questions (enforced): {max_questions}")
    
    # Get student profile for department/section context
    student = db.query(StudentProfile).filter(
        StudentProfile.id == student_id
    ).first()
    
    if not student:
        return {"error": "Student profile not found", "mcqs": []}
    
    # Get topics
    topics = db.query(Topic).filter(Topic.id.in_(topic_ids)).all()
    
    if not topics:
        return {"error": "No topics found", "mcqs": []}
    
    print(f"\n📚 Generating exactly {num_questions} MCQs from {len(topics)} topic(s) using indexed content")
    
    all_mcqs = []
    indexed_content_samples = {}  # Store indexed content for deduplication
    
    # Distribute 10 questions across topics
    # If single topic, get all 10 from it; if multiple, distribute evenly
    if len(topics) == 1:
        questions_per_topic = 10
        remaining_questions = 0
    else:
        questions_per_topic = num_questions // len(topics)
        remaining_questions = num_questions % len(topics)
    
    for idx, topic in enumerate(topics):
        # Determine questions for this topic
        topic_questions = questions_per_topic
        if idx < remaining_questions:
            topic_questions += 1
        
        if topic_questions == 0:
            continue
        
        print(f"\n🔍 Processing Topic: '{topic.title}' (ID: {topic.id}, Indexed: {topic.is_indexed})")
        
        # Get comprehensive content from embedded chunks
        content = _retrieve_topic_content(topic)
        indexed_content_samples[topic.id] = content
        
        if not content or content.strip() == "":
            print(f"⚠️  WARNING: No content retrieved for topic '{topic.title}'")
            print(f"   Topic is_indexed: {topic.is_indexed}, embedding_chunks: {topic.embedding_chunks}")
        
        # Generate MCQs using AI agent with diversity focus
        # If topic is indexed (from uploaded PDF), ensure we get at least 10 questions
        is_from_embeddings = topic.is_indexed and topic.embedding_chunks > 0
        
        if is_from_embeddings:
            # For indexed topics, ALWAYS generate minimum 10 MCQs
            mcqs_needed = max(topic_questions, 10)
            print(f"✍️  Generating {mcqs_needed} MCQs from indexed PDF content...")
        else:
            mcqs_needed = topic_questions
            print(f"✍️  Generating {mcqs_needed} MCQs from topic information...")
        
        try:
            mcqs = _generate_mcqs_with_agent(
                topic_title=topic.title,
                content=content,
                num_questions=mcqs_needed,
                department=student.department.name if student.department else "General",
                topic_id=topic.id,
                is_from_embeddings=is_from_embeddings,
                min_questions=10 if is_from_embeddings else 1  # Minimum 10 for embeddings
            )
            
            if mcqs and len(mcqs) >= (10 if is_from_embeddings else 1):
                # Deduplicate against indexed content
                deduplicated_mcqs = _deduplicate_mcqs(mcqs, content)
                
                # If from embeddings and have fewer than 10 after dedup, try to generate more
                if is_from_embeddings and len(deduplicated_mcqs) < 10:
                    print(f"⚠️  Only {len(deduplicated_mcqs)} unique MCQs after deduplication (need 10 minimum)")
                    print(f"   Attempting to generate more MCQs to reach minimum 10...")
                    additional_mcqs = _generate_mcqs_with_agent(
                        topic_title=topic.title,
                        content=content,
                        num_questions=10 - len(deduplicated_mcqs),
                        department=student.department.name if student.department else "General",
                        topic_id=topic.id,
                        is_from_embeddings=True,
                        min_questions=1
                    )
                    if additional_mcqs:
                        additional_dedup = _deduplicate_mcqs(additional_mcqs, content)
                        deduplicated_mcqs.extend(additional_dedup)
                
                print(f"✅ Generated {len(deduplicated_mcqs)} MCQs for '{topic.title}' from indexed content")
                all_mcqs.extend(deduplicated_mcqs)
            else:
                generated_count = len(mcqs) if mcqs else 0
                print(f"❌ Failed to generate enough MCQs for '{topic.title}'")
                print(f"   Generated: {generated_count}, Needed: {mcqs_needed}")
                print(f"   From Embeddings: {is_from_embeddings}")
                if is_from_embeddings:
                    print(f"   ⚠️  WARNING: PDF has insufficient content or AI generation failed")
                    print(f"   → Attempting fallback MCQs to reach minimum 10")
                    # Create fallback MCQs to reach minimum 10 for indexed topics
                    fallback_count = max(10 - len(all_mcqs), topic_questions)
                    fallback_mcqs = _create_fallback_mcqs(
                        topic_title=topic.title,
                        num_questions=fallback_count,
                        topic_id=topic.id
                    )
                    all_mcqs.extend(fallback_mcqs)
                else:
                    # For non-indexed topics, use fallback if needed
                    fallback_mcqs = _create_fallback_mcqs(
                        topic_title=topic.title,
                        num_questions=topic_questions,
                        topic_id=topic.id
                    )
                    all_mcqs.extend(fallback_mcqs)
        except Exception as e:
            print(f"❌ Exception generating MCQs for topic '{topic.title}': {e}")
            import traceback
            traceback.print_exc()
            # Create fallback MCQs if agent fails
            if is_from_embeddings:
                # For indexed topics, ensure we get at least 10 fallback MCQs
                fallback_count = max(10 - len(all_mcqs), topic_questions)
            else:
                fallback_count = topic_questions
            fallback_mcqs = _create_fallback_mcqs(
                topic_title=topic.title,
                num_questions=fallback_count,
                topic_id=topic.id
            )
            all_mcqs.extend(fallback_mcqs)
        
        # Enforce maximum 10 questions limit
        if len(all_mcqs) >= num_questions:
            all_mcqs = all_mcqs[:num_questions]
            break
    
    # Final enforcement: ensure we don't exceed 10 questions
    final_mcqs = all_mcqs[:max_questions]
    
    print(f"\n✅ MCQ Generation Complete: {len(final_mcqs)}/{num_questions} questions generated")
    
    return {
        "success": True,
        "total_questions": len(final_mcqs),
        "target_questions": num_questions,
        "max_questions": max_questions,
        "topics_count": len(topics),
        "department": student.department.name if student.department else "General",
        "section": student.section,
        "mcqs": final_mcqs
    }


def _retrieve_topic_content(topic: Topic) -> str:
    """
    Retrieve comprehensive content from embedded chunks for a topic.
    Uses multiple search queries to extract different aspects of the topic.
    
    Args:
        topic: Topic object with embedded chunks
    
    Returns:
        String containing consolidated content from embeddings
    """
    
    if not topic.is_indexed or topic.embedding_chunks == 0:
        print(f"  ℹ️  Topic is not indexed. Using basic content.")
        return f"Topic: {topic.title}\nDescription: {topic.description or 'No description available'}"
    
    print(f"  🔎 Retrieving {topic.embedding_chunks} indexed chunks from vector store...")
    
    # Define multiple search queries to extract different aspects
    search_queries = [
        # Main concepts
        f"main concepts key topics core ideas {topic.title}",
        # Definitions
        f"definitions terminology {topic.title}",
        # Practical applications
        f"applications practical examples use cases {topic.title}",
        # Advanced topics
        f"advanced concepts advanced topics deep dive {topic.title}",
        # Problem solving techniques
        f"techniques methods strategies algorithms {topic.title}",
    ]
    
    all_chunks = []
    seen_content = set()  # Avoid duplicates
    
    for query in search_queries:
        try:
            results = search_topic(
                topic_id=topic.id,
                query=query,
                k=5  # Get top 5 relevant chunks per query
            )
            
            if results:
                print(f"  ✓ Found {len(results)} chunks for query: '{query[:40]}...'")
                for result in results:
                    content = result.get("content", "").strip()
                    if content and content not in seen_content:
                        all_chunks.append(content)
                        seen_content.add(content)
            else:
                print(f"  ✗ No results for query: '{query[:40]}...'")
        
        except Exception as e:
            print(f"  ⚠️  Error searching for query '{query[:40]}...': {e}")
            continue
    
    if all_chunks:
        print(f"  📦 Retrieved {len(all_chunks)} unique chunks from {len(search_queries)} search queries")
        content = "\n\n".join(all_chunks)
    else:
        print(f"  ⚠️  No chunks found from vector store, using basic content")
        content = f"Topic: {topic.title}\nDescription: {topic.description or 'No description available'}"
    
    return content


def _deduplicate_mcqs(mcqs: List[Dict], indexed_content: str) -> List[Dict]:
    """
    Remove MCQs that are too similar to the indexed content (verbatim duplicates).
    This ensures we generate new questions, not exact copies from the content.
    
    Args:
        mcqs: List of generated MCQs
        indexed_content: Original indexed content from embeddings
    
    Returns:
        List of deduplicated MCQs
    """
    
    if not indexed_content:
        return mcqs
    
    # Convert content to lowercase for comparison
    content_lower = indexed_content.lower()
    content_sentences = [s.strip() for s in indexed_content.split('.') if s.strip()]
    
    deduplicated = []
    
    for mcq in mcqs:
        question = mcq.get("question", "").lower()
        
        # Check if question is verbatim in content (allow partial matches for interpretation)
        is_verbatim = any(
            sent.lower() in question or question in sent.lower() 
            for sent in content_sentences 
            if len(sent) > 20
        )
        
        if not is_verbatim:
            deduplicated.append(mcq)
        else:
            print(f"  ⚠️  Skipped verbatim question: '{mcq.get('question', '')[:60]}...'")
    
    return deduplicated


def _generate_mcqs_with_agent(
    topic_title: str,
    content: str,
    num_questions: int,
    department: str,
    topic_id: int,
    is_from_embeddings: bool = False,
    min_questions: int = 1
) -> List[Dict]:
    """
    Internal function to generate MCQs using Gemini AI agent.
    Creates diverse questions combining direct content questions and derived questions.
    
    Args:
        topic_title: Title of the topic
        content: Content to generate questions from (from embeddings or basic info)
        num_questions: Number of questions to generate (max 10)
        department: Department for context
        topic_id: Topic ID for tracking
        is_from_embeddings: Whether content is from vector embeddings (True) or fallback (False)
    
    Returns:
        List of generated MCQ dictionaries
    """
    
    source_indicator = "indexed course materials (uploaded PDFs)" if is_from_embeddings else "topic information"
    
    # For embedded content, ensure we generate enough questions
    # Minimum 10 questions if from embeddings, otherwise use requested amount
    actual_num_questions = max(num_questions, min_questions) if is_from_embeddings else num_questions
    
    # Determine question types to ensure diversity
    num_direct_questions = max(1, actual_num_questions // 2)  # 50% directly from content
    num_derived_questions = actual_num_questions - num_direct_questions  # Rest derived from content
    
    prompt = f"""You are an expert educator creating MCQ questions for placement preparation exams.

Your task: Create exactly {actual_num_questions} diverse multiple-choice questions based on the provided {source_indicator} about "{topic_title}" 
for students of {department} department.

**CRITICAL REQUIREMENT**: You MUST generate EXACTLY {actual_num_questions} questions - no more, no less.

**QUESTION DIVERSITY REQUIREMENT** (CRITICAL):
- Create {num_direct_questions} DIRECT questions: Directly based on specific facts, definitions, or concepts from the material
- Create {num_derived_questions} DERIVED questions: Questions inspired by the material but testing understanding, application, or analysis
- DO NOT generate the same question twice
- DO NOT copy questions that appear verbatim in the content
- Questions must be distinct and test different aspects

**SOURCE MATERIAL**:
=====================================================
COURSE MATERIAL & CONTENT:
=====================================================
{content}
=====================================================

**Requirements**:
1. All questions MUST originate from the provided material above - no external knowledge
2. Mix difficulty levels: Easy (25%), Medium (50%), Hard (25%)
3. DIRECT QUESTIONS: Extract from specific sections and test recall/comprehension
4. DERIVED QUESTIONS: Test application, analysis, comparison, or problem-solving based on material
5. Each question must test a distinct concept/skill
6. Options must be plausible with only ONE correct answer
7. Explanations must reference the material and explain why answer is correct
8. Use professional language suitable for placement exams
9. NO trivial or obvious questions
10. NO duplicate or near-duplicate questions

**Output Format**: Return ONLY a valid JSON array with EXACTLY {actual_num_questions} questions.
No markdown, no extra text. Valid JSON only.

[
    {{
        "question": "What is...",
        "option_a": "First option",
        "option_b": "Second option",
        "option_c": "Third option",
        "option_d": "Fourth option",
        "correct_option": "B",
        "explanation": "Option B is correct because... (reference specific parts of the material)"
    }},
    ... ({actual_num_questions} total questions) ...
]

IMPORTANT: RETURN EXACTLY {actual_num_questions} QUESTIONS - NO MORE, NO LESS.
Ensure all questions originate from the provided material. Create diverse questions covering different concepts."""

    try:
        print(f"    📤 Sending request to Gemini API for {actual_num_questions} questions...")
        print(f"    📝 Prompt length: {len(prompt)} characters")
        print(f"    📋 Content length: {len(content)} characters")
        if is_from_embeddings:
            print(f"    📄 Source: Indexed PDF content (minimum {min_questions} required)")
        
        response = model.generate_content(prompt)
        print(f"    ✓ Received response from Gemini API")
        
        # Log response info for debugging
        response_text = response.text
        print(f"    📖 Response length: {len(response_text)} characters")
        print(f"    🔍 First 200 chars of response: {response_text[:200]}")
        
        # Extract and parse JSON
        mcqs_data = extract_json_from_response(response_text)
        
        if not mcqs_data:
            print(f"    ❌ Failed to extract JSON from response")
            print(f"    📄 Full response text:")
            print(f"---START RESPONSE---")
            print(response_text)
            print(f"---END RESPONSE---")
            return []
        
        if not isinstance(mcqs_data, list):
            print(f"    ❌ Extracted data is not a list: {type(mcqs_data)}")
            print(f"    📄 Data: {mcqs_data}")
            return []
        
        print(f"    ✓ Successfully extracted list with {len(mcqs_data)} items")
        
        # Check if we have enough questions
        if len(mcqs_data) < actual_num_questions:
            print(f"    ⚠️  Expected {actual_num_questions} questions but got {len(mcqs_data)}")
        
        # Validate and add metadata to each MCQ
        valid_mcqs = []
        invalid_count = 0
        
        for idx, mcq in enumerate(mcqs_data):
            if _validate_mcq(mcq):
                mcq["topic_id"] = topic_id
                mcq["difficulty"] = _estimate_difficulty(idx, len(mcqs_data))
                mcq["source"] = "embeddings" if is_from_embeddings else "fallback"
                valid_mcqs.append(mcq)
                print(f"      ✅ Q{idx + 1} valid: '{mcq.get('question', '')[:50]}...'")
            else:
                invalid_count += 1
                print(f"      ❌ Q{idx + 1} invalid: {mcq}")
        
        print(f"    📊 Validation summary: {len(valid_mcqs)} valid, {invalid_count} invalid")
        
        if valid_mcqs:
            # For embeddings, we need at least min_questions
            if is_from_embeddings and len(valid_mcqs) < min_questions:
                print(f"    ⚠️  Only {len(valid_mcqs)} valid MCQs (need minimum {min_questions} for embeddings)")
                return valid_mcqs  # Return what we have, caller will retry or use fallback
            
            print(f"    ✅ {len(valid_mcqs)} questions validated successfully")
            return valid_mcqs[:actual_num_questions]  # Return exactly actual_num_questions
        else:
            print(f"    ❌ No valid MCQs after validation")
            print(f"    📄 Extracted data was: {mcqs_data}")
            return []
    
    except Exception as e:
        print(f"    ❌ Error in MCQ generation agent: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return []


def _validate_mcq(mcq: Dict) -> bool:
    """
    Validate MCQ structure to ensure all required fields are present and correct.
    
    Args:
        mcq: MCQ dictionary to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["question", "option_a", "option_b", "option_c", "option_d", "correct_option", "explanation"]
    
    # Check all required fields exist
    missing_fields = [field for field in required_fields if field not in mcq]
    if missing_fields:
        print(f"        Missing fields: {missing_fields}")
        return False
    
    # Check correct_option is valid
    correct_opt = mcq.get("correct_option", "").upper()
    if correct_opt not in ["A", "B", "C", "D"]:
        print(f"        Invalid correct_option: '{mcq.get('correct_option')}' (must be A, B, C, or D)")
        return False
    
    # Check all options have content
    for opt_key in ["option_a", "option_b", "option_c", "option_d"]:
        opt_val = mcq.get(opt_key, "").strip()
        if not opt_val:
            print(f"        Empty {opt_key}")
            return False
    
    # Check question and explanation have content
    question = mcq.get("question", "").strip()
    explanation = mcq.get("explanation", "").strip()
    
    if not question:
        print(f"        Empty question")
        return False
    
    if not explanation:
        print(f"        Empty explanation")
        return False
    
    if len(question) < 10:
        print(f"        Question too short: '{question}'")
        return False
    
    return True


def _estimate_difficulty(question_index: int, total_questions: int) -> str:
    """Estimate difficulty level based on position in questions"""
    if question_index < total_questions // 3:
        return "easy"
    elif question_index < 2 * total_questions // 3:
        return "medium"
    else:
        return "hard"


def _create_fallback_mcqs(
    topic_title: str,
    num_questions: int,
    topic_id: int
) -> List[Dict]:
    """
    Create fallback MCQs when agent generation fails.
    These are generic questions that use topic information as base.
    
    Args:
        topic_title: Title of the topic
        num_questions: Number of questions needed
        topic_id: Topic ID
    
    Returns:
        List of fallback MCQ dictionaries
    """
    
    print(f"    ⚠️  Using fallback MCQ generation mode (less detailed)")
    
    fallback_questions = [
        {
            "question": f"Which of the following is a fundamental concept in {topic_title}?",
            "option_a": "Basic concept from the topic",
            "option_b": "Another related concept",
            "option_c": "Alternative approach",
            "option_d": "Common misconception",
            "correct_option": "A",
            "explanation": "This is a fundamental concept in {topic_title}. Please review the course materials for detailed understanding.",
            "topic_id": topic_id,
            "difficulty": "easy",
            "source": "fallback"
        },
        {
            "question": f"How would you approach solving a problem using {topic_title}?",
            "option_a": "Systematic analysis approach",
            "option_b": "Trial and error method",
            "option_c": "Random selection method",
            "option_d": "Intuition-based method",
            "correct_option": "A",
            "explanation": "The systematic approach is the most appropriate method. Review the course materials for specific techniques.",
            "topic_id": topic_id,
            "difficulty": "medium",
            "source": "fallback"
        },
        {
            "question": f"Which scenario best demonstrates the application of {topic_title}?",
            "option_a": "Real-world application scenario",
            "option_b": "Theoretical scenario",
            "option_c": "Hypothetical scenario",
            "option_d": "Unrelated scenario",
            "correct_option": "A",
            "explanation": "This scenario correctly demonstrates how {topic_title} is applied in practice.",
            "topic_id": topic_id,
            "difficulty": "medium",
            "source": "fallback"
        }
    ]
    
    return fallback_questions[:num_questions]


def store_mcqs_in_database(
    db: Session,
    test_id: int,
    mcqs: List[Dict],
    topic_ids: List[int],
    student_id: int
) -> Dict:
    """
    Store generated MCQs in the database with proper student-topic mapping.
    
    Args:
        db: Database session
        test_id: Test ID to associate questions with
        mcqs: List of MCQ dictionaries to store
        topic_ids: List of topic IDs the questions belong to
        student_id: Student ID for tracking
    
    Returns:
        Dictionary with storage status and metrics
    """
    
    from app.database.models import Test, TestQuestion, Topic
    
    try:
        # Get the test
        test = db.query(Test).filter(Test.id == test_id).first()
        if not test:
            return {"error": "Test not found", "stored_count": 0}
        
        # Get topics for this test
        topics = db.query(Topic).filter(Topic.id.in_(topic_ids)).all()
        topic_map = {t.id: t for t in topics}
        
        stored_count = 0
        
        # Store each MCQ with proper mapping
        for idx, mcq_data in enumerate(mcqs):
            try:
                # Get the topic ID for this question (from mcq_data or round-robin distribution)
                question_topic_id = mcq_data.get("topic_id")
                if not question_topic_id or question_topic_id not in topic_map:
                    # Round-robin distribution if topic not specified
                    question_topic_id = topic_ids[idx % len(topic_ids)]
                
                # Create TestQuestion with all required fields
                question = TestQuestion(
                    test_id=test_id,
                    question_text=mcq_data.get("question", ""),
                    option_a=mcq_data.get("option_a", ""),
                    option_b=mcq_data.get("option_b", ""),
                    option_c=mcq_data.get("option_c", ""),
                    option_d=mcq_data.get("option_d", ""),
                    correct_option=mcq_data.get("correct_option", "A"),
                    explanation=mcq_data.get("explanation", ""),
                    topic_id=question_topic_id
                )
                
                db.add(question)
                stored_count += 1
                
                print(f"  ✓ Stored Q{idx + 1}: '{mcq_data.get('question', '')[:50]}...' (Topic ID: {question_topic_id})")
                
            except Exception as e:
                print(f"  ⚠️  Error storing question {idx + 1}: {e}")
                continue
        
        # Commit all questions
        db.commit()
        
        print(f"\n✅ Successfully stored {stored_count}/{len(mcqs)} questions in database")
        print(f"   Test ID: {test_id}")
        print(f"   Student ID: {student_id}")
        print(f"   Topics: {', '.join([f'ID:{t}' for t in topic_ids])}")
        
        return {
            "success": True,
            "test_id": test_id,
            "stored_count": stored_count,
            "total_count": len(mcqs),
            "student_id": student_id,
            "topic_ids": topic_ids,
            "message": f"Stored {stored_count} questions with student-topic mapping"
        }
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error storing MCQs in database: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "stored_count": 0,
            "success": False
        }

