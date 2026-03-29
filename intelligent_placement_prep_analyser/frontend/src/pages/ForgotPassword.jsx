import React, { useState } from 'react';
import { InputText } from 'primereact/inputtext';
import { Button } from 'primereact/button';
import { Card } from 'primereact/card';
import { Message } from 'primereact/message';
import authService from '../services/authService.js';
import '../styles/Auth.css';

export default function ForgotPassword({ onBack }) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (!email.trim()) {
      setError('Email is required');
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    try {
      const response = await authService.forgotPassword(email);
      setMessage('If this email exists, a password reset link has been sent');
      setEmail('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process forgot password request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="auth-card">
      <h2>Forgot Password</h2>
      
      {error && <Message severity="error" text={error} className="mb-3" />}
      {message && <Message severity="success" text={message} className="mb-3" />}

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="reset-email">Email Address</label>
          <InputText
            id="reset-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            className="w-full"
          />
        </div>

        <div className="form-actions">
          <Button
            type="submit"
            label="Submit"
            icon="pi pi-check"
            loading={loading}
            className="w-full mb-2"
          />
          <Button
            type="button"
            label="Back to Login"
            icon="pi pi-arrow-left"
            onClick={onBack}
            className="w-full p-button-secondary"
          />
        </div>
      </form>
    </Card>
  );
}
