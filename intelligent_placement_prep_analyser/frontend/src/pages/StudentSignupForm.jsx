import React, { useState, useEffect } from 'react';
import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';
import { Dropdown } from 'primereact/dropdown';
import { Button } from 'primereact/button';
import { Card } from 'primereact/card';
import { Message } from 'primereact/message';
import authService from '../services/authService.js';
import '../styles/Auth.css';

export default function StudentSignupForm({ onBack, onSignupSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    departmentId: null,
    section: null,
    password: '',
    confirmPassword: '',
  });

  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const sections = [
    { label: 'A', value: 'A' },
    { label: 'B', value: 'B' },
    { label: 'C', value: 'C' },
  ];

  useEffect(() => {
    fetchDepartments();
  }, []);

  const fetchDepartments = async () => {
    try {
      const response = await authService.getDepartments();
      setDepartments(response.data);
    } catch (err) {
      setError('Failed to load departments');
    }
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError('Name is required');
      return false;
    }
    if (formData.name.trim().length < 2) {
      setError('Name must be at least 2 characters long');
      return false;
    }
    if (!formData.email.trim()) {
      setError('Email is required');
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }
    if (!formData.departmentId) {
      setError('Please select a department');
      return false;
    }
    if (!formData.section) {
      setError('Please select a section');
      return false;
    }
    if (!formData.password) {
      setError('Password is required');
      return false;
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    return true;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleDepartmentChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      departmentId: e.value.id,
    }));
  };

  const handleSectionChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      section: e.value,
    }));
  };

  const handleClear = () => {
    setFormData({
      name: '',
      email: '',
      departmentId: null,
      section: null,
      password: '',
      confirmPassword: '',
    });
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) return;

    setLoading(true);
    try {
      await authService.studentSignup(
        formData.name,
        formData.email,
        formData.departmentId,
        formData.section,
        formData.password,
        formData.confirmPassword
      );
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onSignupSuccess();
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="auth-card signup-card">
      <h2>Student Registration</h2>
      
      {error && <Message severity="error" text={error} className="mb-3" />}
      {success && <Message severity="success" text="Registration successful!" className="mb-3" />}

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="student-name">Name of Student</label>
          <div className="p-inputgroup">
            <InputText
              id="student-name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Enter your full name"
              className="w-full"
            />
            <Button
              icon="pi pi-times"
              className="p-button-danger"
              onClick={() => setFormData((prev) => ({ ...prev, name: '' }))}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="student-email">Email Address</label>
          <div className="p-inputgroup">
            <InputText
              id="student-email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
              className="w-full"
            />
            <Button
              icon="pi pi-times"
              className="p-button-danger"
              onClick={() => setFormData((prev) => ({ ...prev, email: '' }))}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="student-dept">Department</label>
          <Dropdown
            id="student-dept"
            value={departments.find((d) => d.id === formData.departmentId) || null}
            onChange={handleDepartmentChange}
            options={departments}
            optionLabel="name"
            placeholder="Select Department"
            className="w-full"
          />
        </div>

        <div className="form-group">
          <label htmlFor="student-section">Section</label>
          <Dropdown
            id="student-section"
            value={formData.section}
            onChange={handleSectionChange}
            options={sections}
            placeholder="Select Section"
            className="w-full"
          />
        </div>

        <div className="form-group">
          <label htmlFor="student-password">Password</label>
          <div className="p-inputgroup">
            <Password
              id="student-password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter password (min 8 characters)"
              toggleMask
              className="w-full"
              feedback={false}
            />
            <Button
              icon="pi pi-times"
              className="p-button-danger"
              onClick={() => setFormData((prev) => ({ ...prev, password: '' }))}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="student-confirm-password">Confirm Password</label>
          <div className="p-inputgroup">
            <Password
              id="student-confirm-password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Confirm password"
              toggleMask
              className="w-full"
              feedback={false}
            />
            <Button
              icon="pi pi-times"
              className="p-button-danger"
              onClick={() => setFormData((prev) => ({ ...prev, confirmPassword: '' }))}
            />
          </div>
        </div>

        <div className="form-actions">
          <Button
            type="submit"
            label="Register"
            icon="pi pi-check"
            loading={loading}
            className="w-full mb-2"
          />
          <Button
            type="button"
            label="Back"
            icon="pi pi-arrow-left"
            onClick={onBack}
            className="w-full p-button-secondary"
          />
        </div>
      </form>
    </Card>
  );
}
