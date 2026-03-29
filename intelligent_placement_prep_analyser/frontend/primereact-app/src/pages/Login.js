import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card } from 'primereact/card';
import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';
import { Button } from 'primereact/button';
import { Message } from 'primereact/message';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const user = await login(formData.email, formData.password);
      if (user.role === 'student') {
        navigate('/student/dashboard');
      } else if (user.role === 'staff') {
        navigate('/staff/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <Card className="auth-card">
        <h2 className="auth-title">Login</h2>
        
        {error && <Message severity="error" text={error} style={{ marginBottom: '1rem' }} />}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <InputText
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
              required
              className="w-full"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <Password
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              toggleMask
              required
              className="w-full"
              inputClassName="w-full"
            />
          </div>

          <Button
            type="submit"
            label="Login"
            icon="pi pi-sign-in"
            loading={loading}
            className="w-full auth-button"
          />
        </form>

        <div className="auth-footer">
          <p>
            Student?{' '}
            <Link to="/student/signup" className="auth-link">
              Sign up here
            </Link>
          </p>
          <p>
            Staff?{' '}
            <Link to="/staff/signup" className="auth-link">
              Sign up here
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
}
