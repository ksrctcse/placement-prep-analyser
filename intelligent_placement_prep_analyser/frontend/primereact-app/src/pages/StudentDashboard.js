import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Toolbar } from 'primereact/toolbar';
import { Toast } from 'primereact/toast';
import { Message } from 'primereact/message';
import { Dialog } from 'primereact/dialog';
import { useAuth } from '../context/AuthContext';
import { studentAPI } from '../services/api';
import '../styles/Dashboard.css';
import { useRef } from 'react';

export default function StudentDashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const toast = useRef(null);
  const fileInputRef = useRef(null);
  const [data, setData] = useState(null);
  const [resume, setResume] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [improvementPlan, setImprovementPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [showPlan, setShowPlan] = useState(false);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const dashRes = await studentAPI.getDashboard();
      setData(dashRes.data);

      try {
        const resumeRes = await studentAPI.getMyResume();
        // Handle both 200 and 300 status codes
        if (resumeRes.status === 200 && resumeRes.data?.has_resume) {
          setResume(resumeRes.data.resume);

          try {
            const analysisRes = await studentAPI.getAnalysis();
            setAnalysis(analysisRes.data);
          } catch (err) {
            // Analysis might not exist yet
          }
        } else if (resumeRes.status === 300 || !resumeRes.data?.has_resume) {
          // No resume found - this is expected
          setResume(null);
        }
      } catch (err) {
        // Resume endpoint may return 300 status, check the error response
        if (err.response?.status === 300) {
          setResume(null);
        } else {
          // Other errors
          console.log('Resume fetch note:', err.message);
        }
      }
    } catch (error) {
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load dashboard data',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResumeUpload = async (event) => {
    // For auto-upload, event.files contains the selected files
    const file = event.files ? event.files[0] : event;
    if (!file) return;

    setUploading(true);
    try {
      const response = await studentAPI.uploadResume(file);
      
      toast.current?.show({
        severity: 'success',
        summary: 'Success',
        detail: 'Resume uploaded and analyzed successfully!',
      });

      // Refresh dashboard
      await fetchDashboard();
    } catch (error) {
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: error.response?.data?.detail || 'Failed to upload resume',
      });
    } finally {
      setUploading(false);
    }
  };

  // Handle file input change
  const handleFileInputChange = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    
    // Validate file type
    if (file.type !== 'application/pdf') {
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Please upload a PDF file',
      });
      return;
    }
    
    // Validate file size (5MB)
    if (file.size > 5000000) {
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'File size must be less than 5MB',
      });
      return;
    }

    setUploading(true);
    try {
      const response = await studentAPI.uploadResume(file);
      
      toast.current?.show({
        severity: 'success',
        summary: 'Success',
        detail: 'Resume uploaded and analyzed successfully!',
      });

      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      // Refresh dashboard
      await fetchDashboard();
    } catch (error) {
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: error.response?.data?.detail || 'Failed to upload resume',
      });
      // Clear the file input on error as well
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } finally {
      setUploading(false);
    }
  };

  const handleViewAnalysis = () => {
    setShowAnalysis(true);
  };

  const handleGeneratePlan = async () => {
    if (!resume) return;
    
    try {
      const response = await studentAPI.getImprovementPlan(resume.id);
      setImprovementPlan(response.data.improvement_plan);
      setShowPlan(true);
    } catch (error) {
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to generate improvement plan',
      });
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const renderToolbar = () => (
    <Toolbar
      className="dashboard-toolbar"
      right={
        <Button
          icon="pi pi-sign-out"
          label="Logout"
          onClick={handleLogout}
          className="p-button-danger"
        />
      }
    />
  );

  const skillsList = analysis?.analysis_data?.skills?.slice(0, 5).map((skill) => (
    <span key={skill} className="skill-badge">
      {skill}
    </span>
  ));

  const recommendationsList = analysis?.recommendations?.slice(0, 3).map((rec, idx) => (
    <div key={idx} className="recommendation-item">
      <strong>{rec.recommendation}</strong>
      <span className={`priority-${rec.priority}`}>{rec.priority}</span>
    </div>
  ));

  if (loading) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  return (
    <div className="student-dashboard">
      <Toast ref={toast} />
      {renderToolbar()}

      <div className="dashboard-content">
        {/* Header Card */}
        <Card className="header-card">
          <div className="header-content">
            <div>
              <h1>Welcome, {user?.name}!</h1>
              <p className="subtitle">{user?.role.toUpperCase()} | {data?.department} - {data?.batch}</p>
            </div>
          </div>
        </Card>

        {/* Resume Section */}
        <Card className="section-card">
          <h2 className="section-title">
            <i className="pi pi-file-pdf"></i> Resume Management
          </h2>

          {!resume ? (
            <div className="resume-upload-section">
              <Message
                severity="info"
                text="No resumes uploaded yet. Upload your resume to get AI-powered analysis and improvement recommendations"
                style={{ marginBottom: '1rem' }}
              />
              <div className="file-input-wrapper">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleFileInputChange}
                  style={{ display: 'none' }}
                  id="resume-file-input"
                />
                <Button
                  icon="pi pi-upload"
                  label={uploading ? 'Uploading...' : 'Upload Resume (PDF)'}
                  onClick={() => fileInputRef.current?.click()}
                  loading={uploading}
                  disabled={uploading}
                  className="w-full"
                />
              </div>
            </div>
          ) : (
            <div className="resume-info">
              <div className="resume-details-section">
                <div className="resume-file-info">
                  <div className="file-icon">
                    <i className="pi pi-file-pdf"></i>
                  </div>
                  <div className="file-details">
                    <h3>{resume.file_name}</h3>
                    <div className="file-meta">
                      <span className="file-size">
                        <i className="pi pi-file"></i> {(resume.file_size / 1024).toFixed(2)} KB
                      </span>
                      <span className="file-date">
                        <i className="pi pi-calendar"></i> Uploaded on {new Date(resume.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="resume-actions">
                <Button
                  icon="pi pi-eye"
                  label="View Analysis"
                  onClick={handleViewAnalysis}
                  disabled={!analysis}
                  className="p-button-info"
                />
                <Button
                  icon="pi pi-chart-bar"
                  label="Improvement Plan"
                  onClick={handleGeneratePlan}
                  disabled={!analysis}
                  className="p-button-success"
                />
                <Button
                  icon="pi pi-upload"
                  label="Upload New Resume"
                  className="p-button-warning"
                  onClick={() => {
                    // Trigger file upload
                    document.querySelector('.p-fileupload-choose')?.click();
                  }}
                />
              </div>
            </div>
          )}
        </Card>

        {/* Analysis Section */}
        {analysis && (
          <Card className="section-card">
            <h2 className="section-title">
              <i className="pi pi-check-circle"></i> Resume Analysis
            </h2>

            <div className="analysis-grid">
              <div className="analysis-item">
                <div className="score-circle">
                  <div className="score-value">
                    {analysis.analysis_data?.suitability_score || 0}
                  </div>
                  <div className="score-label">Suitability Score</div>
                </div>
              </div>

              <div className="analysis-item">
                <h3>Professional Summary</h3>
                <p>{analysis.analysis_data?.professional_summary}</p>
              </div>

              <div className="analysis-item">
                <h3>Key Skills</h3>
                <div className="skills-container">{skillsList}</div>
              </div>

              <div className="analysis-item">
                <h3>Recommended Roles</h3>
                <ul>
                  {analysis.analysis_data?.recommended_roles?.slice(0, 3).map((role) => (
                    <li key={role}>{role}</li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>
        )}

        {/* Recommendations Section */}
        {analysis?.recommendations && (
          <Card className="section-card">
            <h2 className="section-title">
              <i className="pi pi-lightbulb"></i> Improvement Recommendations
            </h2>
            <div className="recommendations-container">{recommendationsList}</div>
          </Card>
        )}

        {/* Progress Section */}
        {data?.progress && (
          <Card className="section-card">
            <h2 className="section-title">
              <i className="pi pi-chart-line"></i> Your Progress
            </h2>
            <p>{data.progress}</p>
          </Card>
        )}
      </div>

      {/* Analysis Dialog */}
      <Dialog
        header="Resume Analysis Details"
        visible={showAnalysis}
        onHide={() => setShowAnalysis(false)}
        style={{ width: '90vw' }}
        maximizable
      >
        <div className="analysis-details">
          <div className="analysis-section">
            <h3>Candidate Information</h3>
            <p>
              <strong>Name:</strong> {analysis?.analysis_data?.candidate_name}
            </p>
            <p>
              <strong>Email:</strong> {analysis?.analysis_data?.email}
            </p>
            <p>
              <strong>Phone:</strong> {analysis?.analysis_data?.phone || 'Not provided'}
            </p>
          </div>

          <div className="analysis-section">
            <h3>Experience</h3>
            {analysis?.analysis_data?.experience?.map((exp, idx) => (
              <div key={idx} className="experience-item">
                <h4>{exp.position}</h4>
                <p>
                  <strong>{exp.company}</strong> | {exp.duration}
                </p>
                <p>{exp.description}</p>
              </div>
            ))}
          </div>

          <div className="analysis-section">
            <h3>Education</h3>
            {analysis?.analysis_data?.education?.map((edu, idx) => (
              <div key={idx} className="education-item">
                <p>
                  <strong>{edu.degree}</strong> from {edu.institution}
                </p>
                <p>Year: {edu.year}</p>
                {edu.gpa && <p>GPA: {edu.gpa}</p>}
              </div>
            ))}
          </div>

          <div className="analysis-section">
            <h3>Overall Assessment</h3>
            <p>{analysis?.analysis_data?.overall_assessment}</p>
          </div>
        </div>
      </Dialog>

      {/* Improvement Plan Dialog */}
      <Dialog
        header="30-60-90 Day Improvement Plan"
        visible={showPlan}
        onHide={() => setShowPlan(false)}
        style={{ width: '90vw' }}
        maximizable
      >
        <div className="improvement-plan-details">
          {improvementPlan && (
            <>
              <div className="plan-section">
                <h3>First 30 Days</h3>
                <ul>
                  {improvementPlan['30_day_plan']?.map((item, idx) => (
                    <li key={idx}>
                      <strong>{item.action}</strong> - {item.description}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="plan-section">
                <h3>Next 30 Days (60)</h3>
                <ul>
                  {improvementPlan['60_day_plan']?.map((item, idx) => (
                    <li key={idx}>
                      <strong>{item.action}</strong> - {item.description}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="plan-section">
                <h3>Final 30 Days (90)</h3>
                <ul>
                  {improvementPlan['90_day_plan']?.map((item, idx) => (
                    <li key={idx}>
                      <strong>{item.action}</strong> - {item.description}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="plan-section">
                <h3>Skills to Develop</h3>
                <div className="skills-container">
                  {improvementPlan.skills_to_develop?.map((skill) => (
                    <span key={skill} className="skill-badge">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              <div className="plan-section">
                <h3>Certifications to Pursue</h3>
                <ul>
                  {improvementPlan.certifications_to_pursue?.map((cert) => (
                    <li key={cert}>{cert}</li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      </Dialog>
    </div>
  );
}
