/**
 * Authentication API service
 * Handles all authentication-related API calls
 */
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8003';

const api = axios.create({
  baseURL: `${API_URL}/auth`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_role');
      localStorage.removeItem('user_id');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: (email, password) =>
    api.post('/login', { email, password }),

  staffSignup: (name, email, departmentId, password, confirmPassword) =>
    api.post('/staff/signup', {
      name,
      email,
      department_id: departmentId,
      password,
      confirm_password: confirmPassword,
    }),

  studentSignup: (name, email, departmentId, section, password, confirmPassword) =>
    api.post('/student/signup', {
      name,
      email,
      department_id: departmentId,
      section,
      password,
      confirm_password: confirmPassword,
    }),

  getDepartments: () =>
    api.get('/departments'),

  forgotPassword: (email) =>
    api.post('/forgot-password', { email }),

  verifyToken: (token) =>
    api.get(`/verify-token?token=${token}`),

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_id');
  },
};

export default authService;
