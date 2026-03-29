import json
from typing import Dict, List, Any, Optional
from app.services.gemini_service import ask_gemini
from app.services.vector_service import add_chunks
from langchain.text_splitter import RecursiveCharacterTextSplitter


class ResumeAnalysisService:
    """
    Service for analyzing resumes using Google Gemini AI.
    Extracts key information, generates insights, and stores in vector database.
    """
    
    @staticmethod
    async def analyze_resume(resume_text: str, user_id: int, file_name: str) -> Dict[str, Any]:
        """
        Analyze resume using Gemini AI and extract structured information.
        
        Args:
            resume_text: Extracted text from resume PDF
            user_id: User ID for tracking
            file_name: Original resume file name
        
        Returns:
            Dictionary containing analysis results with structured data
        """
        try:
            # Create analysis prompt for Gemini
            analysis_prompt = f"""
            Analyze the following resume and extract key information in JSON format.
            
            Resume Content:
            {resume_text}
            
            Please provide a comprehensive analysis in the following JSON structure:
            {{
                "candidate_name": "Full name if found",
                "email": "Email address if found",
                "phone": "Phone number if found",
                "professional_summary": "Brief summary of the candidate's background",
                "skills": ["skill1", "skill2", "skill3", ...],
                "technical_skills": ["tech1", "tech2", ...],
                "soft_skills": ["skill1", "skill2", ...],
                "experience": [
                    {{
                        "position": "Job title",
                        "company": "Company name",
                        "duration": "Duration or dates",
                        "description": "Key responsibilities and achievements"
                    }}
                ],
                "education": [
                    {{
                        "degree": "Degree name",
                        "institution": "University/College name",
                        "year": "Graduation year",
                        "gpa": "GPA if mentioned"
                    }}
                ],
                "projects": [
                    {{
                        "title": "Project name",
                        "description": "What the project does",
                        "technologies": ["tech1", "tech2"],
                        "highlights": "Key achievements"
                    }}
                ],
                "certifications": ["cert1", "cert2", ...],
                "languages": ["language1", "language2", ...],
                "strengths": ["strength1", "strength2", ...],
                "areas_for_improvement": ["area1", "area2", ...],
                "overall_assessment": "Brief overall assessment of the candidate",
                "suitability_score": 0-100,
                "recommended_roles": ["role1", "role2", ...],
                "key_achievements": ["achievement1", "achievement2", ...]
            }}
            
            Ensure the response is valid JSON that can be parsed. If any field is not found in the resume, use null.
            """
            
            # Call Gemini API for analysis
            analysis_response = ask_gemini(analysis_prompt)
            
            # Parse the JSON response
            try:
                # Extract JSON from the response (in case Gemini adds extra text)
                json_start = analysis_response.find('{')
                json_end = analysis_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    analysis_json = json.loads(analysis_response[json_start:json_end])
                else:
                    analysis_json = json.loads(analysis_response)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis_json = {
                    "error": "Could not parse analysis",
                    "raw_analysis": analysis_response
                }
            
            # Generate recommendation insight
            recommendation_prompt = f"""
            Based on the following resume analysis, provide 3-5 specific, actionable recommendations 
            for improving this resume for placement/job opportunities:
            
            Analysis: {json.dumps(analysis_json, indent=2)}
            
            Provide recommendations in JSON array format:
            [
                {{"recommendation": "...", "priority": "high/medium/low"}},
                ...
            ]
            """
            
            recommendations_response = ask_gemini(recommendation_prompt)
            
            try:
                json_start = recommendations_response.find('[')
                json_end = recommendations_response.rfind(']') + 1
                if json_start != -1 and json_end > json_start:
                    recommendations = json.loads(recommendations_response[json_start:json_end])
                else:
                    recommendations = json.loads(recommendations_response)
            except json.JSONDecodeError:
                recommendations = []
            
            # Prepare final analysis result
            analysis_result = {
                "user_id": user_id,
                "file_name": file_name,
                "analysis": analysis_json,
                "recommendations": recommendations,
                "analysis_status": "completed"
            }
            
            return analysis_result
        
        except Exception as e:
            return {
                "user_id": user_id,
                "file_name": file_name,
                "analysis_status": "failed",
                "error": str(e)
            }
    
    @staticmethod
    async def store_analysis_in_vector_db(
        resume_text: str,
        analysis_data: Dict[str, Any],
        user_id: int
    ) -> List[str]:
        """
        Store resume content and analysis in vector database for semantic search.
        
        Args:
            resume_text: Original resume text
            analysis_data: Structured analysis from Gemini
            user_id: User ID
        
        Returns:
            List of chunk IDs stored in vector database
        """
        try:
            # Prepare texts to embed - combine resume with analysis insights
            texts_to_store = []
            metadata_list = []
            
            # Add original resume content
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            resume_chunks = splitter.split_text(resume_text)
            
            for i, chunk in enumerate(resume_chunks):
                texts_to_store.append(chunk)
                metadata_list.append({
                    "user_id": user_id,
                    "type": "resume_content",
                    "chunk_index": i
                })
            
            # Add analysis summary
            analysis_summary = f"""
            Candidate Profile Summary:
            Name: {analysis_data.get('candidate_name', 'Unknown')}
            
            Professional Summary: {analysis_data.get('professional_summary', '')}
            
            Key Skills: {', '.join(analysis_data.get('skills', [])[:10])}
            
            Technical Skills: {', '.join(analysis_data.get('technical_skills', [])[:10])}
            
            Experience: {len(analysis_data.get('experience', []))} positions
            
            Education: {', '.join([f"{e.get('degree')} from {e.get('institution')}" 
                                   for e in analysis_data.get('education', [])])}
            
            Key Achievements: {', '.join(analysis_data.get('key_achievements', [])[:5])}
            
            Overall Assessment: {analysis_data.get('overall_assessment', '')}
            """
            
            summary_chunks = splitter.split_text(analysis_summary)
            for i, chunk in enumerate(summary_chunks):
                texts_to_store.append(chunk)
                metadata_list.append({
                    "user_id": user_id,
                    "type": "analysis_summary",
                    "chunk_index": i
                })
            
            # Add chunks to vector store
            add_chunks(texts_to_store)
            
            return [f"user_{user_id}_chunk_{i}" for i in range(len(texts_to_store))]
        
        except Exception as e:
            print(f"Error storing analysis in vector DB: {str(e)}")
            return []
    
    @staticmethod
    async def generate_improvement_plan(
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a personalized improvement plan based on resume analysis.
        
        Args:
            analysis_data: Structured analysis from Gemini
        
        Returns:
            Improvement plan with actionable steps
        """
        try:
            improvement_prompt = f"""
            Based on the following resume analysis, create a detailed 30-60-90 day improvement plan 
            for the candidate to enhance their resume and career prospects:
            
            Analysis: {json.dumps(analysis_data.get('analysis', {}), indent=2)}
            
            Provide the plan in JSON format:
            {{
                "30_day_plan": [
                    {{"action": "...", "description": "...", "priority": "high/medium/low"}},
                    ...
                ],
                "60_day_plan": [...],
                "90_day_plan": [...],
                "skills_to_develop": ["skill1", "skill2", ...],
                "certifications_to_pursue": ["cert1", "cert2", ...],
                "projects_to_build": ["project1", "project2", ...],
                "interview_focus_areas": ["area1", "area2", ...]
            }}
            """
            
            plan_response = ask_gemini(improvement_prompt)
            
            try:
                json_start = plan_response.find('{')
                json_end = plan_response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    plan = json.loads(plan_response[json_start:json_end])
                else:
                    plan = json.loads(plan_response)
            except json.JSONDecodeError:
                plan = {"error": "Could not parse improvement plan"}
            
            return plan
        
        except Exception as e:
            return {"error": str(e)}


# Initialize the service
resume_analysis = ResumeAnalysisService()
