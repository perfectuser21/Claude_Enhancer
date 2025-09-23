import React from 'react';
import { useAuth, usePermissions } from '../auth';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const { hasPermission, hasRole } = usePermissions();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Welcome to Claude Enhancer</h1>
          <div className="user-info">
            <span>Hello, {user?.firstName} {user?.lastName}</span>
            <button onClick={handleLogout} className="logout-btn">
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-grid">
          <div className="dashboard-card">
            <h2>Profile Information</h2>
            <div className="user-details">
              <p><strong>Name:</strong> {user?.firstName} {user?.lastName}</p>
              <p><strong>Email:</strong> {user?.email}</p>
              <p><strong>Email Verified:</strong> {user?.emailVerified ? '✅ Yes' : '❌ No'}</p>
              <p><strong>MFA Enabled:</strong> {user?.mfaEnabled ? '✅ Yes' : '❌ No'}</p>
              <p><strong>Account Status:</strong> {user?.status || 'Active'}</p>
            </div>
          </div>

          <div className="dashboard-card">
            <h2>Permissions & Roles</h2>
            <div className="permissions-info">
              <div className="roles">
                <h3>Your Roles:</h3>
                <ul>
                  {user?.roles?.map(role => (
                    <li key={role} className="role-item">{role}</li>
                  )) || <li>No roles assigned</li>}
                </ul>
              </div>

              <div className="permissions">
                <h3>Key Permissions:</h3>
                <ul>
                  <li className={hasPermission('user:read') ? 'has-permission' : 'no-permission'}>
                    Read Users: {hasPermission('user:read') ? '✅' : '❌'}
                  </li>
                  <li className={hasPermission('user:write') ? 'has-permission' : 'no-permission'}>
                    Write Users: {hasPermission('user:write') ? '✅' : '❌'}
                  </li>
                  <li className={hasPermission('admin:access') ? 'has-permission' : 'no-permission'}>
                    Admin Access: {hasPermission('admin:access') ? '✅' : '❌'}
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div className="dashboard-card">
            <h2>Quick Actions</h2>
            <div className="quick-actions">
              <button className="action-btn">
                📝 Edit Profile
              </button>

              {!user?.mfaEnabled && (
                <button className="action-btn security-btn">
                  🔐 Setup MFA
                </button>
              )}

              <button className="action-btn">
                🔑 Change Password
              </button>

              {hasRole('admin') && (
                <button className="action-btn admin-btn">
                  👥 Admin Panel
                </button>
              )}
            </div>
          </div>

          <div className="dashboard-card">
            <h2>Security Status</h2>
            <div className="security-status">
              <div className="security-item">
                <span className="security-label">Password Strength:</span>
                <span className="security-value strong">Strong</span>
              </div>

              <div className="security-item">
                <span className="security-label">Last Login:</span>
                <span className="security-value">{user?.lastLogin || 'Just now'}</span>
              </div>

              <div className="security-item">
                <span className="security-label">Login Sessions:</span>
                <span className="security-value">1 active</span>
              </div>

              <div className="security-item">
                <span className="security-label">Account Security:</span>
                <span className={`security-value ${user?.mfaEnabled ? 'secure' : 'warning'}`}>
                  {user?.mfaEnabled ? 'Excellent' : 'Good'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </main>

      <style jsx>{`
        .dashboard {
          min-height: 100vh;
          background: #f8fafc;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }

        .dashboard-header {
          background: white;
          border-bottom: 1px solid #e2e8f0;
          padding: 1rem 0;
        }

        .header-content {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .header-content h1 {
          margin: 0;
          color: #1e293b;
          font-size: 1.5rem;
          font-weight: 600;
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .user-info span {
          color: #64748b;
          font-weight: 500;
        }

        .logout-btn {
          background: #ef4444;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
        }

        .logout-btn:hover {
          background: #dc2626;
        }

        .dashboard-main {
          max-width: 1200px;
          margin: 0 auto;
          padding: 2rem;
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 2rem;
        }

        .dashboard-card {
          background: white;
          border-radius: 8px;
          padding: 1.5rem;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .dashboard-card h2 {
          margin: 0 0 1rem 0;
          color: #1e293b;
          font-size: 1.25rem;
          font-weight: 600;
        }

        .user-details p {
          margin: 0.5rem 0;
          color: #475569;
        }

        .permissions-info {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .roles h3, .permissions h3 {
          margin: 0 0 0.5rem 0;
          color: #374151;
          font-size: 1rem;
        }

        .roles ul, .permissions ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .role-item {
          background: #f1f5f9;
          color: #475569;
          padding: 0.25rem 0.75rem;
          border-radius: 4px;
          margin-bottom: 0.5rem;
          font-size: 0.9rem;
        }

        .has-permission {
          color: #059669;
        }

        .no-permission {
          color: #64748b;
        }

        .quick-actions {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .action-btn {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          padding: 0.75rem;
          border-radius: 6px;
          cursor: pointer;
          text-align: left;
          font-weight: 500;
          color: #374151;
        }

        .action-btn:hover {
          background: #f1f5f9;
        }

        .security-btn {
          background: #fef3c7;
          border-color: #fbbf24;
          color: #92400e;
        }

        .admin-btn {
          background: #ddd6fe;
          border-color: #8b5cf6;
          color: #5b21b6;
        }

        .security-status {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .security-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .security-label {
          color: #64748b;
          font-weight: 500;
        }

        .security-value {
          font-weight: 600;
        }

        .security-value.strong {
          color: #059669;
        }

        .security-value.secure {
          color: #059669;
        }

        .security-value.warning {
          color: #d97706;
        }

        @media (max-width: 768px) {
          .header-content {
            padding: 0 1rem;
          }

          .dashboard-main {
            padding: 1rem;
          }

          .dashboard-grid {
            grid-template-columns: 1fr;
          }

          .user-info {
            flex-direction: column;
            align-items: flex-end;
            gap: 0.5rem;
          }
        }
      `}</style>
    </div>
  );
};

export default Dashboard;