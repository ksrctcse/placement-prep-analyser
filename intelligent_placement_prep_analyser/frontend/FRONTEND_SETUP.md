# Frontend Setup Guide

## Overview
React frontend for Placement Prep Analyzer with authentication, student/staff dashboards, resume upload, and Gemini AI analysis.

## Features Implemented

### 1. **Authentication System**
- **Login Page** (`/login`)
  - Email and password authentication
  - Automatic role-based redirect (student/staff)
  - JWT token management
  - Password visibility toggle

- **Student Signup** (`/student/signup`)
  - Email, password, department, and batch selection
  - Form validation and error handling
  - Password confirmation
  - Automatic login after signup

- **Staff Signup** (`/staff/signup`)
  - Email, password, staff ID, and position
  - Form validation
  - Unique staff ID verification
  - Automatic login after signup

### 2. **Student Dashboard**
- **Resume Management**
  - Upload PDF resumes
  - File validation (PDF only, max 5MB)
  - Resume metadata tracking

- **AI Analysis Display**
  - Suitability score (0-100)
  - Professional summary
  - Extracted skills (technical & soft)
  - Recommended job roles
  - Education and experience details

- **Improvement Recommendations**
  - AI-generated recommendations
  - Priority levels (high/medium/low)
  - Actionable improvement suggestions

- **30-60-90 Day Improvement Plan**
  - Phased improvement roadmap
  - Skills to develop
  - Certifications to pursue
  - Project suggestions
  - Interview preparation focus areas

### 3. **Staff Dashboard**
- **Statistics Overview**
  - Total students count
  - Staff members count
  - Top performers tracking

- **Student Progress Table**
  - Student name, email, department, batch
  - Interview scores
  - Pagination and sorting
  - Action buttons for viewing resumes

- **Resume Inspection**
  - View student resumes
  - Full resume content display
  - Access to AI analysis data

- **Analysis Review**
  - View detailed resume analysis
  - Student skills assessment
  - Recommendations and feedback
  - Overall assessment and suitability score

## Project Structure

```
frontend/primereact-app/src/
├── pages/
│   ├── Login.js                   # Login page
│   ├── StudentSignup.js           # Student signup
│   ├── StaffSignup.js            # Staff signup
│   ├── StudentDashboard.js        # Student dashboard with resume upload
│   └── StaffDashboard.js         # Staff dashboard
├── components/
│   └── ProtectedRoute.js         # Route protection
├── context/
│   └── AuthContext.js            # Auth state management
├── services/
│   └── api.js                    # API client with interceptors
├── styles/
│   ├── Auth.css                  # Authentication pages styling
│   └── Dashboard.css             # Dashboard styling
└── App.js                        # Main app with routing
```

## Technology Stack

### Core
- **React** - UI library
- **React Router** - Client-side routing
- **Axios** - HTTP client

### UI Components
- **PrimeReact** - UI component library
- **PrimeIcons** - Icon library
- **CSS3** - Styling (with responsive design)

### State Management
- **React Context** - Authentication state
- **localStorage** - Token persistence

## Setup Instructions

### Prerequisites
```bash
node >= 14.0.0
npm >= 6.0.0
```

### Installation

1. **Install Dependencies**
```bash
cd frontend/primereact-app
npm install
```

2. **Install Additional Packages** (if not already installed)
```bash
npm install react-router-dom axios primereact primeicons
```

3. **Create Environment File**
Create `.env` in `frontend/primereact-app/`:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development
```

### Development Server

```bash
npm start
```

The app will start at `http://localhost:3000`

### Production Build

```bash
npm run build
```

Output will be in the `build/` directory.

## API Integration

### Authentication Endpoints
```
POST /auth/student/signup     - Student registration
POST /auth/staff/signup       - Staff registration
POST /auth/login              - User login (email + password)
GET  /auth/me                 - Get current user profile
```

### Student Endpoints
```
GET  /student/dashboard       - Get dashboard data
POST /resume/upload           - Upload and analyze resume
GET  /resume/my-resume        - Get student's resume
GET  /resume/analysis/my-analysis - Get resume analysis
POST /resume/analysis/{id}/improvement-plan - Get improvement plan
DELETE /resume/my-resume      - Delete resume
```

### Staff Endpoints
```
GET  /staff/dashboard         - Get staff dashboard
GET  /staff/students          - List all students
GET  /resume/{userId}         - Get student resume
GET  /resume/analysis/{resumeId} - Get resume analysis
```

## Authentication Flow

### Login/Signup
1. User submits credentials
2. Backend validates and hashes password
3. JWT token generated and returned
4. Token stored in localStorage
5. User redirected to appropriate dashboard
6. Token automatically added to all subsequent requests

### Token Management
- Token stored in `localStorage` as `token`
- User data stored as `user` (JSON)
- Axios interceptor adds token to all requests
- 401 responses trigger logout and redirect to login
- Token persists across page refreshes

## Component Communication

### AuthContext
Provides global auth state:
```javascript
{
  user,                  // Current user data
  token,                 // JWT token
  loading,               // Loading state
  isAuthenticated,       // Boolean
  isStudent,             // Boolean
  isStaff,               // Boolean
  login(),              // Login function
  studentSignup(),      // Student signup
  staffSignup(),        // Staff signup
  logout()              // Logout function
}
```

### API Service
Axios instance with:
- Base URL configuration
- Auth token injection
- Error handling
- Automatic logout on 401

### Protected Routes
Wrapper component for role-based access:
```javascript
<ProtectedRoute role="student">
  <StudentDashboard />
</ProtectedRoute>
```

## Styling

### Design System
- **Color Scheme**
  - Primary: #667eea (Purple)
  - Secondary: #764ba2 (Dark Purple)
  - Backgrounds: #f5f7fa
  - Text: #333

- **Component Styling**
  - PrimeReact theme: Lara Light Blue
  - Custom overrides for consistent branding
  - Responsive grid layouts
  - Flexbox for alignment

### Responsive Breakpoints
- Desktop: 1400px (max-width)
- Tablet: 768px breakpoint
- Mobile: < 768px

## Error Handling

### Frontend Errors
- Form validation messages
- API error toast notifications
- Automatic logout on auth failure
- Network error handling
- User-friendly error messages

### Toast Notifications
```javascript
toast.current?.show({
  severity: 'success|error|info|warning',
  summary: 'Title',
  detail: 'Message'
});
```

## CORS Configuration

Backend configured to accept requests from:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://localhost:3002`
- `http://127.0.0.1:3000` (and other ports)

## File Upload

### Resume Upload
- Accepted format: PDF only
- Max file size: 5MB
- Auto-starts upload on file selection
- Shows progress indicator
- Automatic analysis after upload
- User-friendly error messaging

## Security Features

1. **JWT Authentication**
   - Secure token-based auth
   - HTTPOnly flag on cookies (backend)

2. **Input Validation**
   - Form validation on frontend
   - Backend validation on API

3. **CORS Protection**
   - Whitelist approved origins
   - Credentials allowed only from origin

4. **Role-Based Access**
   - Protected routes by user role
   - Automatic redirects for unauthorized access

## Development Tips

### Debugging
```javascript
// Check stored token
console.log(localStorage.getItem('token'));

// Check user data
console.log(JSON.parse(localStorage.getItem('user')));

// API calls
// Check browser DevTools Network tab
```

### Common Issues

**Login fails with CORS error**
- Ensure backend CORS is configured
- Check ALLOW_ORIGINS in settings.py
- Verify API_URL is correct in .env

**Token not persisting**
- Check localStorage is enabled
- Clear cache and reload
- Verify token is being saved in AuthContext

**Cannot access student/staff endpoints**
- Verify user role is set correctly
- Check ProtectedRoute component
- Verify API returns correct user role

## Future Enhancements

- [ ] Remember me functionality
- [ ] Password reset flow
- [ ] Real-time notifications
- [ ] Dark mode toggle
- [ ] Profile editing
- [ ] Resume version history
- [ ] Export analysis as PDF
- [ ] Social media sharing
- [ ] Mobile app version
- [ ] Accessibility improvements

## Support & Troubleshooting

### Starting the app
```bash
npm start
```

### Build issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm start
```

### Backend connection issues
- Verify backend is running on port 8000
- Check `.env` REACT_APP_API_URL value
- Look at browser Console for network errors
- Check backend logs for API issues

## Additional Resources

- [PrimeReact Documentation](https://primereact.org/)
- [React Router Documentation](https://reactrouter.com/)
- [Axios Documentation](https://axios-http.com/)
- [React Context API](https://react.dev/reference/react/useContext)
