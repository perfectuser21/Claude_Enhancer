import React from 'react';

const LoadingSpinner = ({
  size = 'medium',
  color = 'primary',
  text = '',
  className = ''
}) => {
  const getSizeClass = () => {
    switch (size) {
      case 'small':
        return 'spinner-small';
      case 'large':
        return 'spinner-large';
      case 'extra-large':
        return 'spinner-extra-large';
      default:
        return 'spinner-medium';
    }
  };

  const getColorClass = () => {
    switch (color) {
      case 'secondary':
        return 'spinner-secondary';
      case 'success':
        return 'spinner-success';
      case 'warning':
        return 'spinner-warning';
      case 'error':
        return 'spinner-error';
      case 'white':
        return 'spinner-white';
      default:
        return 'spinner-primary';
    }
  };

  return (
    <div className={`loading-spinner ${className}`}>
      <div className={`spinner ${getSizeClass()} ${getColorClass()}`}>
        <div className="spinner-circle"></div>
      </div>
      {text && <span className="spinner-text">{text}</span>}
    </div>
  );
};

export default LoadingSpinner;