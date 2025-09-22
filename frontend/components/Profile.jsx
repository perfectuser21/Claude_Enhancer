import React from 'react';
import { useAuth } from '../auth';

const Profile = () => {
  const { user } = useAuth();

  return (
    <div className="profile-container">
      <div className="profile-header">
        <h1>User Profile</h1>
        <p>Manage your account settings and preferences</p>
      </div>

      <div className="profile-content">
        <div className="profile-card">
          <h2>Personal Information</h2>
          <div className="profile-info">
            <div className="info-item">
              <label>First Name:</label>
              <span>{user?.firstName}</span>
            </div>
            <div className="info-item">
              <label>Last Name:</label>
              <span>{user?.lastName}</span>
            </div>
            <div className="info-item">
              <label>Email:</label>
              <span>{user?.email}</span>
            </div>
            <div className="info-item">
              <label>Account Status:</label>
              <span className="status-active">{user?.status || 'Active'}</span>
            </div>
          </div>
        </div>

        <div className="profile-card">
          <h2>Security Settings</h2>
          <div className="security-info">
            <div className="security-item">
              <div className="security-label">
                <span>Email Verification</span>
                <span className={user?.emailVerified ? 'verified' : 'unverified'}>
                  {user?.emailVerified ? '✅ Verified' : '❌ Unverified'}
                </span>
              </div>
            </div>
            <div className="security-item">
              <div className="security-label">
                <span>Two-Factor Authentication</span>
                <span className={user?.mfaEnabled ? 'enabled' : 'disabled'}>
                  {user?.mfaEnabled ? '✅ Enabled' : '❌ Disabled'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .profile-container {
          min-height: 100vh;
          background: #f8fafc;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
          padding: 2rem;
        }

        .profile-header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .profile-header h1 {
          color: #1e293b;
          font-size: 2rem;
          margin: 0 0 0.5rem 0;
          font-weight: 600;
        }

        .profile-header p {
          color: #64748b;
          margin: 0;
        }

        .profile-content {
          max-width: 800px;
          margin: 0 auto;
          display: grid;
          gap: 2rem;
        }

        .profile-card {
          background: white;
          border-radius: 12px;
          padding: 2rem;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .profile-card h2 {
          color: #1e293b;
          font-size: 1.25rem;
          margin: 0 0 1.5rem 0;
          font-weight: 600;
        }

        .profile-info {
          display: grid;
          gap: 1rem;
        }

        .info-item {
          display: grid;
          grid-template-columns: 150px 1fr;
          gap: 1rem;
          align-items: center;
        }

        .info-item label {
          color: #64748b;
          font-weight: 500;
        }

        .info-item span {
          color: #1e293b;
          font-weight: 500;
        }

        .status-active {
          color: #059669 !important;
        }

        .security-info {
          display: grid;
          gap: 1rem;
        }

        .security-item {
          padding: 1rem;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
        }

        .security-label {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .security-label span:first-child {
          color: #1e293b;
          font-weight: 500;
        }

        .verified {
          color: #059669;
        }

        .unverified {
          color: #ef4444;
        }

        .enabled {
          color: #059669;
        }

        .disabled {
          color: #ef4444;
        }

        @media (max-width: 640px) {
          .profile-container {
            padding: 1rem;
          }

          .info-item {
            grid-template-columns: 1fr;
            gap: 0.5rem;
          }

          .security-label {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
          }
        }
      `}</style>
    </div>
  );
};

export default Profile;