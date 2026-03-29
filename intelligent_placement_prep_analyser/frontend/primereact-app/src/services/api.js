import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  studentSignup: (data) => api.post('/auth/student/signup', data),
  staffSignup: (data) => api.post('/auth/staff/signup', data),
  login: (data) => api.post('/auth/login', data),
  getProfile: () => api.get('/auth/me'),
};

export const studentAPI = {
  getDashboard: () => api.get('/student/dashboard'),
  uploadResume: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getMyResume: () => api.get('/resume/my-resume'),
  getAnalysis: () => api.get('/resume/analysis/my-analysis'),
  getImprovementPlan: (resumeId) => api.post(`/resume/analysis/${resumeId}/improvement-plan`),
  deleteResume: () => api.delete('/resume/my-resume'),
};

export const staffAPI = {
  getDashboard: () => api.get('/staff/dashboard'),
  getStudents: () => api.get('/staff/students'),
  getStudentResume: (userId) => api.get(`/resume/${userId}`),
  getResumeAnalysis: (resumeId) => api.get(`/resume/analysis/${resumeId}`),
};

export default api;
