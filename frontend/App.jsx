import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import {
  AuthProvider,
  AuthLayout,
  ProtectedRoute,
  NotificationProvider
} from './auth';

// Example components (these would be your actual app components)
import Dashboard from './components/Dashboard';
import Profile from './components/Profile';
import AdminPanel from './components/AdminPanel';
import Unauthorized from './components/Unauthorized';

function App() {
  return (
    <Router>
      <NotificationProvider>
        <AuthProvider>
          <div className="app">
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<AuthLayout initialView="login" />} />
              <Route path="/register" element={<AuthLayout initialView="register" />} />
              <Route path="/forgot-password" element={<AuthLayout initialView="forgot-password" />} />

              {/* Protected routes */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />

              <Route
                path="/profile"
                element={
                  <ProtectedRoute requireEmailVerification={true}>
                    <Profile />
                  </ProtectedRoute>
                }
              />

              {/* Admin routes */}
              <Route
                path="/admin"
                element={
                  <ProtectedRoute
                    requiredRoles={['admin']}
                    fallbackPath="/unauthorized"
                  >
                    <AdminPanel />
                  </ProtectedRoute>
                }
              />

              {/* MFA setup route */}
              <Route
                path="/setup-mfa"
                element={
                  <ProtectedRoute>
                    <AuthLayout initialView="mfa-setup" />
                  </ProtectedRoute>
                }
              />

              {/* Error routes */}
              <Route path="/unauthorized" element={<Unauthorized />} />

              {/* Default redirects */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/auth/*" element={<Navigate to="/login" replace />} />

              {/* 404 fallback */}
              <Route path="*" element={<div>Page not found</div>} />
            </Routes>
          </div>
        </AuthProvider>
      </NotificationProvider>
    </Router>
  );
}

export default App;