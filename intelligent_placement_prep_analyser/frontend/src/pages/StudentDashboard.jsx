
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
  const [testResults, setTestResults] = useState([]);
  const [topicPerformance, setTopicPerformance] = useState(null);
  const [selectedTestAnalysis, setSelectedTestAnalysis] = useState(null);
  const [resumeInfo, setResumeInfo] = useState(null);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [resumeFile, setResumeFile] = useState(null);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [dragActive, setDragActive] = useState(false);
  const [selectedTopicIds, setSelectedTopicIds] = useState([]);
  const [generatedMCQs, setGeneratedMCQs] = useState([]);
  const [showTestBuilder, setShowTestBuilder] = useState(false);
  const [isGeneratingMCQs, setIsGeneratingMCQs] = useState(false);
  const [isCreatingTest, setIsCreatingTest] = useState(false);
  const [testName, setTestName] = useState('');
  const [loadingResults, setLoadingResults] = useState(false);
  const [menuLoading, setMenuLoading] = useState(false);
  const [topicTests, setTopicTests] = useState({});
  const [expandedTopicId, setExpandedTopicId] = useState(null);
  const [showDialog, setShowDialog] = useState(false);
  const [dialogType, setDialogType] = useState(''); // 'already_attempted' or 'pending_tests'
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [pendingTestsList, setPendingTestsList] = useState([]);
  const [attemptedTestsList, setAttemptedTestsList] = useState([]);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [testToDelete, setTestToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [showResultsDetail, setShowResultsDetail] = useState(false);
  const [selectedAttemptDetails, setSelectedAttemptDetails] = useState(null);
  const [loadingAttemptDetails, setLoadingAttemptDetails] = useState(false);
  const [createdTestInfo, setCreatedTestInfo] = useState(null);
  const [topicAttemptedInfo, setTopicAttemptedInfo] = useState({});
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
    } else if (activeMenu === 'results') {
      fetchTestResults();
      fetchTopicPerformance();
    } else if (activeMenu === 'resume') {
      fetchResumeInfo();
    }
  }, [activeMenu]);

  // Refresh tests and dashboard data when user comes back to the page (e.g., from test submission)
  useEffect(() => {
    if (!token) return;

    const handleFocus = () => {
      if (activeMenu === 'tests') {
        fetchTests();
      } else if (activeMenu === 'dashboard') {
        fetchDashboardData();
      } else if (activeMenu === 'results') {
        fetchTestResults();
        fetchTopicPerformance();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [activeMenu, token]);

  const fetchDashboardData = async () => {
    setMenuLoading(true);
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
    } finally {
      setMenuLoading(false);
    }
  };

  const fetchTopics = async () => {
    setMenuLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/student/topics`, {
        headers: { 'Authorization': authHeader }
      });
      setTopics(response.data);
    } catch (error) {
      console.error('Error fetching topics:', error);
      setMessage({ type: 'error', text: 'Failed to load topics' });
    } finally {
      setMenuLoading(false);
    }
  };

  const fetchTests = async () => {
    setMenuLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/student/tests`, {
        headers: { 'Authorization': authHeader }
      });
      setTests(response.data);
    } catch (error) {
      console.error('Error fetching tests:', error);
      setMessage({ type: 'error', text: 'Failed to load tests' });
    } finally {
      setMenuLoading(false);
    }
  };

  const fetchInterviews = async () => {
    setMenuLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/student/interviews`, {
        headers: { 'Authorization': authHeader }
      });
      setInterviews(response.data);
    } catch (error) {
      console.error('Error fetching interviews:', error);
      setMessage({ type: 'error', text: 'Failed to load interviews' });
    } finally {
      setMenuLoading(false);
    }
  };

  const fetchResumeInfo = async () => {
    setMenuLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/student/resume`, {
        headers: { 'Authorization': authHeader }
      });
      setResumeInfo(response.data);
    } catch (error) {
      console.error('Error fetching resume:', error);
      setMessage({ type: 'error', text: 'Failed to load resume info' });
    } finally {
      setMenuLoading(false);
    }
  };

  const fetchTestResults = async () => {
    setMenuLoading(true);
    setLoadingResults(true);
    try {
      const response = await axios.get(`${API_BASE}/student/test-builder/student-test-history`, {
        headers: { 'Authorization': authHeader }
      });
      setTestResults(response.data.test_history || []);
    } catch (error) {
      console.error('Error fetching test results:', error);
      setMessage({ type: 'error', text: 'Failed to load test results' });
    } finally {
      setLoadingResults(false);
      setMenuLoading(false);
    }
  };

  const fetchTopicPerformance = async () => {
    try {
      const response = await axios.get(`${API_BASE}/student/test-builder/topic-performance-summary`, {
        headers: { 'Authorization': authHeader }
      });
      setTopicPerformance(response.data);
    } catch (error) {
      console.error('Error fetching topic performance:', error);
      setMessage({ type: 'error', text: 'Failed to load topic performance' });
    }
  };

  const fetchTestAnalysis = async (testAttemptId) => {
    try {
      const response = await axios.get(
        `${API_BASE}/student/test-builder/test-analysis/${testAttemptId}`,
        { headers: { 'Authorization': authHeader } }
      );
      setSelectedTestAnalysis(response.data.analysis);
    } catch (error) {
      console.error('Error fetching test analysis:', error);
      setMessage({ type: 'error', text: 'Failed to load test analysis' });
    }
  };

  const handleDeleteTest = async () => {
    if (!testToDelete) {
      console.error('❌ No test selected for deletion');
      setMessage({ type: 'error', text: 'No test selected' });
      return;
    }

    const testId = testToDelete.id;
    console.log('🗑️ Starting deletion for test:', testId, testToDelete.title);

    try {
      setDeleting(true);
      
      // Build the DELETE URL
      const deleteUrl = `${API_BASE}/student/test-builder/tests/${testId}`;
      console.log('📍 API URL:', deleteUrl);
      console.log('🔐 Authorization header:', authHeader ? 'Present' : 'Missing');

      // Make the DELETE request
      const response = await axios.delete(deleteUrl, {
        headers: {
          'Authorization': authHeader,
          'Content-Type': 'application/json'
        }
      });

      console.log('✅ Delete response:', response.status, response.data);

      if (response.data && response.data.success) {
        console.log('🎉 Test deleted successfully');
        setMessage({ 
          type: 'success', 
          text: `Test "${testToDelete.title}" deleted successfully` 
        });
        
        // Close dialog and reset
        setShowDeleteConfirm(false);
        setTestToDelete(null);
        
        // Refresh the data
        setTimeout(() => {
          fetchTests();
          fetchDashboardData();
        }, 500);
      } else {
        throw new Error('Delete returned success=false');
      }
    } catch (error) {
      console.error('❌ Delete error:', error);
      
      let errorMsg = 'Failed to delete test';
      
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
        errorMsg = error.response.data?.detail || error.response.data?.message || errorMsg;
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      setMessage({ type: 'error', text: errorMsg });
      setShowDeleteConfirm(false);
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteClick = (test) => {
    console.log('Delete clicked for test:', test);
    setTestToDelete(test);
    setShowDeleteConfirm(true);
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
    setTestToDelete(null);
  };

  const handleViewTestResults = async (test) => {
    console.log('📊 Fetching results for test:', test.id);
    
    if (!test.attempt_id) {
      console.error('No attempt_id found for test');
      setMessage({ type: 'error', text: 'Test attempt not found' });
      return;
    }

    try {
      setLoadingAttemptDetails(true);
      
      const response = await axios.get(
        `${API_BASE}/student/test-attempt/${test.attempt_id}/details`,
        { headers: { 'Authorization': authHeader } }
      );
      
      console.log('✅ Results fetched:', response.data);
      
      setSelectedAttemptDetails(response.data);
      setShowResultsDetail(true);
    } catch (error) {
      console.error('❌ Error fetching results:', error);
      let errorMsg = 'Failed to load test results';
      
      if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      }
      
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setLoadingAttemptDetails(false);
    }
  };

  const handleCloseResultsDetail = () => {
    setShowResultsDetail(false);
    setSelectedAttemptDetails(null);
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

  const fetchTopicTests = async (topicId) => {
    try {
      const response = await axios.get(
        `${API_BASE}/student/topics/${topicId}/tests`,
        { headers: { 'Authorization': authHeader } }
      );
      setTopicTests({
        ...topicTests,
        [topicId]: response.data
      });
      setExpandedTopicId(expandedTopicId === topicId ? null : topicId);
    } catch (error) {
      console.error('Error fetching topic tests:', error);
      setMessage({ type: 'error', text: 'Failed to load tests for this topic' });
    }
  };

  const handleAddTest = async (topic) => {
    try {
      // Check if tests are already loaded
      let tests;
      if (topicTests[topic.id]) {
        tests = topicTests[topic.id].tests;
      } else {
        // Fetch tests if not already loaded
        const response = await axios.get(
          `${API_BASE}/student/topics/${topic.id}/tests`,
          { headers: { 'Authorization': authHeader } }
        );
        tests = response.data.tests || [];
        // Update state with fetched data
        setTopicTests(prev => ({
          ...prev,
          [topic.id]: response.data
        }));
      }

      // Now check if there are any tests
      if (tests && tests.length > 0) {
        const attemptedTests = tests.filter(t => t.attempted);
        const pendingTests = tests.filter(t => !t.attempted);

        if (attemptedTests.length > 0 && pendingTests.length === 0) {
          // All tests attempted - offer to create another test
          setSelectedTopic(topic);
          setAttemptedTestsList(attemptedTests);
          setDialogType('already_attempted');
          setShowDialog(true);
        } else if (pendingTests.length > 0) {
          // Show pending/unattempted tests first
          setSelectedTopic(topic);
          setPendingTestsList(pendingTests);
          setDialogType('pending_tests');
          setShowDialog(true);
        }
      } else {
        // No tests created yet - proceed to add for test builder
        addTopicToTest(topic.id);
      }
    } catch (error) {
      console.error('Error handling add test:', error);
      setMessage({ type: 'error', text: 'Failed to load tests for this topic' });
      // Fallback: just add to test builder
      addTopicToTest(topic.id);
    }
  };

  const handleDialogConfirm = () => {
    if (dialogType === 'test_created') {
      // User confirmed - go to take tests section
      setShowDialog(false);
      setActiveMenu('tests');
      fetchTests();
    } else if (dialogType === 'already_attempted') {
      // User confirmed creating new test after all attempts done
      addTopicToTest(selectedTopic.id);
      setShowDialog(false);
    } else if (dialogType === 'pending_tests') {
      // User confirmed, show as is (they can still add to builder)
      addTopicToTest(selectedTopic.id);
      setShowDialog(false);
    }
  };

  const handleDialogCancel = () => {
    setShowDialog(false);
    setSelectedTopic(null);
    setPendingTestsList([]);
    setAttemptedTestsList([]);
    setCreatedTestInfo(null);
    setTopicAttemptedInfo({});
    setDialogType('');
  };

  const addTopicToTest = async (topicId) => {
    try {
      await axios.post(
        `${API_BASE}/student/test-builder/add-topic/${topicId}`,
        {},
        { headers: { 'Authorization': authHeader } }
      );
      
      if (!selectedTopicIds.includes(topicId)) {
        setSelectedTopicIds([...selectedTopicIds, topicId]);
      }
      
      setMessage({ type: 'success', text: 'Topic added to test!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to add topic' });
    }
  };

  const removeTopicFromTest = async (topicId) => {
    try {
      await axios.post(
        `${API_BASE}/student/test-builder/remove-topic/${topicId}`,
        {},
        { headers: { 'Authorization': authHeader } }
      );
      
      setSelectedTopicIds(selectedTopicIds.filter(id => id !== topicId));
      setMessage({ type: 'success', text: 'Topic removed' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to remove topic' });
    }
  };

  const generateMCQs = async () => {
    if (selectedTopicIds.length === 0) {
      setMessage({ type: 'error', text: 'Please select at least one topic' });
      return;
    }

    setIsGeneratingMCQs(true);
    try {
      const response = await axios.post(
        `${API_BASE}/student/test-builder/generate-mcqs`,
        {
          topic_ids: selectedTopicIds,
          num_questions: 5
        },
        { headers: { 'Authorization': authHeader } }
      );

      setGeneratedMCQs(response.data.mcqs || []);
      setMessage({ type: 'success', text: `Generated ${response.data.total_questions} MCQ questions!` });
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to generate MCQs';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setIsGeneratingMCQs(false);
    }
  };

  const createTest = async () => {
    if (generatedMCQs.length === 0) {
      setMessage({ type: 'error', text: 'Please generate MCQs first' });
      return;
    }

    setIsCreatingTest(true);
    try {
      const url = testName && testName.trim() 
        ? `${API_BASE}/student/test-builder/create-test?title=${encodeURIComponent(testName.trim())}` 
        : `${API_BASE}/student/test-builder/create-test`;
      
      const response = await axios.post(
        url,
        {},
        { headers: { 'Authorization': authHeader } }
      );

      // Store created test info
      setCreatedTestInfo({
        title: testName || response.data.title,
        topicIds: selectedTopicIds
      });

      // Refresh topicTests for all selected topics to check for attempted tests
      const attemptedInfo = {};
      for (const topicId of selectedTopicIds) {
        try {
          const topicResponse = await axios.get(
            `${API_BASE}/student/topics/${topicId}/tests`,
            { headers: { 'Authorization': authHeader } }
          );
          setTopicTests(prev => ({
            ...prev,
            [topicId]: topicResponse.data
          }));
          // Check if there are attempted tests
          const attemptedTests = topicResponse.data.tests.filter(t => t.attempted);
          if (attemptedTests.length > 0) {
            attemptedInfo[topicId] = {
              topicTitle: topicResponse.data.topic_title,
              attemptedCount: attemptedTests.length,
              totalCount: topicResponse.data.tests.length
            };
          }
        } catch (err) {
          console.error(`Error fetching tests for topic ${topicId}:`, err);
        }
      }

      setTopicAttemptedInfo(attemptedInfo);
      
      // Show dialog for test created
      setDialogType('test_created');
      setShowDialog(true);
      
      // Reset builder
      setSelectedTopicIds([]);
      setGeneratedMCQs([]);
      setTestName('');
      setShowTestBuilder(false);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to create test';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setIsCreatingTest(false);
    }
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
            className={`menu-item ${activeMenu === 'results' ? 'active' : ''}`}
            onClick={() => setActiveMenu('results')}
          >
            📊 Test Results
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

        {/* Loading Spinner */}
        {menuLoading && (
          <div className="loader-container">
            <div className="loader"></div>
            <p>Loading...</p>
          </div>
        )}

        {/* Dashboard View */}
        {!menuLoading && activeMenu === 'dashboard' && dashboardData && (
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
              <h2>📚 Recent Test Attempts</h2>
              {dashboardData.recent_test_attempts && dashboardData.recent_test_attempts.length > 0 ? (
                <div className="table-wrapper">
                  <table className="tests-table">
                    <thead>
                      <tr>
                        <th className="col-test">Test Name</th>
                        <th className="col-score">Score</th>
                        <th className="col-correct">Correct</th>
                        <th className="col-status">Status</th>
                        <th className="col-date">Date</th>
                        <th className="col-topics">Topics</th>
                        <th className="col-action">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboardData.recent_test_attempts.map((test, idx) => (
                        <tr key={test.id} className={`table-row ${test.pass_status}`}>
                          <td className="col-test">
                            <button 
                              className="test-link"
                              onClick={() => navigate(`/test-review/${test.id}`)}
                              title="View test details"
                            >
                              {test.test_title}
                            </button>
                          </td>
                          <td className="col-score">
                            <div className="score-cell">
                              <span className="score-value">{test.percentage}%</span>
                              <div className="mini-bar">
                                <div 
                                  className={`mini-fill ${test.pass_status}`}
                                  style={{ width: `${test.percentage}%` }}
                                ></div>
                              </div>
                            </div>
                          </td>
                          <td className="col-correct">
                            <span className="correct-badge">
                              {test.correct_answers}/{test.total_questions}
                            </span>
                          </td>
                          <td className="col-status">
                            <span className={`status-badge ${test.pass_status}`}>
                              {test.pass_status === 'pass' ? '✓ PASS' : '✗ FAIL'}
                            </span>
                          </td>
                          <td className="col-date">
                            <span className="date-text">
                              {new Date(test.created_at).toLocaleDateString('en-US', { 
                                month: 'short', 
                                day: 'numeric', 
                                year: 'numeric' 
                              })}
                            </span>
                          </td>
                          <td className="col-topics">
                            {test.topics && test.topics.length > 0 ? (
                              <div className="topics-cell">
                                {test.topics.slice(0, 1).map((topic, i) => (
                                  <span key={i} className="topic-badge">{topic}</span>
                                ))}
                                {test.topics.length > 1 && (
                                  <span className="topic-more">+{test.topics.length - 1}</span>
                                )}
                              </div>
                            ) : (
                              <span className="no-topics">-</span>
                            )}
                          </td>
                          <td className="col-action">
                            <button 
                              className="btn-view"
                              onClick={() => navigate(`/test-review/${test.id}`)}
                              title="View details"
                            >
                              View
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="no-data-container">
                  <p className="no-data-text">📝 No test attempts yet. Start taking tests to see your results here!</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Topics View */}
        {!menuLoading && activeMenu === 'topics' && (
          <div className="topics-view">
            <h1>Available Topics</h1>
            
            {topics.length > 0 ? (
              <div className="topics-grid">
                {topics.map((topic) => (
                  <div key={topic.id} className="topic-card">
                    <div className="topic-header">
                      <h3>{topic.title}</h3>
                      <span className="topic-badge">
                        {topic.department_name} - Section {topic.section}
                      </span>
                    </div>
                    <p className="topic-description">{topic.description || 'No description provided'}</p>
                    <div className="topic-meta">
                      <span className="staff-name">👨‍🏫 {topic.staff_name}</span>
                      <span className="topic-date">{new Date(topic.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="topic-actions">
                      <button
                        className="view-tests-btn"
                        onClick={() => fetchTopicTests(topic.id)}
                        title="View tests for this topic"
                      >
                        📋 View Tests {expandedTopicId === topic.id ? '▲' : '▼'}
                      </button>
                      <button
                        className={`add-to-test-btn ${selectedTopicIds.includes(topic.id) ? 'added' : ''}`}
                        onClick={() => selectedTopicIds.includes(topic.id) ? removeTopicFromTest(topic.id) : handleAddTest(topic)}
                        title={selectedTopicIds.includes(topic.id) ? 'Remove from test' : 'Add to test'}
                      >
                        {selectedTopicIds.includes(topic.id) ? '✓ Added' : '+ Add Test'}
                      </button>
                    </div>

                    {/* Topic Tests Display */}
                    {expandedTopicId === topic.id && topicTests[topic.id] && (
                      <div className="topic-tests-section">
                        <div className="topic-tests-header">
                          <h4>Tests for "{topic.title}"</h4>
                          <span className="tests-count">
                            {topicTests[topic.id].attempted_tests}/{topicTests[topic.id].total_tests} attempted
                          </span>
                        </div>
                        {topicTests[topic.id].tests && topicTests[topic.id].tests.length > 0 ? (
                          <div className="tests-list">
                            {topicTests[topic.id].tests.map((test) => (
                              <div key={test.id} className={`topic-test-item ${test.attempted ? 'attempted' : ''}`}>
                                <div className="test-item-title">
                                  <h5>{test.title}</h5>
                                  {test.attempted && (
                                    <span className="attempted-badge">✓ Attempted</span>
                                  )}
                                </div>
                                <div className="test-item-details">
                                  {test.attempted && (
                                    <>
                                      <span className="score">Score: {test.attempt_score}%</span>
                                      <span className="date">{new Date(test.attempted_at).toLocaleDateString()}</span>
                                    </>
                                  )}
                                  {!test.attempted && (
                                    <span className="pending">Pending</span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="no-tests">No tests created from this topic yet</p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-data">No topics available yet</p>
            )}
            
            {/* Test Builder Section */}
            {selectedTopicIds.length > 0 && (
              <div className="test-builder-panel">
                <div className="selected-topics-header">
                  <h3>📝 Topics Selected for Test ({selectedTopicIds.length})</h3>
                  <button 
                    className="toggle-builder-btn"
                    onClick={() => setShowTestBuilder(!showTestBuilder)}
                  >
                    {showTestBuilder ? 'Hide' : 'Show'} Test Builder
                  </button>
                </div>

                {showTestBuilder && (
                  <div className="test-builder-content">
                    <div className="selected-topics-list">
                      {topics.filter(t => selectedTopicIds.includes(t.id)).map(topic => (
                        <div key={topic.id} className="selected-topic-item">
                          <span>{topic.title}</span>
                          <button 
                            className="remove-topic-btn"
                            onClick={() => removeTopicFromTest(topic.id)}
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>

                    {generatedMCQs.length === 0 ? (
                      <button 
                        className="generate-btn"
                        onClick={generateMCQs}
                        disabled={isGeneratingMCQs || selectedTopicIds.length === 0}
                      >
                        {isGeneratingMCQs ? '⏳ Generating MCQs...' : '✨ Generate MCQs'}
                      </button>
                    ) : (
                      <div className="mcq-section">
                        <h4>Generated Questions ({generatedMCQs.length})</h4>
                        <div className="mcq-preview">
                          {generatedMCQs.slice(0, 3).map((mcq, idx) => (
                            <div key={idx} className="mcq-item">
                              <p className="question"><strong>Q{idx + 1}:</strong> {mcq.question}</p>
                              <ul className="options">
                                <li>A) {mcq.option_a}</li>
                                <li>B) {mcq.option_b}</li>
                                <li>C) {mcq.option_c}</li>
                                <li>D) {mcq.option_d}</li>
                              </ul>
                            </div>
                          ))}
                          {generatedMCQs.length > 3 && (
                            <p className="more-questions">+{generatedMCQs.length - 3} more questions</p>
                          )}
                        </div>

                        <div className="test-name-input">
                          <label>Test Name <span className="required">*</span></label>
                          <input
                            type="text"
                            placeholder="Enter test name"
                            value={testName}
                            onChange={(e) => setTestName(e.target.value)}
                            required
                          />
                        </div>

                        <button 
                          className="create-test-btn"
                          onClick={createTest}
                          disabled={isCreatingTest || generatedMCQs.length === 0 || !testName.trim()}
                        >
                          {isCreatingTest ? '⏳ Creating Test...' : '🎯 Create Test'}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Tests View */}
        {!menuLoading && activeMenu === 'tests' && (
          <div className="tests-view">
            <h1>Available Tests</h1>
            {tests.length > 0 ? (
              <div className="tests-grid">
                {tests.map((test) => (
                  <div key={test.id} className={`test-card ${test.attempted ? 'attempted' : ''}`}>
                    <div className="test-header">
                      <h3>{test.title}</h3>
                      {test.attempted && <span className="badge attempted">✓ Attempted</span>}
                    </div>
                    <p className="test-description">{test.description || 'No description'}</p>
                    <div className="test-meta">
                      <span className="topic-info">📚 {test.topic_title}</span>
                      <span className="staff-info">👨‍🏫 {test.staff_name}</span>
                    </div>
                    <div className="test-actions">
                      <button 
                        className="start-btn"
                        onClick={() => test.attempted ? handleViewTestResults(test) : handleStartTest(test.id)}
                      >
                        {test.attempted ? '📊 View Results' : 'Start Test'}
                      </button>
                      {!test.attempted && (
                        <button 
                          className="btn-delete-icon"
                          onClick={(e) => {
                            console.log('Button clicked!');
                            handleDeleteClick(test);
                          }}
                          title="Delete test"
                          type="button"
                        >
                          🗑️
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-data">No tests available yet</p>
            )}
          </div>
        )}

        {/* Interviews View */}
        {!menuLoading && activeMenu === 'interviews' && (
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

        {/* Test Results View */}
        {!menuLoading && activeMenu === 'results' && (
          <div className="results-view">
            <h1>Test Results & Analysis</h1>

            {loadingResults ? (
              <p className="loading">Loading test results...</p>
            ) : (
              <>
                {/* Topic Performance Summary */}
                {topicPerformance && topicPerformance.topic_details && topicPerformance.topic_details.length > 0 && (
                  <div className="performance-summary">
                    <div className="summary-header">
                      <h2>📊 Topic Performance Summary</h2>
                      <div className="summary-stats">
                        <div className="stat">
                          <span className="label">Overall Average:</span>
                          <span className="value">{topicPerformance.overall_average_percentage}%</span>
                        </div>
                        <div className="stat">
                          <span className="label">Mastered Topics:</span>
                          <span className="value">{topicPerformance.mastered_topics}/{topicPerformance.total_topics_attempted}</span>
                        </div>
                      </div>
                    </div>

                    <div className="topics-grid">
                      {topicPerformance.topic_details.map((topic) => (
                        <div key={topic.topic_id} className={`topic-card ${topic.proficiency_level}`}>
                          <div className="topic-header">
                            <h3>{topic.topic_name}</h3>
                            <span className={`badge ${topic.mastery_status ? 'mastered' : ''}`}>
                              {topic.proficiency_level}
                            </span>
                          </div>
                          <div className="topic-stats">
                            <div className="stat-item">
                              <span className="label">Average:</span>
                              <span className="value">{topic.average_percentage}%</span>
                            </div>
                            <div className="stat-item">
                              <span className="label">Last Attempt:</span>
                              <span className="value">{topic.last_attempt_percentage}%</span>
                            </div>
                            <div className="stat-item">
                              <span className="label">Attempts:</span>
                              <span className="value">{topic.total_attempts}</span>
                            </div>
                          </div>
                          <div className="progress-bar">
                            <div 
                              className="progress-fill" 
                              style={{width: `${topic.average_percentage}%`}}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Test History */}
                {testResults && testResults.length > 0 ? (
                  <div className="test-history">
                    <h2>📝 Test History</h2>
                    <div className="test-list">
                      {testResults.map((result) => (
                        <div key={result.test_attempt_id} className={`test-item ${result.pass_status ? 'passed' : 'failed'}`}>
                          <div className="test-info-left">
                            <h3>{result.test_title}</h3>
                            <p className="date">
                              {new Date(result.attempted_at).toLocaleDateString()} at {new Date(result.attempted_at).toLocaleTimeString()}
                            </p>
                          </div>
                          <div className="test-score">
                            <div className={`score-badge ${result.pass_status ? 'passed' : 'failed'}`}>
                              {result.score}%
                            </div>
                            <p className={`status ${result.pass_status ? 'passed' : 'failed'}`}>
                              {result.pass_status ? '✓ Passed' : '✗ Failed'}
                            </p>
                          </div>
                          {result.has_analysis && (
                            <button 
                              className="view-analysis-btn"
                              onClick={() => fetchTestAnalysis(result.test_attempt_id)}
                            >
                              View Analysis →
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="no-data">No tests attempted yet. Start taking tests to see your results!</p>
                )}

                {/* Selected Test Analysis */}
                {selectedTestAnalysis && (
                  <div className="analysis-detail">
                    <button 
                      className="close-analysis"
                      onClick={() => setSelectedTestAnalysis(null)}
                    >
                      ✕ Close
                    </button>

                    <h2>Detailed Test Analysis</h2>

                    {/* Score Overview */}
                    <div className="analysis-overview">
                      <div className="score-card">
                        <h3>Score</h3>
                        <div className="big-score">{selectedTestAnalysis.overall_percentage}%</div>
                        <p>{selectedTestAnalysis.correct_answers}/{selectedTestAnalysis.total_questions} correct</p>
                      </div>

                      <div className="metrics-card">
                        <h3>Breakdown</h3>
                        <div className="metric">
                          <span>Correct Answers:</span>
                          <span className="value correct">{selectedTestAnalysis.correct_answers}</span>
                        </div>
                        <div className="metric">
                          <span>Incorrect Answers:</span>
                          <span className="value incorrect">{selectedTestAnalysis.incorrect_answers}</span>
                        </div>
                      </div>
                    </div>

                    {/* Strengths, Weaknesses, Recommendations */}
                    <div className="analysis-content">
                      {selectedTestAnalysis.strengths && selectedTestAnalysis.strengths.length > 0 && (
                        <div className="analysis-section strengths">
                          <h3>✓ Strengths</h3>
                          <ul>
                            {selectedTestAnalysis.strengths.map((strength, idx) => (
                              <li key={idx}>{strength}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {selectedTestAnalysis.weaknesses && selectedTestAnalysis.weaknesses.length > 0 && (
                        <div className="analysis-section weaknesses">
                          <h3>✗ Areas for Improvement</h3>
                          <ul>
                            {selectedTestAnalysis.weaknesses.map((weakness, idx) => (
                              <li key={idx}>{weakness}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {selectedTestAnalysis.recommendations && selectedTestAnalysis.recommendations.length > 0 && (
                        <div className="analysis-section recommendations">
                          <h3>💡 Recommendations</h3>
                          <ul>
                            {selectedTestAnalysis.recommendations.map((rec, idx) => (
                              <li key={idx}>{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* Topic-wise Analysis */}
                    {selectedTestAnalysis.topic_wise_analysis && Object.keys(selectedTestAnalysis.topic_wise_analysis).length > 0 && (
                      <div className="topic-analysis">
                        <h3>Performance by Topic</h3>
                        <div className="topic-overview">
                          {Object.values(selectedTestAnalysis.topic_wise_analysis).map((topic) => (
                            <div key={topic.topic_id} className="topic-result">
                              <h4>{topic.topic_name}</h4>
                              <p>
                                <span className="correct">{topic.correct_answers}/{topic.total_questions}</span> correct
                                {' '}(<span className={topic.percentage >= 70 ? 'good' : 'poor'}>{topic.percentage}%</span>)
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Resume View */}
        {!menuLoading && activeMenu === 'resume' && (
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

      {/* Confirmation Dialog */}
      {showDialog && (
        <div className="dialog-overlay" onClick={handleDialogCancel}>
          <div className="dialog-box" onClick={(e) => e.stopPropagation()}>
            {dialogType === 'already_attempted' && (
              <>
                <h2>⚠️ Test Already Attempted</h2>
                <p>
                  The following tests for "<strong>{selectedTopic?.title}</strong>" have already been attempted:
                </p>
                <div className="attempted-tests-summary">
                  {attemptedTestsList.map((test) => (
                    <div key={test.id} className="attempted-test-item">
                      <span className="test-name-badge">📝 {test.title}</span>
                      <span className="attempt-badge">{test.attempt_count ? `${test.attempt_count} attempt${test.attempt_count > 1 ? 's' : ''}` : '1 attempt'}</span>
                    </div>
                  ))}
                </div>
                <p className="dialog-message">
                  Would you like to attempt again or create a new test from this topic?
                </p>
                <div className="dialog-actions">
                  <button className="btn-cancel" onClick={handleDialogCancel}>Cancel</button>
                  <button className="btn-confirm" onClick={handleDialogConfirm}>Create New Test</button>
                </div>
              </>
            )}

            {dialogType === 'test_created' && (
              <>
                <h2>✅ Test Created Successfully!</h2>
                <p>
                  Your test "<strong>{createdTestInfo?.title}</strong>" has been created successfully.
                </p>
                {Object.keys(topicAttemptedInfo).length > 0 && (
                  <div className="attempted-tests-info">
                    <h3>📊 Attempted Tests Info:</h3>
                    {Object.entries(topicAttemptedInfo).map(([topicId, info]) => (
                      <div key={topicId} className="attempted-info-item">
                        <span className="topic-name">{info.topicTitle}</span>
                        <span className="attempted-count">{info.attemptedCount}/{info.totalCount} attempted</span>
                      </div>
                    ))}
                  </div>
                )}
                <p className="test-creation-note">
                  {Object.keys(topicAttemptedInfo).length > 0 
                    ? 'These topics have already attempted tests. Your new test has been added anyway.' 
                    : 'Start taking the test now or come back later from the Take Tests section.'}
                </p>
                <div className="dialog-actions">
                  <button className="btn-cancel" onClick={handleDialogCancel}>Continue</button>
                  <button className="btn-confirm" onClick={handleDialogConfirm}>Go to Take Tests</button>
                </div>
              </>
            )}

            {dialogType === 'pending_tests' && (
              <>
                <h2>⏳ Unattempted Test Available</h2>
                <p>
                  Topic "<strong>{selectedTopic?.title}</strong>" has the following unattempted test:
                </p>
                <div className="pending-tests-list">
                  {pendingTestsList.map((test) => (
                    <div key={test.id} className="pending-test">
                      <button 
                        className="test-name-link"
                        onClick={() => {
                          handleDialogCancel();
                          navigate(`/test/${test.id}`);
                        }}
                        title="Click to take the test"
                      >
                        📝 {test.title}
                      </button>
                      <span className="test-status-badge">Not Attempted</span>
                    </div>
                  ))}
                </div>
                <p className="dialog-note">
                  Click on the test name to take it, or proceed to add more topics to the test builder.
                </p>
                <div className="dialog-actions">
                  <button className="btn-cancel" onClick={handleDialogCancel}>Cancel</button>
                  <button className="btn-confirm" onClick={handleDialogConfirm}>Add Anyway</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog - At Root Level */}
      {showDeleteConfirm && testToDelete && (
        <div className="dialog-overlay" onClick={handleCancelDelete}>
          <div className="dialog-box" onClick={(e) => e.stopPropagation()}>
            <h2>Delete Test</h2>
            <p>Are you sure you want to delete the test <strong>"{testToDelete.title}"</strong>?</p>
            <p className="dialog-warning">⚠️ This action cannot be undone. All associated test data and attempts will also be deleted.</p>
            <div className="dialog-actions">
              <button 
                className="btn-cancel"
                onClick={handleCancelDelete}
                disabled={deleting}
              >
                Cancel
              </button>
              <button 
                className="btn-confirm-delete"
                onClick={handleDeleteTest}
                disabled={deleting}
              >
                {deleting ? 'Deleting...' : 'Delete Test'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Test Results Detail Modal */}
      {showResultsDetail && selectedAttemptDetails && (
        <div className="dialog-overlay" onClick={handleCloseResultsDetail}>
          <div className="dialog-box results-detail-box" onClick={(e) => e.stopPropagation()}>
            <div className="results-header">
              <h2>📊 {selectedAttemptDetails.test_title}</h2>
              <button 
                className="close-btn" 
                onClick={handleCloseResultsDetail}
                style={{
                  position: 'absolute',
                  right: '20px',
                  top: '20px',
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer'
                }}
              >
                ✕
              </button>
            </div>

            {loadingAttemptDetails ? (
              <p className="loading">Loading results...</p>
            ) : (
              <div className="results-content">
                <div className="result-stat">
                  <span className="stat-label">📋 Total Questions:</span>
                  <span className="stat-value">{selectedAttemptDetails.total_questions}</span>
                </div>

                <div className="result-stat">
                  <span className="stat-label">✅ Correct Answers:</span>
                  <span className="stat-value correct">{selectedAttemptDetails.correct_count}</span>
                </div>

                <div className="result-stat">
                  <span className="stat-label">❌ Wrong Answers:</span>
                  <span className="stat-value wrong">{selectedAttemptDetails.wrong_count}</span>
                </div>

                <div className="result-stat score-stat">
                  <span className="stat-label">📈 Score:</span>
                  <span className="stat-value score">{selectedAttemptDetails.score}%</span>
                </div>

                <div className={`result-stat status-stat ${selectedAttemptDetails.status}`}>
                  <span className="stat-label">Result:</span>
                  <span className={`stat-value ${selectedAttemptDetails.status}`}>
                    {selectedAttemptDetails.status === 'pass' ? '✅ PASS' : '❌ FAIL'}
                  </span>
                </div>

                <p className="result-note">
                  Attempted on: {new Date(selectedAttemptDetails.attempted_at).toLocaleString()}
                </p>
              </div>
            )}

            <div className="dialog-actions">
              <button 
                className="btn-confirm"
                onClick={handleCloseResultsDetail}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentDashboard;
