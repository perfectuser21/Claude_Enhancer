import React from 'react';
import { useAuth } from '../auth';

const AdminPanel = () => {
  const { user } = useAuth();

  return (
    <div className="admin-container">
      <div className="admin-header">
        <h1>Admin Panel</h1>
        <p>Administrative tools and system management</p>
      </div>

      <div className="admin-content">
        <div className="admin-card">
          <h2>Welcome, Administrator</h2>
          <p>You have access to this panel because you have admin privileges.</p>
          <div className="admin-info">
            <p><strong>Your Role:</strong> {user?.roles?.join(', ')}</p>
            <p><strong>Permissions:</strong> {user?.permissions?.length || 0} granted</p>
          </div>
        </div>

        <div className="admin-card">
          <h2>System Statistics</h2>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-value">1,234</div>
              <div className="stat-label">Total Users</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">456</div>
              <div className="stat-label">Active Sessions</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">89%</div>
              <div className="stat-label">Uptime</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">12</div>
              <div className="stat-label">Pending Reviews</div>
            </div>
          </div>
        </div>

        <div className="admin-card">
          <h2>Quick Actions</h2>
          <div className="actions-grid">
            <button className="action-btn">👥 Manage Users</button>
            <button className="action-btn">🔐 Security Logs</button>
            <button className="action-btn">📊 Analytics</button>
            <button className="action-btn">⚙️ System Settings</button>
            <button className="action-btn">📝 Audit Trail</button>
            <button className="action-btn">🔔 Notifications</button>
          </div>
        </div>
      </div>

      <style jsx>{`
        .admin-container {
          min-height: 100vh;
          background: #f8fafc;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
          padding: 2rem;
        }

        .admin-header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .admin-header h1 {
          color: #1e293b;
          font-size: 2rem;
          margin: 0 0 0.5rem 0;
          font-weight: 600;
        }

        .admin-header p {
          color: #64748b;
          margin: 0;
        }

        .admin-content {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          gap: 2rem;
        }

        .admin-card {
          background: white;
          border-radius: 12px;
          padding: 2rem;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .admin-card h2 {
          color: #1e293b;
          font-size: 1.25rem;
          margin: 0 0 1rem 0;
          font-weight: 600;
        }

        .admin-info {
          margin-top: 1rem;
          padding: 1rem;
          background: #f1f5f9;
          border-radius: 8px;
        }

        .admin-info p {
          margin: 0.5rem 0;
          color: #475569;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
        }

        .stat-item {
          text-align: center;
          padding: 1.5rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 8px;
          color: white;
        }

        .stat-value {
          font-size: 2rem;
          font-weight: 700;
          margin-bottom: 0.5rem;
        }

        .stat-label {
          font-size: 0.9rem;
          opacity: 0.9;
        }

        .actions-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
        }

        .action-btn {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          padding: 1rem;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          color: #374151;
          transition: all 0.2s ease;
          text-align: left;
        }

        .action-btn:hover {
          background: #f1f5f9;
          border-color: #d1d5db;
          transform: translateY(-1px);
        }

        @media (max-width: 768px) {
          .admin-container {
            padding: 1rem;
          }

          .stats-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          .actions-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default AdminPanel;