// Main entry point for authentication module
export { AuthProvider, useAuth } from './context/AuthContext';
export { default as LoginForm } from './components/LoginForm';
export { default as RegisterForm } from './components/RegisterForm';
export { default as MFASetup } from './components/MFASetup';
export { default as ForgotPassword } from './components/ForgotPassword';
export { default as AuthLayout } from './components/AuthLayout';
export { default as ProtectedRoute, withAuthProtection, usePermissions, PermissionGate } from './components/ProtectedRoute';
export { NotificationProvider, useNotification, useGlobalNotification } from './hooks/useNotification';
export { tokenManager } from './utils/tokenManager';
export { authAPI } from './services/authAPI';
export * from './utils/validation';

// Import styles
import './styles/auth.css';