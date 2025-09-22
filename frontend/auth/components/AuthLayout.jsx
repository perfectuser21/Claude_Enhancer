import React, { useState } from 'react';
import { AuthProvider } from '../context/AuthContext';
import { NotificationProvider } from '../hooks/useNotification';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import MFASetup from './MFASetup';
import ForgotPassword from './ForgotPassword';
import NotificationDisplay from './NotificationDisplay';

const AuthLayout = ({ initialView = 'login' }) => {
  const [currentView, setCurrentView] = useState(initialView);

  const renderView = () => {
    switch (currentView) {
      case 'register':
        return (
          <RegisterForm
            onSwitchToLogin={() => setCurrentView('login')}
          />
        );

      case 'forgot-password':
        return (
          <ForgotPassword
            onSwitchToLogin={() => setCurrentView('login')}
          />
        );

      case 'mfa-setup':
        return (
          <MFASetup
            onComplete={() => setCurrentView('login')}
            onSkip={() => setCurrentView('login')}
          />
        );

      case 'login':
      default:
        return (
          <LoginForm
            onSwitchToRegister={() => setCurrentView('register')}
            onForgotPassword={() => setCurrentView('forgot-password')}
          />
        );
    }
  };

  return (
    <NotificationProvider>
      <AuthProvider>
        <div className="auth-layout">
          <div className="auth-container">
            <div className="auth-brand">
              <div className="brand-logo">
                <h1>Perfect21</h1>
              </div>
              <div className="brand-tagline">
                <p>Secure authentication for modern applications</p>
              </div>
            </div>

            <div className="auth-content">
              {renderView()}
            </div>

            <div className="auth-footer">
              <div className="footer-links">
                <a href="/privacy" target="_blank" rel="noopener noreferrer">
                  Privacy Policy
                </a>
                <a href="/terms" target="_blank" rel="noopener noreferrer">
                  Terms of Service
                </a>
                <a href="/support" target="_blank" rel="noopener noreferrer">
                  Support
                </a>
              </div>
              <div className="footer-security">
                <div className="security-badge">
                  <span className="security-icon">🔒</span>
                  <span>Secured with 256-bit SSL encryption</span>
                </div>
              </div>
            </div>
          </div>

          <NotificationDisplay />
        </div>
      </AuthProvider>
    </NotificationProvider>
  );
};

export default AuthLayout;