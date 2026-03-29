import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card } from 'primereact/card';
import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';
import { Dropdown } from 'primereact/dropdown';
import { Button } from 'primereact/button';
import { Message } from 'primereact/message';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

const DEPARTMENTS = [
  { label: 'Computer Science Engineering', value: 'CSE' },
  { label: 'Information Technology', value: 'IT' },
  { label: 'Electrical Engineering', value: 'EEE' },
  { label: 'Electronics Engineering', value: 'ECE' },
  { label: 'Mechanical Engineering', value: 'MECH' },
  { label: 'Civil Engineering', value: 'CIVL' },
  { label: 'Computer Science & Business Systems', value: 'CSBS' },
];

const BATCHES = [
  { label: '2024-2027', value: '2024-2027' },
  { label: '2025-2028', value: '2025-2028' },
];

export default function StudentSignup() {
  const navigate = useNavigate();
  const { studentSignup } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    department: '',
    batch: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleDropdownChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError('');
  };

  const validateForm = () => {
    if (!formData.name || !formData.email || !formData.password || !formData.department || !formData.batch) {
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
      await studentSignup({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        department: formData.department,
        batch: formData.batch,
      });
      navigate('/student/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <Card className="auth-card">
        <h2 className="auth-title">Student Sign Up</h2>

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
            <label htmlFor="department">Department</label>
            <Dropdown
              id="department"
              value={formData.department}
              options={DEPARTMENTS}
              onChange={(e) => handleDropdownChange('department', e.value)}
              placeholder="Select your department"
              className="w-full"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="batch">Batch</label>
            <Dropdown
              id="batch"
              value={formData.batch}
              options={BATCHES}
              onChange={(e) => handleDropdownChange('batch', e.value)}
              placeholder="Select your batch"
              className="w-full"
              required
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
