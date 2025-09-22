import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { validateEmail, validatePassword, validatePasswordStrength } from '../utils/validation';
import { useNotification } from '../hooks/useNotification';
import LoadingSpinner from '../../common/components/LoadingSpinner';
import PasswordStrengthIndicator from './PasswordStrengthIndicator';

const RegisterForm = ({ onSwitchToLogin }) => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false
  });

  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(null);

  const { register } = useContext(AuthContext);
  const { showNotification } = useNotification();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;

    setFormData(prev => ({
      ...prev,
      [name]: newValue
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }

    // Update password strength in real-time
    if (name === 'password') {
      setPasswordStrength(validatePasswordStrength(newValue));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    }

    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    }

    if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!validatePassword(formData.password)) {
      newErrors.password = 'Password must be at least 8 characters with uppercase, lowercase, number, and special character';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (!formData.acceptTerms) {
      newErrors.acceptTerms = 'You must accept the terms and conditions';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      await register({
        firstName: formData.firstName.trim(),
        lastName: formData.lastName.trim(),
        email: formData.email.toLowerCase(),
        password: formData.password
      });

      showNotification('Registration successful! Please check your email to verify your account.', 'success');
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Registration failed. Please try again.';
      showNotification(errorMessage, 'error');

      if (error.response?.status === 409) {
        setErrors({ email: 'This email is already registered' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-form-container">
      <div className="auth-form-header">
        <h2>Create Account</h2>
        <p>Join us today! Please fill in your information</p>
      </div>

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="firstName">First Name</label>
            <input
              type="text"
              id="firstName"
              name="firstName"
              value={formData.firstName}
              onChange={handleChange}
              className={`form-input ${errors.firstName ? 'error' : ''}`}
              placeholder="Enter your first name"
              disabled={isLoading}
              autoComplete="given-name"
              required
            />
            {errors.firstName && <span className="error-message">{errors.firstName}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="lastName">Last Name</label>
            <input
              type="text"
              id="lastName"
              name="lastName"
              value={formData.lastName}
              onChange={handleChange}
              className={`form-input ${errors.lastName ? 'error' : ''}`}
              placeholder="Enter your last name"
              disabled={isLoading}
              autoComplete="family-name"
              required
            />
            {errors.lastName && <span className="error-message">{errors.lastName}</span>}
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="email">Email Address</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className={`form-input ${errors.email ? 'error' : ''}`}
            placeholder="Enter your email"
            disabled={isLoading}
            autoComplete="email"
            required
          />
          {errors.email && <span className="error-message">{errors.email}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            className={`form-input ${errors.password ? 'error' : ''}`}
            placeholder="Create a strong password"
            disabled={isLoading}
            autoComplete="new-password"
            required
          />
          {formData.password && (
            <PasswordStrengthIndicator strength={passwordStrength} />
          )}
          {errors.password && <span className="error-message">{errors.password}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            className={`form-input ${errors.confirmPassword ? 'error' : ''}`}
            placeholder="Confirm your password"
            disabled={isLoading}
            autoComplete="new-password"
            required
          />
          {errors.confirmPassword && <span className="error-message">{errors.confirmPassword}</span>}
        </div>

        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="acceptTerms"
              checked={formData.acceptTerms}
              onChange={handleChange}
              disabled={isLoading}
              required
            />
            <span className="checkmark"></span>
            I agree to the <a href="/terms" target="_blank" rel="noopener noreferrer">Terms of Service</a> and <a href="/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
          </label>
          {errors.acceptTerms && <span className="error-message">{errors.acceptTerms}</span>}
        </div>

        <button
          type="submit"
          className="submit-button"
          disabled={isLoading || !formData.acceptTerms}
        >
          {isLoading ? <LoadingSpinner size="small" /> : 'Create Account'}
        </button>
      </form>

      <div className="auth-form-footer">
        <span>Already have an account? </span>
        <button
          type="button"
          className="link-button"
          onClick={onSwitchToLogin}
          disabled={isLoading}
        >
          Sign in here
        </button>
      </div>
    </div>
  );
};

export default RegisterForm;