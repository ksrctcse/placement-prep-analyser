# Quick Start Guide

## 🚀 Start Backend Server

```bash
cd /Users/arunkumaraswamy/Documents/Study/placement-prep-analyser/intelligent_placement_prep_analyser/backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend runs at:** `http://localhost:8000`
**API Docs:** `http://localhost:8000/docs`

---

## 🎨 Start Frontend Server

```bash
cd /Users/arunkumaraswamy/Documents/Study/placement-prep-analyser/intelligent_placement_prep_analyser/frontend/primereact-app

# Install dependencies (if not already done)
npm install

# Start development server
npm start
```

**Frontend runs at:** `http://localhost:3000`

---

## 📝 Test Login Credentials

### Student Account
```
Email: student@example.com
Password: securepassword123
Department: CSE
Batch: 2024-2027
```

Or create a new account at: `http://localhost:3000/student/signup`

### Staff Account
```
Email: staff@example.com
Password: securepassword123
Staff ID: STAFF001
Position: Associate Professor
```

Or create a new account at: `http://localhost:3000/staff/signup`

---

## ✨ Key Features to Try

### 1. **Student Login & Resume Upload**
1. Go to `http://localhost:3000/login`
2. Click "Sign up here" for Student signup
3. Fill in the form and click "Sign Up"
4. You'll be automatically logged in to Student Dashboard
5. Click "Upload Resume (PDF)" 
6. Select a PDF file (you can create a test PDF or use any college-related PDF)
7. The system will automatically:
   - Extract text from the PDF
   - Analyze with Google Gemini AI
   - Generate suitability score
   - Create recommendations
   - Generate 30-60-90 day improvement plan

### 2. **View Analysis**
1. After upload, click "View Analysis" button
2. See AI breakdown of:
   - Candidate information
   - Work experience
   - Education
   - Overall assessment
   - Recommended roles

### 3. **30-60-90 Day Plan**
1. Click "Improvement Plan" button
2. See phased improvement roadmap for 3 months
3. Includes skills to develop, certifications, projects

### 4. **Staff Dashboard**
1. Sign up as staff: `http://localhost:3000/staff/signup`
2. View all students in the system
3. Click eye icon to view student resume
4. View AI analysis for each student
5. See statistics (total students, top performers, etc.)

---

## 📋 API Endpoints to Test

### Authentication
```bash
# Student Signup
curl -X POST http://localhost:8000/auth/student/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123",
    "department": "CSE",
    "batch": "2024-2027"
  }'

# Staff Signup
curl -X POST http://localhost:8000/auth/staff/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prof Smith",
    "email": "smith@example.com",
    "password": "password123",
    "staff_id": "STAFF001",
    "position": "Professor"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'
```

### Resume Operations
```bash
# Upload Resume (requires auth token)
curl -X POST http://localhost:8000/resume/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/resume.pdf"

# Get My Resume
curl -X GET http://localhost:8000/resume/my-resume \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get Resume Analysis
curl -X GET http://localhost:8000/resume/analysis/my-analysis \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get Improvement Plan
curl -X POST http://localhost:8000/resume/analysis/1/improvement-plan \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔍 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process on port 8000
kill -9 <PID>

# Try starting again
uvicorn app.main:app --reload
```

### Frontend Won't Start
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm start
```

### Can't Upload Resume
- Ensure it's a PDF file
- File size must be under 5MB
- Backend must be running
- Check browser console for errors

### Login Not Working
1. Check backend is running (`http://localhost:8000/docs`)
2. Verify credentials are correct
3. Check browser console for network errors
4. Clear localStorage: 
   ```javascript
   localStorage.clear()
   ```
   Then try again

### API Docs
- **Backend API Documentation:** `http://localhost:8000/docs`
- **Alternative format:** `http://localhost:8000/redoc`

---

## 📊 Database

### Check Database
```bash
# Connect to PostgreSQL
psql -U postgres -d academic_analyser

# View users
SELECT id, name, email, role FROM users;

# View resumes
SELECT id, user_id, file_name FROM resumes;

# View analyses
SELECT id, resume_id, suitability_score FROM resume_analyses;
```

---

## 🎯 Complete User Flow

### Student Flow
```
1. Sign up at /student/signup
   ↓
2. Auto-login to /student/dashboard
   ↓
3. Upload resume (PDF)
   ↓
4. Gemini AI analyzes resume automatically
   ↓
5. View analysis scores and recommendations
   ↓
6. Click "Improvement Plan" for 30-60-90 day plan
   ↓
7. View detailed analysis in dialog
```

### Staff Flow
```
1. Sign up at /staff/signup
   ↓
2. Auto-login to /staff/dashboard
   ↓
3. See all students in table
   ↓
4. Click eye icon to view student resume
   ↓
5. Click "View Analysis" button
   ↓
6. See detailed AI analysis of student resume
   ↓
7. Scroll through recommendations and assessment
```

---

## 📚 Important Files

### Frontend
- **Pages:** `/src/pages/*.js` - All page components
- **Auth:** `/src/context/AuthContext.js` - Authentication state
- **API:** `/src/services/api.js` - API client
- **Styling:** `/src/styles/*.css` - Custom styles
- **Routes:** `/src/App.js` - Routing configuration

### Backend
- **Auth Routes:** `/app/routes/auth_routes.py` - Login/signup endpoints
- **Resume Routes:** `/app/routes/resume_routes.py` - Resume upload/analysis
- **Gemini Service:** `/app/services/resume_analysis_service.py` - AI analysis
- **Database Models:** `/app/database/models.py` - User, Resume, ResumeAnalysis
- **Config:** `/app/config/settings.py` - Environment variables

---

## 🛠️ Development Tips

### See API Requests in Browser
1. Open DevTools (F12)
2. Go to Network tab
3. Perform an action
4. Watch API calls in real-time

### Enable Redux DevTools
The app uses Context API, check Redux DevTools for state changes

### Check Stored Data
```javascript
// In browser console
localStorage.getItem('token')    // JWT token
localStorage.getItem('user')     // User object
```

### Enable API Debugging
```javascript
// In app/services/api.js, uncomment logging
// Logs all requests and responses
```

---

## ✅ Verification Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can access `http://localhost:8000/docs`
- [ ] Can access `http://localhost:3000`
- [ ] Student signup works
- [ ] Can login with credentials
- [ ] Can upload PDF resume
- [ ] Resume analysis displays
- [ ] Staff can view student resumes
- [ ] Improvement plan generates

---

## 🎉 Ready to Go!

If all checks pass, your system is fully operational!

**Next Steps:**
1. Create test student accounts
2. Upload test resumes
3. View AI analysis
4. Invite staff to use dashboard
5. Customize as needed

---

## 📞 Support

For issues:
1. Check backend logs: `uvicorn app.main:app --reload`
2. Check browser console (F12 → Console)
3. Check network requests (F12 → Network)
4. Review documentation files in project root

Good luck! 🚀
