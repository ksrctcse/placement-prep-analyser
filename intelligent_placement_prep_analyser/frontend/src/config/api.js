// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003'

export const API_ENDPOINTS = {
  STUDENT_DASHBOARD: `${API_BASE_URL}/student/dashboard`,
  STAFF_STUDENTS_PROGRESS: `${API_BASE_URL}/staff/students-progress`,
  RESUME_UPLOAD: `${API_BASE_URL}/resume/upload`,
  INTERVIEW_ANALYSIS: `${API_BASE_URL}/interview/analyze`
}

export default API_BASE_URL
