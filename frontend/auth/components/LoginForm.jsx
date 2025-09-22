import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { validateEmail, validatePassword } from '../utils/validation';
import { useNotification } from '../hooks/useNotification';
import LoadingSpinner from '../../common/components/LoadingSpinner';

const LoginForm = ({ onSwitchToRegister, onForgotPassword }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });

  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useContext(AuthContext);
  const { showNotification } = useNotification();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!validatePassword(formData.password)) {
      newErrors.password = 'Password must be at least 8 characters';
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
      await login({
        email: formData.email,
        password: formData.password,
        rememberMe: formData.rememberMe
      });

      showNotification('Login successful! Welcome back.', 'success');
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Login failed. Please try again.';
      showNotification(errorMessage, 'error');

      if (error.response?.status === 429) {
        setErrors({ general: 'Too many login attempts. Please try again later.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-form-container">
      <div className="auth-form-header">
        <h2>Welcome Back</h2>
        <p>Please sign in to your account</p>
      </div>

      <form onSubmit={handleSubmit} className="auth-form">
        {errors.general && (
          <div className="error-message general-error">
            {errors.general}
          </div>
        )}

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
            placeholder="Enter your password"
            disabled={isLoading}
            autoComplete="current-password"
            required
          />
          {errors.password && <span className="error-message">{errors.password}</span>}
        </div>

        <div className="form-options">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="rememberMe"
              checked={formData.rememberMe}
              onChange={handleChange}
              disabled={isLoading}
            />
            <span className="checkmark"></span>
            Remember me
          </label>

          <button
            type="button"
            className="link-button"
            onClick={onForgotPassword}
            disabled={isLoading}
          >
            Forgot password?
          </button>
        </div>

        <button
          type="submit"
          className="submit-button"
          disabled={isLoading}
        >
          {isLoading ? <LoadingSpinner size="small" /> : 'Sign In'}
        </button>
      </form>

      <div className="auth-form-footer">
        <span>Don't have an account? </span>
        <button
          type="button"
          className="link-button"
          onClick={onSwitchToRegister}
          disabled={isLoading}
        >
          Sign up here
        </button>
      </div>
    </div>
  );
};

export default LoginForm;