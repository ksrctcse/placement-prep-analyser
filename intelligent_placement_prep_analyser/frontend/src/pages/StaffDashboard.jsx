
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './StaffDashboard.css';

const StaffDashboard = () => {
  const [activeMenu, setActiveMenu] = useState('dashboard');
  const [staffName, setStaffName] = useState('');
  const [department, setDepartment] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [topics, setTopics] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadDepartment, setUploadDepartment] = useState(null);
  const [uploadSection, setUploadSection] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [dragActive, setDragActive] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState({ show: false, topicId: null, title: '' });
  const [reindexLoading, setReindexLoading] = useState(null); // Track which topic is being re-indexed
  
  // Filter state for topics view
  const [filterDepartment, setFilterDepartment] = useState(null);
  const [filterSection, setFilterSection] = useState(null);
  const [availableDepartments, setAvailableDepartments] = useState([]);
  const [availableSections, setAvailableSections] = useState([]);
  const [filterOptionsLoading, setFilterOptionsLoading] = useState(false);
  const [menuLoading, setMenuLoading] = useState(false);
  
  const fileInputRef = React.useRef(null);
  const navigate = useNavigate();

  const API_BASE = 'http://localhost:8003';
  const token = localStorage.getItem('access_token');
  const authHeader = `Bearer ${token}`;

  const sections = ['A', 'B', 'C'];

  useEffect(() => {
    if (!token) {
      navigate('/auth');
      return;
    }
    
    if (activeMenu === 'dashboard') {
      fetchDashboardData();
    } else if (activeMenu === 'topics') {
      fetchFilterOptions();
    } else if (activeMenu === 'upload') {
      fetchDepartments();
    } else if (activeMenu === 'performance') {
      fetchPerformanceMetrics();
    }
  }, [activeMenu]);

  const fetchDashboardData = async () => {
    setMenuLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/staff/dashboard`, {
        headers: { 'Authorization': authHeader }
      });
      setDashboardData(response.data);
      setStaffName(response.data.staff_name);
      setDepartment(response.data.department);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      setMessage({ type: 'error', text: 'Failed to load dashboard' });
    } finally {
      setMenuLoading(false);
    }
  };

  const fetchTopics = async (deptId = null, sec = null) => {
    setMenuLoading(true);
    try {
      const params = new URLSearchParams();
      if (deptId !== null) params.append('department_id', deptId);
      if (sec !== null) params.append('section', sec);
      
      const url = `${API_BASE}/staff/topics${params.toString() ? '?' + params.toString() : ''}`;
      const response = await axios.get(url, {
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

  const fetchFilterOptions = async () => {
    setMenuLoading(true);
    try {
      setFilterOptionsLoading(true);
      const response = await axios.get(`${API_BASE}/staff/topics/filters/options`, {
        headers: { 'Authorization': authHeader }
      });
      
      setAvailableDepartments(response.data.departments);
      setAvailableSections(response.data.sections);
      
      // Set defaults to first added value
      if (response.data.default_department) {
        setFilterDepartment(response.data.default_department);
      }
      if (response.data.default_section) {
        setFilterSection(response.data.default_section);
      }
    } catch (error) {
      console.error('Error fetching filter options:', error);
      setMenuLoading(false);
    } finally {
      setFilterOptionsLoading(false);
    }
  };

  // Fetch topics when filters change
  useEffect(() => {
    if (activeMenu === 'topics' && filterDepartment !== null && filterSection !== null) {
      fetchTopics(filterDepartment, filterSection);
    }
  }, [filterDepartment, filterSection, activeMenu]);

  const deleteTopic = async (topicId) => {
    try {
      await axios.delete(`${API_BASE}/staff/topics/${topicId}`, {
        headers: { 'Authorization': authHeader }
      });
      setMessage({ type: 'success', text: 'Topic deleted successfully' });
      setDeleteConfirm({ show: false, topicId: null, title: '' });
      // Refresh topics list
      fetchTopics();
    } catch (error) {
      console.error('Error deleting topic:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to delete topic';
      setMessage({ type: 'error', text: errorMsg });
    }
  };

  const showDeleteConfirm = (topicId, topicTitle) => {
    setDeleteConfirm({ show: true, topicId, title: topicTitle });
  };

  const reindexTopic = async (topicId) => {
    try {
      setReindexLoading(topicId);
      const response = await axios.post(`${API_BASE}/staff/topics/${topicId}/reindex`, {}, {
        headers: { 'Authorization': authHeader }
      });
      setMessage({ type: 'success', text: `✓ ${response.data.message}` });
      // Refresh topics list
      fetchTopics();
    } catch (error) {
      console.error('Error re-indexing topic:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to re-index topic';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setReindexLoading(null);
    }
  };

  const fetchPerformanceMetrics = async () => {
    setMenuLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/staff/performance-metrics`, {
        headers: { 'Authorization': authHeader }
      });
      setMetrics(response.data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
      setMessage({ type: 'error', text: 'Failed to load performance metrics' });
    } finally {
      setMenuLoading(false);
    }
  };

  const fetchDepartments = async () => {
    setMenuLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/auth/departments`);
      setDepartments(response.data);
    } catch (error) {
      console.error('Error fetching departments:', error);
      setMessage({ type: 'error', text: 'Failed to load departments' });
    } finally {
      setMenuLoading(false);
    }
  };

  const validateAndSetFile = (file) => {
    if (!file.name.endsWith('.pdf')) {
      setMessage({ type: 'error', text: 'Please select a PDF file' });
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setMessage({ type: 'error', text: 'File size exceeds 10MB limit' });
      return;
    }
    setUploadFile(file);
    setMessage({ type: '', text: '' });
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const handleFileInputClick = () => {
    if (fileInputRef.current && !uploadLoading) {
      fileInputRef.current.click();
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (uploadLoading) return;
    
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
    
    if (uploadLoading) return;

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      validateAndSetFile(files[0]);
    }
  };

  const handleUploadTopic = async (e) => {
    e.preventDefault();
    
    if (!uploadTitle.trim()) {
      setMessage({ type: 'error', text: 'Please enter topic title' });
      return;
    }
    
    if (!uploadFile) {
      setMessage({ type: 'error', text: 'Please select a PDF file' });
      return;
    }

    setUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append('title', uploadTitle);
      formData.append('description', uploadDescription);
      formData.append('file', uploadFile);
      if (uploadDepartment) {
        formData.append('department_id', uploadDepartment);
      }
      if (uploadSection) {
        formData.append('section', uploadSection);
      }

      const response = await axios.post(
        `${API_BASE}/staff/upload-topic`,
        formData,
        {
          headers: {
            'Authorization': authHeader,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setMessage({ type: 'success', text: response.data.message });
      setUploadTitle('');
      setUploadDescription('');
      setUploadDepartment(null);
      setUploadSection(null);
      setUploadFile(null);
      setTimeout(() => {
        setActiveMenu('topics');
        fetchTopics();
      }, 1500);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to upload topic';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setUploadLoading(false);
    }
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
    <div className="staff-dashboard">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>Staff Portal</h2>
          <p className="staff-info">{staffName}</p>
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
            className={`menu-item ${activeMenu === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveMenu('upload')}
          >
            📤 Upload Topic
          </button>
          <button
            className={`menu-item ${activeMenu === 'performance' ? 'active' : ''}`}
            onClick={() => setActiveMenu('performance')}
          >
            📈 Performance Metrics
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
            <h1>Welcome, {dashboardData.staff_name}!</h1>
            <p className="subtitle">Department: {dashboardData.department}</p>

            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-icon">📚</div>
                <div className="metric-content">
                  <p className="metric-label">Topics Created</p>
                  <p className="metric-value">{dashboardData.total_topics}</p>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">📝</div>
                <div className="metric-content">
                  <p className="metric-label">Tests Created</p>
                  <p className="metric-value">{dashboardData.total_tests}</p>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">👥</div>
                <div className="metric-content">
                  <p className="metric-label">Students</p>
                  <p className="metric-value">{dashboardData.total_students}</p>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon">⭐</div>
                <div className="metric-content">
                  <p className="metric-label">Avg Student Score</p>
                  <p className="metric-value">{dashboardData.avg_student_score}%</p>
                </div>
              </div>
            </div>

            <div className="recent-section">
              <h2>Recent Test Attempts</h2>
              {dashboardData.recent_tests && dashboardData.recent_tests.length > 0 ? (
                <table className="recent-table">
                  <thead>
                    <tr>
                      <th>Test Title</th>
                      <th>Score</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboardData.recent_tests.map((test) => (
                      <tr key={test.id}>
                        <td>{test.test_title}</td>
                        <td>{test.score ? `${test.score}%` : 'N/A'}</td>
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
        {!menuLoading && activeMenu === 'topics' && (
          <div className="topics-view">
            <h1>My Topics</h1>
            
            {/* Filters */}
            <div className="topics-filters">
              <div className="filter-group">
                <label htmlFor="filter-department">Department:</label>
                <select
                  id="filter-department"
                  value={filterDepartment || ''}
                  onChange={(e) => setFilterDepartment(e.target.value ? parseInt(e.target.value) : null)}
                  disabled={filterOptionsLoading}
                  className="filter-select"
                >
                  <option value="">All Departments</option>
                  {availableDepartments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="filter-group">
                <label htmlFor="filter-section">Section:</label>
                <select
                  id="filter-section"
                  value={filterSection || ''}
                  onChange={(e) => setFilterSection(e.target.value || null)}
                  disabled={filterOptionsLoading}
                  className="filter-select"
                >
                  <option value="">All Sections</option>
                  {availableSections.map((sec) => (
                    <option key={sec} value={sec}>
                      Section {sec}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            {topics.length > 0 ? (
              <div className="topics-grid">
                {topics.map((topic) => (
                  <div key={topic.id} className="topic-card">
                    <div className="topic-header">
                      <h3>{topic.title}</h3>
                      <span className="topic-date">
                        {new Date(topic.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="topic-description">{topic.description || 'No description'}</p>
                    <div className="topic-meta">
                      <span className="file-size">
                        📄 {(topic.file_size / 1024).toFixed(2)} KB
                      </span>
                      {topic.department_name && (
                        <span className="topic-dept-badge">
                          {topic.department_name} - Section {topic.section}
                        </span>
                      )}
                      <span className="status-badge">
                        {topic.is_indexed ? (
                          <span className="indexed">✓ Indexed ({topic.embedding_chunks} chunks)</span>
                        ) : (
                          <span className="pending">⏳ Not indexed</span>
                        )}
                      </span>
                    </div>
                    <div className="topic-actions">
                      {!topic.is_indexed && (
                        <button
                          className={`btn-reindex ${reindexLoading === topic.id ? 'loading' : ''}`}
                          onClick={() => reindexTopic(topic.id)}
                          disabled={reindexLoading === topic.id}
                          title="Retry semantic indexing for this topic"
                        >
                          {reindexLoading === topic.id ? '⏳ Re-indexing...' : '🔄 Re-index'}
                        </button>
                      )}
                      <button
                        className="btn-delete"
                        onClick={() => showDeleteConfirm(topic.id, topic.title)}
                        title="Delete this topic"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-data">No topics uploaded yet</p>
            )}
          </div>
        )}

        {/* Upload Topic View */}
        {!menuLoading && activeMenu === 'upload' && (
          <div className="upload-view">
            <h1>Upload New Topic</h1>
            <form onSubmit={handleUploadTopic} className="upload-form">
              <div className="form-group">
                <label htmlFor="title">Topic Title *</label>
                <input
                  type="text"
                  id="title"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="Enter topic title"
                  disabled={uploadLoading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  value={uploadDescription}
                  onChange={(e) => setUploadDescription(e.target.value)}
                  placeholder="Enter topic description (optional)"
                  rows="4"
                  disabled={uploadLoading}
                />
              </div>

              <div className="form-row">
                <div className="form-group form-col-2">
                  <label htmlFor="department">Department *</label>
                  <select
                    id="department"
                    value={uploadDepartment || ''}
                    onChange={(e) => setUploadDepartment(e.target.value ? parseInt(e.target.value) : null)}
                    disabled={uploadLoading}
                  >
                    <option value="">Select Department</option>
                    {departments.map((dept) => (
                      <option key={dept.id} value={dept.id}>
                        {dept.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group form-col-2">
                  <label htmlFor="section">Section *</label>
                  <select
                    id="section"
                    value={uploadSection || ''}
                    onChange={(e) => setUploadSection(e.target.value || null)}
                    disabled={uploadLoading}
                  >
                    <option value="">Select Section</option>
                    {sections.map((sec) => (
                      <option key={sec} value={sec}>
                        {sec}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="file">PDF File (Max 10MB) *</label>
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
                    id="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    disabled={uploadLoading}
                  />
                  <div 
                    className="file-display"
                    onClick={handleFileInputClick}
                    role="button"
                    tabIndex={uploadLoading ? -1 : 0}
                    onKeyDown={(e) => {
                      if ((e.key === 'Enter' || e.key === ' ') && !uploadLoading) {
                        handleFileInputClick();
                      }
                    }}
                  >
                    {uploadFile ? (
                      <span className="file-selected">✓ {uploadFile.name}</span>
                    ) : (
                      <span className="file-placeholder">Click to select or drag and drop</span>
                    )}
                  </div>
                </div>
              </div>

              <button 
                type="submit" 
                className="submit-btn"
                disabled={uploadLoading}
              >
                {uploadLoading ? 'Uploading...' : 'Upload Topic'}
              </button>
            </form>
          </div>
        )}

        {/* Performance Metrics View */}
        {!menuLoading && activeMenu === 'performance' && metrics && (
          <div className="performance-view">
            <h1>Student Performance Metrics</h1>
            
            <div className="metrics-summary">
              <div className="summary-card">
                <span className="summary-label">Total Attempts</span>
                <span className="summary-value">{metrics.total_attempts}</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">Completed</span>
                <span className="summary-value" style={{color: '#28a745'}}>{metrics.completed}</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">In Progress</span>
                <span className="summary-value" style={{color: '#ffc107'}}>{metrics.in_progress}</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">Pending</span>
                <span className="summary-value" style={{color: '#dc3545'}}>{metrics.pending}</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">Average Score</span>
                <span className="summary-value">{metrics.average_score}%</span>
              </div>
            </div>

            {metrics.top_performers && metrics.top_performers.length > 0 && (
              <div className="top-performers">
                <h2>Top Performers</h2>
                <table className="performers-table">
                  <thead>
                    <tr>
                      <th>Student Name</th>
                      <th>Average Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.top_performers.map((performer, idx) => (
                      <tr key={idx}>
                        <td>{performer.name}</td>
                        <td>{performer.avg_score}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {deleteConfirm.show && (
          <div className="modal-overlay">
            <div className="modal-content">
              <h2>Confirm Delete</h2>
              <p>Are you sure you want to delete the topic "<strong>{deleteConfirm.title}</strong>"?</p>
              <p className="warning-text">⚠️ This action cannot be undone. All uploaded content and vector embeddings will be deleted.</p>
              <div className="modal-actions">
                <button
                  className="btn-cancel"
                  onClick={() => setDeleteConfirm({ show: false, topicId: null, title: '' })}
                >
                  Cancel
                </button>
                <button
                  className="btn-confirm-delete"
                  onClick={() => deleteTopic(deleteConfirm.topicId)}
                >
                  Delete Topic
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default StaffDashboard;
