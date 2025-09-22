import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { authAPI } from '../services/authAPI';
import { tokenManager } from '../utils/tokenManager';

// Auth state reducer
const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_START':
    case 'REGISTER_START':
    case 'REFRESH_START':
      return {
        ...state,
        isLoading: true,
        error: null
      };

    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isLoading: false,
        isAuthenticated: true,
        user: action.payload.user,
        tokens: action.payload.tokens,
        error: null
      };

    case 'REGISTER_SUCCESS':
      return {
        ...state,
        isLoading: false,
        user: action.payload.user,
        pendingVerification: true,
        error: null
      };

    case 'REFRESH_SUCCESS':
      return {
        ...state,
        isLoading: false,
        tokens: action.payload.tokens,
        error: null
      };

    case 'LOGOUT':
      return {
        ...state,
        isLoading: false,
        isAuthenticated: false,
        user: null,
        tokens: null,
        pendingVerification: false,
        mfaRequired: false,
        error: null
      };

    case 'MFA_REQUIRED':
      return {
        ...state,
        isLoading: false,
        mfaRequired: true,
        mfaSession: action.payload.session,
        error: null
      };

    case 'MFA_SUCCESS':
      return {
        ...state,
        isLoading: false,
        isAuthenticated: true,
        mfaRequired: false,
        mfaSession: null,
        user: action.payload.user,
        tokens: action.payload.tokens,
        error: null
      };

    case 'UPDATE_USER':
      return {
        ...state,
        user: { ...state.user, ...action.payload }
      };

    case 'AUTH_ERROR':
      return {
        ...state,
        isLoading: false,
        error: action.payload,
        mfaRequired: false,
        mfaSession: null
      };

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null
      };

    default:
      return state;
  }
};

// Initial state
const initialState = {
  isAuthenticated: false,
  isLoading: false,
  user: null,
  tokens: null,
  error: null,
  pendingVerification: false,
  mfaRequired: false,
  mfaSession: null
};

// Create context
export const AuthContext = createContext();

// Auth provider component
export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedTokens = tokenManager.getTokens();

        if (storedTokens?.access) {
          // Verify token and get user info
          const response = await authAPI.verifyToken();

          dispatch({
            type: 'LOGIN_SUCCESS',
            payload: {
              user: response.data.user,
              tokens: storedTokens
            }
          });
        }
      } catch (error) {
        // Token is invalid, clear it
        tokenManager.clearTokens();
        // console.log('Token verification failed during initialization');
      }
    };

    initializeAuth();
  }, []);

  // Login function
  const login = async (credentials) => {
    dispatch({ type: 'LOGIN_START' });

    try {
      const response = await authAPI.login(credentials);

      if (response.data.mfaRequired) {
        dispatch({
          type: 'MFA_REQUIRED',
          payload: { session: response.data.mfaSession }
        });
        return { mfaRequired: true, session: response.data.mfaSession };
      }

      // Store tokens
      tokenManager.setTokens(response.data.tokens);

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: {
          user: response.data.user,
          tokens: response.data.tokens
        }
      });

      return { success: true };
    } catch (error) {
      dispatch({
        type: 'AUTH_ERROR',
        payload: error.response?.data?.message || 'Login failed'
      });
      throw error;
    }
  };

  // Register function
  const register = async (userData) => {
    dispatch({ type: 'REGISTER_START' });

    try {
      const response = await authAPI.register(userData);

      dispatch({
        type: 'REGISTER_SUCCESS',
        payload: { user: response.data.user }
      });

      return { success: true };
    } catch (error) {
      dispatch({
        type: 'AUTH_ERROR',
        payload: error.response?.data?.message || 'Registration failed'
      });
      throw error;
    }
  };

  // MFA verification
  const verifyMFA = async (mfaData) => {
    dispatch({ type: 'LOGIN_START' });

    try {
      const response = await authAPI.verifyMFA({
        ...mfaData,
        session: state.mfaSession
      });

      // Store tokens
      tokenManager.setTokens(response.data.tokens);

      dispatch({
        type: 'MFA_SUCCESS',
        payload: {
          user: response.data.user,
          tokens: response.data.tokens
        }
      });

      return { success: true };
    } catch (error) {
      dispatch({
        type: 'AUTH_ERROR',
        payload: error.response?.data?.message || 'MFA verification failed'
      });
      throw error;
    }
  };

  // Setup MFA
  const setupMFA = async (method) => {
    try {
      const response = await authAPI.setupMFA(method);
      return response;
    } catch (error) {
      dispatch({
        type: 'AUTH_ERROR',
        payload: error.response?.data?.message || 'MFA setup failed'
      });
      throw error;
    }
  };

  // Logout function
  const logout = async () => {
    try {
      // Call logout API to invalidate tokens on server
      await authAPI.logout();
    } catch (error) {
      // console.log('Logout API call failed, proceeding with local logout');
    } finally {
      // Clear local tokens regardless of API call result
      tokenManager.clearTokens();
      dispatch({ type: 'LOGOUT' });
    }
  };

  // Refresh token function
  const refreshToken = async () => {
    try {
      dispatch({ type: 'REFRESH_START' });

      const refreshToken = tokenManager.getRefreshToken();
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await authAPI.refreshToken(refreshToken);

      // Update stored tokens
      tokenManager.setTokens(response.data.tokens);

      dispatch({
        type: 'REFRESH_SUCCESS',
        payload: { tokens: response.data.tokens }
      });

      return response.data.tokens.access;
    } catch (error) {
      // Refresh failed, logout user
      logout();
      throw error;
    }
  };

  // Update user profile
  const updateUser = async (userData) => {
    try {
      const response = await authAPI.updateProfile(userData);

      dispatch({
        type: 'UPDATE_USER',
        payload: response.data.user
      });

      return { success: true };
    } catch (error) {
      dispatch({
        type: 'AUTH_ERROR',
        payload: error.response?.data?.message || 'Profile update failed'
      });
      throw error;
    }
  };

  // Change password
  const changePassword = async (passwordData) => {
    try {
      await authAPI.changePassword(passwordData);
      return { success: true };
    } catch (error) {
      dispatch({
        type: 'AUTH_ERROR',
        payload: error.response?.data?.message || 'Password change failed'
      });
      throw error;
    }
  };

  // Clear error
  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  // Context value
  const value = {
    // State
    ...state,

    // Actions
    login,
    register,
    logout,
    verifyMFA,
    setupMFA,
    refreshToken,
    updateUser,
    changePassword,
    clearError
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
};