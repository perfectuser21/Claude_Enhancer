import React from 'react';

const PasswordStrengthIndicator = ({ strength }) => {
  if (!strength) {
    return null;
  }

  const { score, level, message, feedback } = strength;

  const getColorClass = (level) => {
    switch (level) {
      case 'very-weak':
        return 'strength-very-weak';
      case 'weak':
        return 'strength-weak';
      case 'medium':
        return 'strength-medium';
      case 'strong':
        return 'strength-strong';
      case 'very-strong':
        return 'strength-very-strong';
      default:
        return 'strength-very-weak';
    }
  };

  const getProgressWidth = () => {
    return `${score}%`;
  };

  return (
    <div className="password-strength-indicator">
      <div className="strength-bar-container">
        <div
          className={`strength-bar ${getColorClass(level)}`}
          style={{ width: getProgressWidth() }}
        />
      </div>

      <div className="strength-info">
        <span className={`strength-text ${getColorClass(level)}`}>
          {message}
        </span>
        <span className="strength-score">
          {score}/100
        </span>
      </div>

      {feedback && feedback.length > 0 && (
        <div className="strength-feedback">
          <ul>
            {feedback.map((item, index) => (
              <li key={index} className="feedback-item">
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default PasswordStrengthIndicator;