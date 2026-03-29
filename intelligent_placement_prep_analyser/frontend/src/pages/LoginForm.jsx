import React, { useState } from 'react';
import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';
import { Button } from 'primereact/button';
import { Card } from 'primereact/card';
import { Message } from 'primereact/message';
import authService from '../services/authService.js';
import '../styles/Auth.css';

export default function LoginForm({ onLoginSuccess, onForgotPassword }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const validateForm = () => {
    if (!email.trim()) {
      setError('Email is required');
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address');
      return false;
    }
    if (!password) {
      setError('Password is required');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) return;

    setLoading(true);
    try {
      const response = await authService.login(email, password);
      const { access_token, role, user_id } = response.data;
      
      // Store token and user info
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user_role', role);
      localStorage.setItem('user_id', user_id);
      
      onLoginSuccess(role);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setEmail('');
    setPassword('');
    setError(null);
  };

  return (
    <Card className="auth-card">
      <h2>Login</h2>
      
      {error && <Message severity="error" text={error} className="mb-3" />}

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="login-email">Email Address</label>
          <InputText
            id="login-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            className="w-full"
          />
        </div>

        <div className="form-group">
          <label htmlFor="login-password">Password</label>
          <Password
            id="login-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            toggleMask
            className="w-full"
            feedback={false}
          />
        </div>

        <div className="form-actions">
          <Button
            type="submit"
            label="Login"
            icon="pi pi-sign-in"
            loading={loading}
            className="w-full mb-2"
          />
          <Button
            type="button"
            label="Clear"
            icon="pi pi-times"
            onClick={handleClear}
            className="w-full p-button-secondary mb-3"
          />
        </div>

        <div className="forgot-password-link">
          <Button
            type="button"
            label="Forgot Password?"
            onClick={onForgotPassword}
            className="p-button-link"
          />
        </div>
      </form>
    </Card>
  );
}
