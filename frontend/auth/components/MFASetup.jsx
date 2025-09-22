import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNotification } from '../hooks/useNotification';
import LoadingSpinner from '../../common/components/LoadingSpinner';
import QRCodeDisplay from './QRCodeDisplay';

const MFASetup = ({ onComplete, onSkip }) => {
  const [step, setStep] = useState(1); // 1: Choose method, 2: Setup, 3: Verify
  const [selectedMethod, setSelectedMethod] = useState('');
  const [setupData, setSetupData] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const { setupMFA, verifyMFA } = useContext(AuthContext);
  const { showNotification } = useNotification();

  const mfaMethods = [
    {
      id: 'totp',
      name: 'Authenticator App',
      description: 'Use Google Authenticator, Authy, or similar apps',
      icon: '📱',
      recommended: true
    },
    {
      id: 'sms',
      name: 'SMS',
      description: 'Receive codes via text message',
      icon: '💬',
      recommended: false
    },
    {
      id: 'email',
      name: 'Email',
      description: 'Receive codes via email',
      icon: '📧',
      recommended: false
    }
  ];

  const handleMethodSelect = (methodId) => {
    setSelectedMethod(methodId);
    setErrors({});
  };

  const handleSetupStart = async () => {
    if (!selectedMethod) {
      setErrors({ method: 'Please select a verification method' });
      return;
    }

    setIsLoading(true);

    try {
      const response = await setupMFA(selectedMethod);
      setSetupData(response.data);
      setStep(2);
      showNotification('MFA setup initiated. Please follow the instructions.', 'info');
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Failed to setup MFA. Please try again.';
      showNotification(errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerification = async () => {
    if (!verificationCode.trim()) {
      setErrors({ code: 'Please enter the verification code' });
      return;
    }

    setIsLoading(true);

    try {
      await verifyMFA({
        method: selectedMethod,
        code: verificationCode.trim(),
        setupToken: setupData?.setupToken
      });

      showNotification('MFA setup completed successfully!', 'success');
      setStep(3);

      // Auto-complete after 2 seconds
      setTimeout(() => {
        onComplete();
      }, 2000);
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Invalid verification code. Please try again.';
      setErrors({ code: errorMessage });
      showNotification(errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStepOne = () => (
    <div className="mfa-setup-step">
      <div className="step-header">
        <h3>Choose Your Verification Method</h3>
        <p>Select how you'd like to receive verification codes</p>
      </div>

      <div className="mfa-methods">
        {mfaMethods.map((method) => (
          <div
            key={method.id}
            className={`mfa-method ${selectedMethod === method.id ? 'selected' : ''}`}
            onClick={() => handleMethodSelect(method.id)}
          >
            <div className="method-icon">{method.icon}</div>
            <div className="method-info">
              <div className="method-name">
                {method.name}
                {method.recommended && <span className="recommended-badge">Recommended</span>}
              </div>
              <div className="method-description">{method.description}</div>
            </div>
            <div className="method-selector">
              <input
                type="radio"
                name="mfaMethod"
                value={method.id}
                checked={selectedMethod === method.id}
                onChange={() => handleMethodSelect(method.id)}
              />
            </div>
          </div>
        ))}
      </div>

      {errors.method && <div className="error-message">{errors.method}</div>}

      <div className="step-actions">
        <button
          type="button"
          className="secondary-button"
          onClick={onSkip}
          disabled={isLoading}
        >
          Skip for Now
        </button>
        <button
          type="button"
          className="primary-button"
          onClick={handleSetupStart}
          disabled={isLoading || !selectedMethod}
        >
          {isLoading ? <LoadingSpinner size="small" /> : 'Continue'}
        </button>
      </div>
    </div>
  );

  const renderStepTwo = () => (
    <div className="mfa-setup-step">
      <div className="step-header">
        <h3>Setup {mfaMethods.find(m => m.id === selectedMethod)?.name}</h3>
        <p>Follow the instructions below to complete setup</p>
      </div>

      <div className="setup-instructions">
        {selectedMethod === 'totp' && (
          <div className="totp-setup">
            <div className="instruction-step">
              <div className="step-number">1</div>
              <div className="step-content">
                <p>Install an authenticator app on your phone:</p>
                <ul>
                  <li>Google Authenticator</li>
                  <li>Authy</li>
                  <li>Microsoft Authenticator</li>
                </ul>
              </div>
            </div>

            <div className="instruction-step">
              <div className="step-number">2</div>
              <div className="step-content">
                <p>Scan this QR code with your authenticator app:</p>
                {setupData?.qrCode && (
                  <QRCodeDisplay
                    qrCode={setupData.qrCode}
                    manualCode={setupData.manualCode}
                  />
                )}
              </div>
            </div>

            <div className="instruction-step">
              <div className="step-number">3</div>
              <div className="step-content">
                <p>Enter the 6-digit code from your authenticator app:</p>
                <input
                  type="text"
                  className={`verification-input ${errors.code ? 'error' : ''}`}
                  placeholder="000000"
                  value={verificationCode}
                  onChange={(e) => {
                    setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6));
                    if (errors.code) setErrors({ ...errors, code: '' });
                  }}
                  maxLength={6}
                  disabled={isLoading}
                />
              </div>
            </div>
          </div>
        )}

        {selectedMethod === 'sms' && (
          <div className="sms-setup">
            <p>We'll send verification codes to your phone number:</p>
            <div className="phone-display">{setupData?.phoneNumber}</div>
            <p>Enter the code you receive:</p>
            <input
              type="text"
              className={`verification-input ${errors.code ? 'error' : ''}`}
              placeholder="000000"
              value={verificationCode}
              onChange={(e) => {
                setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6));
                if (errors.code) setErrors({ ...errors, code: '' });
              }}
              maxLength={6}
              disabled={isLoading}
            />
          </div>
        )}

        {selectedMethod === 'email' && (
          <div className="email-setup">
            <p>We'll send verification codes to your email:</p>
            <div className="email-display">{setupData?.email}</div>
            <p>Enter the code you receive:</p>
            <input
              type="text"
              className={`verification-input ${errors.code ? 'error' : ''}`}
              placeholder="000000"
              value={verificationCode}
              onChange={(e) => {
                setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6));
                if (errors.code) setErrors({ ...errors, code: '' });
              }}
              maxLength={6}
              disabled={isLoading}
            />
          </div>
        )}
      </div>

      {errors.code && <div className="error-message">{errors.code}</div>}

      <div className="step-actions">
        <button
          type="button"
          className="secondary-button"
          onClick={() => setStep(1)}
          disabled={isLoading}
        >
          Back
        </button>
        <button
          type="button"
          className="primary-button"
          onClick={handleVerification}
          disabled={isLoading || verificationCode.length !== 6}
        >
          {isLoading ? <LoadingSpinner size="small" /> : 'Verify & Complete'}
        </button>
      </div>
    </div>
  );

  const renderStepThree = () => (
    <div className="mfa-setup-step">
      <div className="success-message">
        <div className="success-icon">✅</div>
        <h3>MFA Setup Complete!</h3>
        <p>Your account is now protected with two-factor authentication.</p>
      </div>
    </div>
  );

  return (
    <div className="mfa-setup-container">
      <div className="setup-progress">
        <div className={`progress-step ${step >= 1 ? 'active' : ''}`}>
          <div className="step-circle">1</div>
          <span>Choose Method</span>
        </div>
        <div className={`progress-step ${step >= 2 ? 'active' : ''}`}>
          <div className="step-circle">2</div>
          <span>Setup</span>
        </div>
        <div className={`progress-step ${step >= 3 ? 'active' : ''}`}>
          <div className="step-circle">3</div>
          <span>Complete</span>
        </div>
      </div>

      {step === 1 && renderStepOne()}
      {step === 2 && renderStepTwo()}
      {step === 3 && renderStepThree()}
    </div>
  );
};

export default MFASetup;