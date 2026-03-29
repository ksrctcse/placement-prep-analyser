
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './StudentDashboard.css';

const StudentDashboard = () => {
  const [activeMenu, setActiveMenu] = useState('dashboard');
  const [studentName, setStudentName] = useState('');
  const [studentRoll, setStudentRoll] = useState('');
  const [department, setDepartment] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [topics, setTopics] = useState([]);
  const [tests, setTests] = useState([]);
  const [interviews, setInterviews] = useState([]);
  const [resumeInfo, setResumeInfo] = useState(null);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [resumeFile, setResumeFile] = useState(null);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = React.useRef(null);
  const navigate = useNavigate();

  const API_BASE = 'http://localhost:8003';
  const token = localStorage.getItem('access_token');
  const authHeader = `Bearer ${token}`;

  useEffect(() => {
    if (!token) {
      navigate('/auth');
      return;
    }

    if (activeMenu === 'dashboard') {
      fetchDashboardData();
    } else if (activeMenu === 'topics') {
      fetchTopics();
    } else if (activeMenu === 'tests') {
      fetchTests();
    } else if (activeMenu === 'interviews') {
      fetchInterviews();
    } else if (activeMenu === 'resume') {
      fetchResumeInfo();
    }
  }, [activeMenu]);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API_BASE}/student/dashboard`, {
        headers: { 'Authorization': authHeader }
      });
      setDashboardData(response.data);
      setStudentName(response.data.student_name);
      setStudentRoll(response.data.student_roll);
      setDepartment(response.data.department);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      setMessage({ type: 'error', text: 'Failed to load dashboard' });
    }
  };

  const fetchTopics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/student/topics`, {
        headers: { 'Authorization': authHeader }
      });
      setTopics(response.data);
    } catch (error) {
      console.error('Error fetching topics:', error);
      setMessage({ type: 'error', text: 'Failed to load topics' });
    }
  };

  const fetchTests = async () => {
    try {
      const response = await axios.get(`${API_BASE}/student/tests`, {
        headers: { 'Authorization': authHeader }
      });
      setTests(response.data);
    } catch (error) {
      console.error('Error fetching tests:', error);
      setMessage({ type: 'error', text: 'Failed to load tests' });
    }
  };

  const fetchInterviews = async () => {
    try {
      const response = await axios.get(`${API_BASE}/student/interviews`, {
        headers: { 'Authorization': authHeader }
      });
      setInterviews(response.data);
    } catch (error) {
      console.error('Error fetching interviews:', error);
      setMessage({ type: 'error', text: 'Failed to load interviews' });
    }
  };

  const fetchResumeInfo = async () => {
    try {
      const response = await axios.get(`${API_BASE}/student/resume`, {
        headers: { 'Authorization': authHeader }
      });
      setResumeInfo(response.data);
    } catch (error) {
      console.error('Error fetching resume:', error);
      setMessage({ type: 'error', text: 'Failed to load resume info' });
    }
  };

  const validateAndSetFile = (file) => {
    const ext = file.name.split('.').pop().toLowerCase();
    const validExts = ['pdf', 'doc', 'docx'];
    
    if (!validExts.includes(ext)) {
      setMessage({ type: 'error', text: 'Only PDF, DOC, and DOCX files are allowed' });
      return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
      setMessage({ type: 'error', text: 'File size exceeds 10MB limit' });
      return;
    }
    
    setResumeFile(file);
    setMessage({ type: '', text: '' });
  };

  const handleResumeFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const handleFileInputClick = () => {
    if (fileInputRef.current && !uploadingResume) {
      fileInputRef.current.click();
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (uploadingResume) return;
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (uploadingResume) return;

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      validateAndSetFile(files[0]);
    }
  };

  const handleUploadResume = async (e) => {
    e.preventDefault();
    
    if (!resumeFile) {
      setMessage({ type: 'error', text: 'Please select a resume file' });
      return;
    }

    setUploadingResume(true);
    try {
      const formData = new FormData();
      formData.append('file', resumeFile);

      const response = await axios.post(
        `${API_BASE}/student/upload-resume`,
        formData,
        {
          headers: {
            'Authorization': authHeader,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setMessage({ type: 'success', text: response.data.message });
      setResumeFile(null);
      setTimeout(() => {
        fetchResumeInfo();
      }, 1500);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to upload resume';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setUploadingResume(false);
    }
  };

  const handleStartTest = (testId) => {
    navigate(`/test/${testId}`);
  };

  const handleStartInterview = (interviewId) => {
    navigate(`/interview/${interviewId}`);
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API_BASE}/auth/logout`, {}, {
        headers: { 'Authorization': authHeader }
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    navigate('/auth');
  };

  return (
    <div className="student-dashboard">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>Student Portal</h2>
          <p className="student-info">{studentName}</p>
          <p className="roll-number">Roll: {studentRoll}</p>
        </div>

        <nav className="sidebar-menu">
          <button
            className={`menu-item ${activeMenu === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveMenu('dashboard')}
          >
            📊 Dashboard
          </button>
          <button
            className={`menu-item ${activeMenu === 'topics' ? 'active' : ''}`}
            onClick={() => setActiveMenu('topics')}
          >
            📚 Topics
          </button>
          <button
            className={`menu-item ${activeMenu === 'tests' ? 'active' : ''}`}
            onClick={() => setActiveMenu('tests')}
          >
            📝 Take Test
          </button>
          <button
            className={`menu-item ${activeMenu === 'interviews' ? 'active' : ''}`}
            onClick={() => setActiveMenu('interviews')}
          >
            🎤 Take Interview
          </button>
          <button
            className={`menu-item ${activeMenu === 'resume' ? 'active' : ''}`}
            onClick={() => setActiveMenu('resume')}
          >
            📄 Upload Resume
          </button>
        </nav>

        <button className="logout-btn" onClick={handleLogout}>
          🚪 Logout
        </button>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {message.text && (
          <div className={`message ${message.type}`}>
            {message.text}
            <button onClick={() => setMessage({ type: '', text: '' })} className="close-msg">×</button>
          </div>
        )}

        {/* Dashboard View */}
        {activeMenu === 'dashboard' && dashboardData && (
          <div className="dashboard-view">
            <h1>Welcome, {dashboardData.student_name}!</h1>
            <p className="subtitle">Department: {dashboardData.department}</p>

            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-icon">📝</div>
                <div className="metric-content">
                  <p className="metric-label">Tests Taken</p>
                  <p className="metric-value">{dashboardData.metrics.total_tests_taken}</p>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">🎤</div>
                <div className="metric-content">
                  <p className="metric-label">Interviews Taken</p>
                  <p className="metric-value">{dashboardData.metrics.total_interviews_taken}</p>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">📊</div>
                <div className="metric-content">
                  <p className="metric-label">Avg Test Score</p>
                  <p className="metric-value">{dashboardData.metrics.avg_test_score}%</p>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">⭐</div>
                <div className="metric-content">
                  <p className="metric-label">Avg Interview Score</p>
                  <p className="metric-value">{dashboardData.metrics.avg_interview_score}%</p>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">📄</div>
                <div className="metric-content">
                  <p className="metric-label">Resume</p>
                  <p className="metric-value">{dashboardData.metrics.resume_uploaded ? '✓ Uploaded' : '✗ Not Uploaded'}</p>
                </div>
              </div>
            </div>

            <div className="recent-section">
              <h2>Recent Test Attempts</h2>
              {dashboardData.recent_test_attempts && dashboardData.recent_test_attempts.length > 0 ? (
                <table className="recent-table">
                  <thead>
                    <tr>
                      <th>Test Title</th>
                      <th>Score</th>
                      <th>Status</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardData.recent_test_attempts.map((test) => (
                      <tr key={test.id}>
                        <td>{test.test_title}</td>
                        <td>{test.score ? `${test.score}%` : 'N/A'}</td>
                        <td><span className={`status ${test.status}`}>{test.status}</span></td>
                        <td>{new Date(test.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="no-data">No test attempts yet</p>
              )}
            </div>
          </div>
        )}

        {/* Topics View */}
        {activeMenu === 'topics' && (
          <div className="topics-view">
            <h1>Available Topics</h1>
            {topics.length > 0 ? (
              <div className="topics-grid">
                {topics.map((topic) => (
                  <div key={topic.id} className="topic-card">
                    <div className="topic-header">
                      <h3>{topic.title}</h3>
                    </div>
                    <p className="topic-description">{topic.description || 'No description provided'}</p>
                    <div className="topic-meta">
                      <span className="staff-name">👨‍🏫 {topic.staff_name}</span>
                      <span className="topic-date">{new Date(topic.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-data">No topics available yet</p>
            )}
          </div>
        )}

        {/* Tests View */}
        {activeMenu === 'tests' && (
          <div className="tests-view">
            <h1>Available Tests</h1>
            {tests.length > 0 ? (
              <div className="tests-grid">
                {tests.map((test) => (
                  <div key={test.id} className="test-card">
                    <div className="test-header">
                      <h3>{test.title}</h3>
                      {test.attempted && <span className="badge attempted">✓ Attempted</span>}
                    </div>
                    <p className="test-description">{test.description || 'No description'}</p>
                    <div className="test-meta">
                      <span className="topic-info">📚 {test.topic_title}</span>
                      <span className="staff-info">👨‍🏫 {test.staff_name}</span>
                    </div>
                    <button 
                      className="start-btn"
                      onClick={() => handleStartTest(test.id)}
                      disabled={test.attempted}
                    >
                      {test.attempted ? 'Already Attempted' : 'Start Test'}
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-data">No tests available yet</p>
            )}
          </div>
        )}

        {/* Interviews View */}
        {activeMenu === 'interviews' && (
          <div className="interviews-view">
            <h1>Available Interviews</h1>
            {interviews.length > 0 ? (
              <div className="interviews-grid">
                {interviews.map((interview) => (
                  <div key={interview.id} className="interview-card">
                    <div className="interview-header">
                      <h3>{interview.title}</h3>
                      {interview.attempted && <span className="badge attempted">✓ Attempted</span>}
                    </div>
                    <p className="interview-description">{interview.description || 'No description'}</p>
                    <div className="interview-meta">
                      <span className="topic-info">📚 {interview.topic_title}</span>
                      <span className="staff-info">👨‍🏫 {interview.staff_name}</span>
                    </div>
                    <button 
                      className="start-btn"
                      onClick={() => handleStartInterview(interview.id)}
                      disabled={interview.attempted}
                    >
                      {interview.attempted ? 'Already Attempted' : 'Start Interview'}
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-data">No interviews available yet</p>
            )}
          </div>
        )}

        {/* Resume View */}
        {activeMenu === 'resume' && (
          <div className="resume-view">
            <h1>Resume Management</h1>
            
            <div className="resume-content">
              <div className="resume-upload">
                <h2>Upload Resume</h2>
                <form onSubmit={handleUploadResume} className="resume-form">
                  <div className="form-group">
                    <label htmlFor="resumeFile">Select Resume (PDF, DOC, DOCX - Max 10MB)</label>
                    <div 
                      className={`file-input-wrapper ${dragActive ? 'drag-active' : ''}`}
                      onDragEnter={handleDrag}
                      onDragLeave={handleDrag}
                      onDragOver={handleDrag}
                      onDrop={handleDrop}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        id="resumeFile"
                        accept=".pdf,.doc,.docx"
                        onChange={handleResumeFileChange}
                        disabled={uploadingResume}
                      />
                      <div 
                        className="file-display"
                        onClick={handleFileInputClick}
                        role="button"
                        tabIndex={uploadingResume ? -1 : 0}
                        onKeyDown={(e) => {
                          if ((e.key === 'Enter' || e.key === ' ') && !uploadingResume) {
                            handleFileInputClick();
                          }
                        }}
                      >
                        {resumeFile ? (
                          <span className="file-selected">✓ {resumeFile.name}</span>
                        ) : (
                          <span className="file-placeholder">Click to select or drag and drop</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <button 
                    type="submit" 
                    className="submit-btn"
                    disabled={uploadingResume}
                  >
                    {uploadingResume ? 'Uploading...' : 'Upload Resume'}
                  </button>
                </form>
              </div>

              {resumeInfo && resumeInfo.resume ? (
                <div className="resume-info">
                  <h2>Current Resume</h2>
                  <div className="resume-details">
                    <div className="detail-item">
                      <span className="label">File Size:</span>
                      <span className="value">{(resumeInfo.resume.file_size / 1024).toFixed(2)} KB</span>
                    </div>
                    <div className="detail-item">
                      <span className="label">Uploaded:</span>
                      <span className="value">{new Date(resumeInfo.resume.uploaded_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="no-resume">
                  <p>📄 No resume uploaded yet</p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default StudentDashboard;
