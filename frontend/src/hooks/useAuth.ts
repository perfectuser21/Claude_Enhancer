import { useEffect } from 'react';
import { useAuthStore } from '../store';
import { uiUtils } from '../store/uiStore';

export const useAuth = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    refreshToken
  } = useAuthStore();

  // Check for token refresh on mount
  useEffect(() => {
    const token = useAuthStore.getState().token;
    if (token && !user) {
      refreshToken().catch(() => {
        // Token refresh failed, user will need to login again
        logout();
      });
    }
  }, []);

  // Show auth-related notifications
  useEffect(() => {
    if (error) {
      uiUtils.showError('Authentication Error', error);
    }
  }, [error]);

  const handleLogin = async (credentials: { email: string; password: string; rememberMe?: boolean }) => {
    try {
      await login(credentials);
      uiUtils.showSuccess('Welcome back!', `Successfully signed in as ${credentials.email}`);
    } catch (error: any) {
      uiUtils.showError('Login Failed', error.message);
      throw error;
    }
  };

  const handleRegister = async (data: {
    email: string;
    username: string;
    password: string;
    confirmPassword: string;
    firstName: string;
    lastName: string;
  }) => {
    try {
      await register(data);
      uiUtils.showSuccess(
        'Account Created!',
        `Welcome ${data.firstName}! Your account has been created successfully.`
      );
    } catch (error: any) {
      uiUtils.showError('Registration Failed', error.message);
      throw error;
    }
  };

  const handleLogout = () => {
    logout();
    uiUtils.showInfo('Signed Out', 'You have been successfully signed out.');
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    refreshToken,
  };
};