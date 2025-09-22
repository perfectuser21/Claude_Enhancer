import React, { useState } from 'react';
import { authAPI } from '../services/authAPI';
import { validateEmail } from '../utils/validation';
import { useNotification } from '../hooks/useNotification';
import LoadingSpinner from '../../common/components/LoadingSpinner';

const ForgotPassword = ({ onSwitchToLogin }) => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [errors, setErrors] = useState({});

  const { showNotification } = useNotification();

  const handleChange = (e) => {
    setEmail(e.target.value);

    // Clear error when user starts typing
    if (errors.email) {
      setErrors({});
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!validateEmail(email)) {
      newErrors.email = 'Please enter a valid email address';
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
      await authAPI.forgotPassword(email);

      setIsSubmitted(true);
      showNotification(
        'Password reset instructions have been sent to your email.',
        'success'
      );
    } catch (error) {
      const errorMessage = error.response?.data?.message ||
        'Failed to send password reset email. Please try again.';

      showNotification(errorMessage, 'error');

      if (error.response?.status === 404) {
        setErrors({ email: 'No account found with this email address' });
      } else if (error.response?.status === 429) {
        setErrors({
          general: 'Too many reset attempts. Please try again later.'
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setIsLoading(true);

    try {
      await authAPI.forgotPassword(email);
      showNotification('Password reset email resent successfully.', 'success');
    } catch (error) {
      showNotification('Failed to resend email. Please try again.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="auth-form-container">
        <div className="success-state">
          <div className="success-icon">📧</div>
          <h2>Check Your Email</h2>
          <p>
            We've sent password reset instructions to:
          </p>
          <div className="email-display">{email}</div>

          <div className="success-instructions">
            <h3>What to do next:</h3>
            <ol>
              <li>Check your email inbox (and spam folder)</li>
              <li>Click the reset link in the email</li>
              <li>Follow the instructions to create a new password</li>
            </ol>
          </div>

          <div className="success-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={handleResend}
              disabled={isLoading}
            >
              {isLoading ? <LoadingSpinner size="small" /> : 'Resend Email'}
            </button>

            <button
              type="button"
              className="primary-button"
              onClick={onSwitchToLogin}
            >
              Back to Login
            </button>
          </div>

          <div className="help-text">
            <p>
              <strong>Didn't receive the email?</strong>
            </p>
            <ul>
              <li>Check your spam or junk folder</li>
              <li>Make sure the email address is correct</li>
              <li>Try resending the email</li>
              <li>Contact support if you continue having issues</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-form-container">
      <div className="auth-form-header">
        <h2>Reset Your Password</h2>
        <p>Enter your email address and we'll send you instructions to reset your password</p>
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
            value={email}
            onChange={handleChange}
            className={`form-input ${errors.email ? 'error' : ''}`}
            placeholder="Enter your email address"
            disabled={isLoading}
            autoComplete="email"
            required
            autoFocus
          />
          {errors.email && <span className="error-message">{errors.email}</span>}
        </div>

        <button
          type="submit"
          className="submit-button"
          disabled={isLoading || !email}
        >
          {isLoading ? <LoadingSpinner size="small" /> : 'Send Reset Instructions'}
        </button>
      </form>

      <div className="auth-form-footer">
        <span>Remember your password? </span>
        <button
          type="button"
          className="link-button"
          onClick={onSwitchToLogin}
          disabled={isLoading}
        >
          Back to Login
        </button>
      </div>

      <div className="security-note">
        <div className="note-icon">🔒</div>
        <p>
          For your security, password reset links expire after 1 hour.
          If you don't receive an email within a few minutes, please check your spam folder.
        </p>
      </div>
    </div>
  );
};

export default ForgotPassword;