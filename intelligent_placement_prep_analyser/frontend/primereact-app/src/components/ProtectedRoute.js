import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute = ({ children, role = null }) => {
  const { isAuthenticated, loading, user } = useAuth();

  if (loading) {
    return <div style={{ padding: '20px' }}>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (role && user?.role !== role) {
    return <Navigate to={user?.role === 'student' ? '/student/dashboard' : '/staff/dashboard'} replace />;
  }

  return children;
};

export default ProtectedRoute;
