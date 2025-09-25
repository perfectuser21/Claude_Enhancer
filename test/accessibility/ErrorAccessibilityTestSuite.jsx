/**
 * React Component Test Suite for Error Message Accessibility
 * Phase 4: Local Testing - Interactive Error Accessibility Testing
 *
 * Tests real React components for:
 * 1. Error messages are clear and actionable
 * 2. Recovery options are easily accessible
 * 3. Status indicators are perceivable
 * 4. Keyboard navigation works in recovery flows
 */

import React, { useState, useRef, useEffect } from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

/**
 * Enhanced Error Message Component with Accessibility Features
 */
const AccessibleErrorMessage = ({
  type = 'error',
  message,
  onRetry,
  onDismiss,
  actionable = true,
  autoFocus = true
}) => {
  const errorRef = useRef(null);

  useEffect(() => {
    if (autoFocus && errorRef.current) {
      // Move focus to error message for screen readers
      errorRef.current.focus();
    }
  }, [autoFocus, message]);

  const getAriaLive = () => {
    switch (type) {
      case 'error':
        return 'assertive';
      case 'warning':
        return 'polite';
      case 'success':
        return 'polite';
      default:
        return 'polite';
    }
  };

  const getIcon = () => {
    const icons = {
      error: '❌',
      warning: '⚠️',
      success: '✅',
      info: 'ℹ️'
    };
    return icons[type] || icons.info;
  };

  return (
    <div
      className={`notification notification-${type}`}
      role="alert"
      aria-live={getAriaLive()}
      aria-atomic="true"
      tabIndex={-1}
      ref={errorRef}
    >
      <div className="notification-content">
        <div
          className="notification-icon"
          aria-hidden="true"
          role="img"
          aria-label={`${type} indicator`}
        >
          {getIcon()}
        </div>

        <div className="notification-message">
          {message}
        </div>

        {actionable && (onRetry || onDismiss) && (
          <div className="notification-actions">
            {onRetry && (
              <button
                type="button"
                className="notification-action-button primary"
                onClick={onRetry}
                aria-describedby="retry-help"
              >
                Try Again
              </button>
            )}

            {onDismiss && (
              <button
                type="button"
                className="notification-close"
                onClick={onDismiss}
                aria-label="Dismiss error message"
              >
                ×
              </button>
            )}
          </div>
        )}
      </div>

      <div id="retry-help" className="sr-only">
        Retry the failed operation
      </div>
    </div>
  );
};

/**
 * Enhanced Recovery Flow Component
 */
const AccessibleRecoveryFlow = ({
  error,
  onRecover,
  onCancel,
  currentStep = 0,
  totalSteps = 3
}) => {
  const [step, setStep] = useState(currentStep);
  const [loading, setLoading] = useState(false);
  const [recoveryData, setRecoveryData] = useState({});
  const stepRefs = useRef([]);

  // Focus management when step changes
  useEffect(() => {
    if (stepRefs.current[step]) {
      stepRefs.current[step].focus();
    }
  }, [step]);

  const handleNext = async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate async operation
      if (step < totalSteps - 1) {
        setStep(step + 1);
      } else {
        onRecover(recoveryData);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div className="recovery-step" role="group" aria-labelledby="step-0-title">
            <h3 id="step-0-title" ref={el => stepRefs.current[0] = el} tabIndex={-1}>
              Step 1: Identify the Issue
            </h3>
            <p>We've detected a {error.type} error. Let's work together to resolve it.</p>
            <div className="error-details" role="region" aria-label="Error details">
              <strong>Error:</strong> {error.message}
            </div>
          </div>
        );

      case 1:
        return (
          <div className="recovery-step" role="group" aria-labelledby="step-1-title">
            <h3 id="step-1-title" ref={el => stepRefs.current[1] = el} tabIndex={-1}>
              Step 2: Choose Recovery Method
            </h3>
            <fieldset>
              <legend>Select a recovery option:</legend>
              <div className="recovery-options">
                <label className="recovery-option">
                  <input
                    type="radio"
                    name="recovery-method"
                    value="retry"
                    onChange={(e) => setRecoveryData({...recoveryData, method: e.target.value})}
                  />
                  <span>Retry the operation</span>
                </label>
                <label className="recovery-option">
                  <input
                    type="radio"
                    name="recovery-method"
                    value="reset"
                    onChange={(e) => setRecoveryData({...recoveryData, method: e.target.value})}
                  />
                  <span>Reset and start over</span>
                </label>
                <label className="recovery-option">
                  <input
                    type="radio"
                    name="recovery-method"
                    value="skip"
                    onChange={(e) => setRecoveryData({...recoveryData, method: e.target.value})}
                  />
                  <span>Skip this step</span>
                </label>
              </div>
            </fieldset>
          </div>
        );

      case 2:
        return (
          <div className="recovery-step" role="group" aria-labelledby="step-2-title">
            <h3 id="step-2-title" ref={el => stepRefs.current[2] = el} tabIndex={-1}>
              Step 3: Confirm Recovery
            </h3>
            <p>You selected: <strong>{recoveryData.method}</strong></p>
            <p>Click "Complete Recovery" to proceed with this action.</p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div
      className="recovery-flow"
      role="region"
      aria-label="Error recovery workflow"
      aria-live="polite"
    >
      {/* Progress indicator */}
      <div
        className="recovery-progress"
        role="progressbar"
        aria-valuenow={step + 1}
        aria-valuemin={1}
        aria-valuemax={totalSteps}
        aria-label={`Recovery step ${step + 1} of ${totalSteps}`}
      >
        <div className="progress-bar">
          {Array.from({ length: totalSteps }, (_, i) => (
            <div
              key={i}
              className={`progress-step ${i <= step ? 'completed' : ''}`}
              aria-current={i === step ? 'step' : undefined}
            >
              {i + 1}
            </div>
          ))}
        </div>
        <div className="progress-text">
          Step {step + 1} of {totalSteps}
        </div>
      </div>

      {/* Current step content */}
      {renderStep()}

      {/* Navigation */}
      <div className="recovery-navigation" role="group" aria-label="Navigation">
        <button
          type="button"
          className="secondary-button"
          onClick={step === 0 ? onCancel : handleBack}
          disabled={loading}
        >
          {step === 0 ? 'Cancel' : 'Back'}
        </button>

        <button
          type="button"
          className="primary-button"
          onClick={handleNext}
          disabled={loading || (step === 1 && !recoveryData.method)}
          aria-describedby="next-help"
        >
          {loading ? (
            <>
              <span className="loading-spinner" aria-hidden="true" />
              <span>Processing...</span>
            </>
          ) : step === totalSteps - 1 ? (
            'Complete Recovery'
          ) : (
            'Next'
          )}
        </button>

        <div id="next-help" className="sr-only">
          {step === 1 && !recoveryData.method
            ? 'Please select a recovery method before continuing'
            : 'Continue to the next step'
          }
        </div>
      </div>
    </div>
  );
};

/**
 * Accessible Status Indicator Component
 */
const AccessibleStatusIndicator = ({
  status,
  message,
  progress,
  showProgress = false
}) => {
  const statusConfig = {
    loading: {
      icon: '⏳',
      role: 'status',
      ariaLive: 'polite',
      className: 'status-loading'
    },
    success: {
      icon: '✅',
      role: 'status',
      ariaLive: 'polite',
      className: 'status-success'
    },
    error: {
      icon: '❌',
      role: 'alert',
      ariaLive: 'assertive',
      className: 'status-error'
    },
    warning: {
      icon: '⚠️',
      role: 'status',
      ariaLive: 'polite',
      className: 'status-warning'
    }
  };

  const config = statusConfig[status] || statusConfig.loading;

  return (
    <div
      className={`status-indicator ${config.className}`}
      role={config.role}
      aria-live={config.ariaLive}
      aria-atomic="true"
    >
      <div className="status-content">
        <span
          className="status-icon"
          role="img"
          aria-label={`${status} status`}
        >
          {config.icon}
        </span>

        <span className="status-message">
          {message}
        </span>

        {showProgress && typeof progress === 'number' && (
          <div
            className="status-progress"
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Progress: ${progress}%`}
          >
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
            <span className="progress-text">
              {progress}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Test Suite for Error Accessibility
 */
describe('Error Message Accessibility', () => {
  describe('AccessibleErrorMessage', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <AccessibleErrorMessage
          type="error"
          message="Login failed. Please check your credentials."
          onRetry={() => {}}
          onDismiss={() => {}}
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should announce error messages immediately', () => {
      render(
        <AccessibleErrorMessage
          type="error"
          message="Network connection failed"
          actionable={true}
        />
      );

      const errorMessage = screen.getByRole('alert');
      expect(errorMessage).toHaveAttribute('aria-live', 'assertive');
      expect(errorMessage).toHaveAttribute('aria-atomic', 'true');
      expect(errorMessage).toHaveTextContent('Network connection failed');
    });

    it('should be keyboard accessible', async () => {
      const user = userEvent.setup();
      const onRetry = jest.fn();
      const onDismiss = jest.fn();

      render(
        <AccessibleErrorMessage
          message="Operation failed"
          onRetry={onRetry}
          onDismiss={onDismiss}
        />
      );

      // Should be able to focus and activate retry button
      const retryButton = screen.getByRole('button', { name: /try again/i });
      await user.tab();
      expect(retryButton).toHaveFocus();

      await user.keyboard('{Enter}');
      expect(onRetry).toHaveBeenCalledTimes(1);

      // Should be able to focus and activate dismiss button
      const dismissButton = screen.getByRole('button', { name: /dismiss/i });
      await user.tab();
      expect(dismissButton).toHaveFocus();

      await user.keyboard('{Enter}');
      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    it('should provide clear actionable guidance', () => {
      render(
        <AccessibleErrorMessage
          message="Invalid email format. Please enter a valid email address."
          onRetry={() => {}}
        />
      );

      const message = screen.getByText(/invalid email format/i);
      expect(message).toBeInTheDocument();

      // Should have actionable button
      const actionButton = screen.getByRole('button', { name: /try again/i });
      expect(actionButton).toBeInTheDocument();
      expect(actionButton).toHaveAttribute('aria-describedby', 'retry-help');
    });

    it('should manage focus correctly', () => {
      const { rerender } = render(
        <AccessibleErrorMessage
          message="First error"
          autoFocus={false}
        />
      );

      // Should not have focus initially
      const errorMessage = screen.getByRole('alert');
      expect(errorMessage).not.toHaveFocus();

      // Should focus when autoFocus is enabled
      rerender(
        <AccessibleErrorMessage
          message="Second error"
          autoFocus={true}
        />
      );

      expect(errorMessage).toHaveFocus();
    });
  });

  describe('AccessibleRecoveryFlow', () => {
    const mockError = {
      type: 'authentication',
      message: 'Login session expired'
    };

    it('should have no accessibility violations', async () => {
      const { container } = render(
        <AccessibleRecoveryFlow
          error={mockError}
          onRecover={() => {}}
          onCancel={() => {}}
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should provide proper progress indication', () => {
      render(
        <AccessibleRecoveryFlow
          error={mockError}
          onRecover={() => {}}
          onCancel={() => {}}
          currentStep={1}
          totalSteps={3}
        />
      );

      const progressbar = screen.getByRole('progressbar');
      expect(progressbar).toHaveAttribute('aria-valuenow', '2');
      expect(progressbar).toHaveAttribute('aria-valuemin', '1');
      expect(progressbar).toHaveAttribute('aria-valuemax', '3');
      expect(progressbar).toHaveAttribute('aria-label', 'Recovery step 2 of 3');
    });

    it('should manage keyboard navigation correctly', async () => {
      const user = userEvent.setup();
      const onRecover = jest.fn();
      const onCancel = jest.fn();

      render(
        <AccessibleRecoveryFlow
          error={mockError}
          onRecover={onRecover}
          onCancel={onCancel}
        />
      );

      // Should be able to navigate with keyboard
      await user.tab(); // Focus on cancel button
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      expect(cancelButton).toHaveFocus();

      await user.tab(); // Focus on next button
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toHaveFocus();

      // Should be able to proceed to next step
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText(/step 2/i)).toBeInTheDocument();
      });
    });

    it('should provide proper step navigation', async () => {
      const user = userEvent.setup();

      render(
        <AccessibleRecoveryFlow
          error={mockError}
          onRecover={() => {}}
          onCancel={() => {}}
        />
      );

      // Step 1: Should show initial step
      expect(screen.getByRole('heading', { name: /step 1/i })).toBeInTheDocument();

      // Navigate to step 2
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /step 2/i })).toBeInTheDocument();
      });

      // Should have radio buttons for recovery method
      const radioButtons = screen.getAllByRole('radio');
      expect(radioButtons).toHaveLength(3);

      // Select a recovery method
      await user.click(radioButtons[0]);

      // Navigate to step 3
      const nextButton2 = screen.getByRole('button', { name: /next/i });
      expect(nextButton2).not.toBeDisabled();
      await user.click(nextButton2);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /step 3/i })).toBeInTheDocument();
      });
    });

    it('should handle form validation appropriately', async () => {
      const user = userEvent.setup();

      render(
        <AccessibleRecoveryFlow
          error={mockError}
          onRecover={() => {}}
          onCancel={() => {}}
          currentStep={1}
        />
      );

      // Next button should be disabled if no recovery method is selected
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();

      // Should have help text explaining why button is disabled
      expect(screen.getByText(/please select a recovery method/i)).toBeInTheDocument();

      // Select a method
      const radioButton = screen.getAllByRole('radio')[0];
      await user.click(radioButton);

      // Next button should now be enabled
      expect(nextButton).not.toBeDisabled();
    });
  });

  describe('AccessibleStatusIndicator', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <AccessibleStatusIndicator
          status="loading"
          message="Processing your request..."
          progress={50}
          showProgress={true}
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should announce status changes correctly', () => {
      const { rerender } = render(
        <AccessibleStatusIndicator
          status="loading"
          message="Starting process..."
        />
      );

      const statusIndicator = screen.getByRole('status');
      expect(statusIndicator).toHaveAttribute('aria-live', 'polite');

      // Change to error status
      rerender(
        <AccessibleStatusIndicator
          status="error"
          message="Process failed"
        />
      );

      const errorIndicator = screen.getByRole('alert');
      expect(errorIndicator).toHaveAttribute('aria-live', 'assertive');
    });

    it('should provide progress information accessibly', () => {
      render(
        <AccessibleStatusIndicator
          status="loading"
          message="Uploading file..."
          progress={75}
          showProgress={true}
        />
      );

      const progressbar = screen.getByRole('progressbar');
      expect(progressbar).toHaveAttribute('aria-valuenow', '75');
      expect(progressbar).toHaveAttribute('aria-valuemin', '0');
      expect(progressbar).toHaveAttribute('aria-valuemax', '100');
      expect(progressbar).toHaveAttribute('aria-label', 'Progress: 75%');
    });

    it('should use appropriate icons with proper labeling', () => {
      render(
        <AccessibleStatusIndicator
          status="success"
          message="Operation completed successfully"
        />
      );

      const icon = screen.getByRole('img', { name: /success status/i });
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveTextContent('✅');
    });
  });

  describe('Integration Tests', () => {
    it('should handle complete error recovery flow', async () => {
      const user = userEvent.setup();
      const TestComponent = () => {
        const [error, setError] = useState(null);
        const [showRecovery, setShowRecovery] = useState(false);
        const [status, setStatus] = useState('idle');

        const handleError = () => {
          setError({
            type: 'network',
            message: 'Connection timeout. Please check your internet connection.'
          });
        };

        const handleRetry = () => {
          setError(null);
          setShowRecovery(true);
        };

        const handleRecover = async () => {
          setStatus('loading');
          setTimeout(() => {
            setStatus('success');
            setShowRecovery(false);
          }, 1000);
        };

        return (
          <div>
            <button onClick={handleError}>Trigger Error</button>

            {error && (
              <AccessibleErrorMessage
                type="error"
                message={error.message}
                onRetry={handleRetry}
                onDismiss={() => setError(null)}
              />
            )}

            {showRecovery && (
              <AccessibleRecoveryFlow
                error={error}
                onRecover={handleRecover}
                onCancel={() => setShowRecovery(false)}
              />
            )}

            {status !== 'idle' && (
              <AccessibleStatusIndicator
                status={status}
                message={status === 'loading' ? 'Recovering...' : 'Recovery complete'}
              />
            )}
          </div>
        );
      };

      render(<TestComponent />);

      // Trigger an error
      await user.click(screen.getByRole('button', { name: /trigger error/i }));

      // Error message should appear
      expect(screen.getByRole('alert')).toHaveTextContent(/connection timeout/i);

      // Click retry to start recovery
      await user.click(screen.getByRole('button', { name: /try again/i }));

      // Recovery flow should appear
      expect(screen.getByText(/step 1/i)).toBeInTheDocument();

      // Navigate through recovery flow
      await user.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByText(/step 2/i)).toBeInTheDocument();
      });

      // Select recovery method and proceed
      await user.click(screen.getAllByRole('radio')[0]);
      await user.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByText(/step 3/i)).toBeInTheDocument();
      });

      // Complete recovery
      await user.click(screen.getByRole('button', { name: /complete recovery/i }));

      // Should show loading status
      await waitFor(() => {
        expect(screen.getByText(/recovering/i)).toBeInTheDocument();
      });

      // Should eventually show success
      await waitFor(() => {
        expect(screen.getByText(/recovery complete/i)).toBeInTheDocument();
      }, { timeout: 2000 });
    });

    it('should maintain accessibility throughout error states', async () => {
      const TestComponent = () => {
        const [hasError, setHasError] = useState(false);

        return (
          <div>
            <button onClick={() => setHasError(true)}>
              Create Error
            </button>

            {hasError && (
              <AccessibleErrorMessage
                message="Critical error occurred. Please contact support."
                type="error"
                onDismiss={() => setHasError(false)}
              />
            )}
          </div>
        );
      };

      const { container } = render(<TestComponent />);

      // Should have no violations initially
      let results = await axe(container);
      expect(results).toHaveNoViolations();

      // Trigger error state
      const user = userEvent.setup();
      await user.click(screen.getByRole('button', { name: /create error/i }));

      // Should still have no violations with error displayed
      results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});

export {
  AccessibleErrorMessage,
  AccessibleRecoveryFlow,
  AccessibleStatusIndicator
};