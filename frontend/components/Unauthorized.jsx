import React from 'react';
import { useLocation, Link } from 'react-router-dom';

const Unauthorized = () => {
  const location = useLocation();
  const { reason, required } = location.state || {};

  const getErrorMessage = () => {
    switch (reason) {
      case 'insufficient_role':
        return {
          title: 'Insufficient Role',
          message: `You need one of the following roles to access this page: ${required?.join(', ')}`,
          icon: '👥'
        };
      case 'insufficient_permissions':
        return {
          title: 'Insufficient Permissions',
          message: `You need the following permissions to access this page: ${required?.join(', ')}`,
          icon: '🔐'
        };
      default:
        return {
          title: 'Access Denied',
          message: 'You do not have permission to access this page.',
          icon: '🚫'
        };
    }
  };

  const error = getErrorMessage();

  return (
    <div className="unauthorized-container">
      <div className="unauthorized-content">
        <div className="error-icon">{error.icon}</div>
        <h1>{error.title}</h1>
        <p>{error.message}</p>

        <div className="error-actions">
          <Link to="/dashboard" className="primary-btn">
            Go to Dashboard
          </Link>
          <Link to="/profile" className="secondary-btn">
            View Profile
          </Link>
        </div>

        <div className="help-section">
          <h3>Need access?</h3>
          <p>Contact your administrator to request the necessary permissions.</p>
        </div>
      </div>

      <style jsx>{`
        .unauthorized-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f8fafc;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
          padding: 2rem;
        }

        .unauthorized-content {
          text-align: center;
          background: white;
          border-radius: 12px;
          padding: 3rem;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          max-width: 500px;
          width: 100%;
        }

        .error-icon {
          font-size: 4rem;
          margin-bottom: 1rem;
        }

        h1 {
          color: #1e293b;
          font-size: 2rem;
          margin: 0 0 1rem 0;
          font-weight: 600;
        }

        p {
          color: #64748b;
          font-size: 1.1rem;
          margin: 0 0 2rem 0;
          line-height: 1.6;
        }

        .error-actions {
          display: flex;
          gap: 1rem;
          justify-content: center;
          margin-bottom: 2rem;
        }

        .primary-btn {
          background: #4f46e5;
          color: white;
          text-decoration: none;
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          font-weight: 600;
          transition: all 0.2s ease;
        }

        .primary-btn:hover {
          background: #4338ca;
        }

        .secondary-btn {
          background: white;
          color: #4f46e5;
          text-decoration: none;
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          border: 2px solid #4f46e5;
          font-weight: 600;
          transition: all 0.2s ease;
        }

        .secondary-btn:hover {
          background: #4f46e5;
          color: white;
        }

        .help-section {
          border-top: 1px solid #e2e8f0;
          padding-top: 2rem;
        }

        .help-section h3 {
          color: #1e293b;
          font-size: 1.1rem;
          margin: 0 0 0.5rem 0;
        }

        .help-section p {
          color: #64748b;
          font-size: 0.9rem;
          margin: 0;
        }

        @media (max-width: 640px) {
          .unauthorized-content {
            padding: 2rem;
          }

          .error-actions {
            flex-direction: column;
          }

          h1 {
            font-size: 1.5rem;
          }
        }
      `}</style>
    </div>
  );
};

export default Unauthorized;