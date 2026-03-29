import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Toolbar } from 'primereact/toolbar';
import { Toast } from 'primereact/toast';
import { Dialog } from 'primereact/dialog';
import { useAuth } from '../context/AuthContext';
import { staffAPI } from '../services/api';
import '../styles/Dashboard.css';
import { useRef } from 'react';

export default function StaffDashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const toast = useRef(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [showResumeDialog, setShowResumeDialog] = useState(false);
  const [selectedResume, setSelectedResume] = useState(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [showAnalysisDialog, setShowAnalysisDialog] = useState(false);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const dashRes = await staffAPI.getDashboard();
      setDashboardData(dashRes.data);
      setStudents(dashRes.data.top_performers || []);
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

  const handleViewResume = async (student) => {
    try {
      const resumeRes = await staffAPI.getStudentResume(student.id);
      setSelectedResume(resumeRes.data);
      setSelectedStudent(student);
      setShowResumeDialog(true);
    } catch (error) {
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load resume',
      });
    }
  };

  const handleViewAnalysis = async (resumeId) => {
    try {
      const analysisRes = await staffAPI.getResumeAnalysis(resumeId);
      setSelectedAnalysis(analysisRes.data);
      setShowAnalysisDialog(true);
    } catch (error) {
      toast.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load analysis',
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

  const actionBodyTemplate = (rowData) => (
    <div className="action-buttons">
      <Button
        icon="pi pi-eye"
        rounded
        text
        severity="info"
        onClick={() => handleViewResume(rowData)}
        tooltip="View Resume"
      />
    </div>
  );

  if (loading) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  return (
    <div className="staff-dashboard">
      <Toast ref={toast} />
      {renderToolbar()}

      <div className="dashboard-content">
        {/* Header Card */}
        <Card className="header-card">
          <div className="header-content">
            <div>
              <h1>Welcome, {user?.name}!</h1>
              <p className="subtitle">{user?.role.toUpperCase()} | {user?.position}</p>
            </div>
          </div>
        </Card>

        {/* Statistics Cards */}
        <div className="stats-grid">
          <Card className="stat-card">
            <div className="stat-content">
              <div className="stat-number">{dashboardData?.total_students || 0}</div>
              <div className="stat-label">Total Students</div>
            </div>
          </Card>

          <Card className="stat-card">
            <div className="stat-content">
              <div className="stat-number">{dashboardData?.total_staff || 0}</div>
              <div className="stat-label">Staff Members</div>
            </div>
          </Card>

          <Card className="stat-card">
            <div className="stat-content">
              <div className="stat-number">
                {dashboardData?.top_performers?.length || 0}
              </div>
              <div className="stat-label">Top Performers</div>
            </div>
          </Card>
        </div>

        {/* Students Table */}
        <Card className="section-card">
          <h2 className="section-title">
            <i className="pi pi-users"></i> Student Progress
          </h2>

          <DataTable
            value={students}
            paginator
            rows={10}
            rowsPerPageOptions={[5, 10, 20]}
            tableStyle={{ minWidth: '50rem' }}
            stripedRows
          >
            <Column field="name" header="Name" sortable />
            <Column field="email" header="Email" />
            <Column field="department" header="Department" />
            <Column field="batch" header="Batch" />
            <Column
              field="interview_score"
              header="Interview Score"
              body={(rowData) => rowData.interview_score || '-'}
            />
            <Column
              header="Actions"
              body={actionBodyTemplate}
              style={{ width: '10rem' }}
            />
          </DataTable>
        </Card>
      </div>

      {/* Resume Dialog */}
      <Dialog
        header={`Resume - ${selectedStudent?.name}`}
        visible={showResumeDialog}
        onHide={() => setShowResumeDialog(false)}
        style={{ width: '90vw' }}
        maximizable
      >
        {selectedResume && (
          <div className="resume-dialog-content">
            <div className="resume-info">
              <p>
                <strong>Student:</strong> {selectedStudent?.name}
              </p>
              <p>
                <strong>Email:</strong> {selectedStudent?.email}
              </p>
              <p>
                <strong>File:</strong> {selectedResume.file_name}
              </p>
              <p>
                <strong>Uploaded:</strong>{' '}
                {new Date(selectedResume.created_at).toLocaleDateString()}
              </p>
            </div>

            <div className="resume-content">
              <h3>Resume Content</h3>
              <div className="content-box">
                {selectedResume.content_text ? (
                  <p>{selectedResume.content_text}</p>
                ) : (
                  <p>No content available</p>
                )}
              </div>
            </div>

            <div className="dialog-actions">
              <Button
                label="View Analysis"
                icon="pi pi-eye"
                onClick={() => {
                  handleViewAnalysis(selectedResume.id);
                  setShowResumeDialog(false);
                }}
                className="p-button-info"
              />
            </div>
          </div>
        )}
      </Dialog>

      {/* Analysis Dialog */}
      <Dialog
        header="Resume Analysis"
        visible={showAnalysisDialog}
        onHide={() => setShowAnalysisDialog(false)}
        style={{ width: '90vw' }}
        maximizable
      >
        {selectedAnalysis && (
          <div className="analysis-details">
            <div className="analysis-section">
              <div className="score-circle">
                <div className="score-value">
                  {selectedAnalysis.analysis_data?.suitability_score || 0}
                </div>
                <div className="score-label">Suitability Score</div>
              </div>
            </div>

            <div className="analysis-section">
              <h3>Professional Summary</h3>
              <p>{selectedAnalysis.analysis_data?.professional_summary}</p>
            </div>

            <div className="analysis-section">
              <h3>Skills</h3>
              <div className="skills-container">
                {selectedAnalysis.analysis_data?.skills?.slice(0, 10).map((skill) => (
                  <span key={skill} className="skill-badge">
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            <div className="analysis-section">
              <h3>Recommended Roles</h3>
              <ul>
                {selectedAnalysis.analysis_data?.recommended_roles?.map((role) => (
                  <li key={role}>{role}</li>
                ))}
              </ul>
            </div>

            <div className="analysis-section">
              <h3>Recommendations for Improvement</h3>
              {selectedAnalysis.recommendations?.map((rec, idx) => (
                <div key={idx} className="recommendation-item">
                  <strong>{rec.recommendation}</strong>
                  <span className={`priority-${rec.priority}`}>{rec.priority}</span>
                </div>
              ))}
            </div>

            <div className="analysis-section">
              <h3>Overall Assessment</h3>
              <p>{selectedAnalysis.analysis_data?.overall_assessment}</p>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
