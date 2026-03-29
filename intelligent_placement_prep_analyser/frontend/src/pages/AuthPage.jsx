import React, { useState } from 'react';
import { TabView, TabPanel } from 'primereact/tabview';
import { useNavigate } from 'react-router-dom';
import LoginForm from './LoginForm.jsx';
import StaffSignupForm from './StaffSignupForm.jsx';
import StudentSignupForm from './StudentSignupForm.jsx';
import ForgotPassword from './ForgotPassword.jsx';
import '../styles/Auth.css';

export default function AuthPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const navigate = useNavigate();

  const handleLoginSuccess = (role) => {
    // Redirect based on user role
    if (role === 'staff') {
      navigate('/staff-dashboard');
    } else if (role === 'student') {
      navigate('/student-dashboard');
    } else {
      navigate('/');
    }
  };

  const handleSignupSuccess = () => {
    // Switch back to login tab after successful signup
    setActiveTab(0);
  };

  if (showForgotPassword) {
    return (
      <ForgotPassword onBack={() => setShowForgotPassword(false)} />
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-header">
        <h1>Placement Prep Analyser</h1>
        <p>Intelligent Academic Performance Analysis</p>
      </div>

      <TabView activeIndex={activeTab} onTabChange={(e) => setActiveTab(e.index)} className="auth-tabs">
        <TabPanel header="Login" leftIcon="pi pi-fw pi-sign-in">
          <LoginForm
            onLoginSuccess={handleLoginSuccess}
            onForgotPassword={() => setShowForgotPassword(true)}
          />
        </TabPanel>

        <TabPanel header="Staff Sign Up" leftIcon="pi pi-fw pi-user-plus">
          <StaffSignupForm
            onBack={() => setActiveTab(0)}
            onSignupSuccess={handleSignupSuccess}
          />
        </TabPanel>

        <TabPanel header="Student Sign Up" leftIcon="pi pi-fw pi-graduation-cap">
          <StudentSignupForm
            onBack={() => setActiveTab(0)}
            onSignupSuccess={handleSignupSuccess}
          />
        </TabPanel>
      </TabView>
    </div>
  );
}
