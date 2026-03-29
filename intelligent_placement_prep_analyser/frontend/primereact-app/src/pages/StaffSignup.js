import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card } from 'primereact/card';
import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';
import { Button } from 'primereact/button';
import { Message } from 'primereact/message';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

export default function StaffSignup() {
  const navigate = useNavigate();
  const { staffSignup } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    staff_id: '',
    position: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const validateForm = () => {
    if (!formData.name || !formData.email || !formData.password || !formData.staff_id || !formData.position) {
      setError('All fields are required');
      return false;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) return;

    setLoading(true);

    try {
      await staffSignup({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        staff_id: formData.staff_id,
        position: formData.position,
      });
      navigate('/staff/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <Card className="auth-card">
        <h2 className="auth-title">Staff Sign Up</h2>

        {error && <Message severity="error" text={error} style={{ marginBottom: '1rem' }} />}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Full Name</label>
            <InputText
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Enter your full name"
              required
              className="w-full"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <InputText
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
              required
              className="w-full"
            />
          </div>

          <div className="form-group">
            <label htmlFor="staff_id">Staff ID</label>
            <InputText
              id="staff_id"
              name="staff_id"
              value={formData.staff_id}
              onChange={handleChange}
              placeholder="Enter your staff ID"
              required
              className="w-full"
            />
          </div>

          <div className="form-group">
            <label htmlFor="position">Position/Designation</label>
            <InputText
              id="position"
              name="position"
              value={formData.position}
              onChange={handleChange}
              placeholder="e.g., Associate Professor, Coordinator"
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

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <Password
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Confirm your password"
              toggleMask
              required
              className="w-full"
              inputClassName="w-full"
              feedback={false}
            />
          </div>

          <Button
            type="submit"
            label="Sign Up"
            icon="pi pi-user-plus"
            loading={loading}
            className="w-full auth-button"
          />
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="auth-link">
              Login here
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
}
