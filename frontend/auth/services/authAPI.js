import axios from 'axios';
import { tokenManager } from '../utils/tokenManager';

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const AUTH_ENDPOINTS = {
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  LOGOUT: '/auth/logout',
  REFRESH: '/auth/refresh',
  VERIFY_EMAIL: '/auth/verify-email',
  RESEND_VERIFICATION: '/auth/resend-verification',
  FORGOT_PASSWORD: '/auth/forgot-password',
  RESET_PASSWORD: '/auth/reset-password',
  CHANGE_PASSWORD: '/auth/change-password',
  VERIFY_TOKEN: '/auth/verify-token',
  MFA_SETUP: '/auth/mfa/setup',
  MFA_VERIFY: '/auth/mfa/verify',
  MFA_DISABLE: '/auth/mfa/disable',
  PROFILE: '/auth/profile',
  SESSIONS: '/auth/sessions'
};

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = tokenManager.getAccessToken();

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add request timestamp for debugging
    config.metadata = { startTime: new Date() };

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for token refresh and error handling
apiClient.interceptors.response.use(
  (response) => {
    // Add response time for monitoring
    if (response.config.metadata) {
      response.config.metadata.endTime = new Date();
      response.config.metadata.duration =
        response.config.metadata.endTime - response.config.metadata.startTime;
    }

    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Attempt to refresh the token
        const refreshToken = tokenManager.getRefreshToken();

        if (refreshToken) {
          const response = await axios.post(
            `${API_BASE_URL}${AUTH_ENDPOINTS.REFRESH}`,
            { refresh_token: refreshToken }
          );

          // Update stored tokens
          tokenManager.setTokens(response.data.tokens);

          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${response.data.tokens.access}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        tokenManager.clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle network errors
    if (!error.response) {
      error.message = 'Network error. Please check your connection.';
    }

    return Promise.reject(error);
  }
);

// Auth API service
export const authAPI = {
  /**
   * User login
   */
  async login(credentials) {
    try {
      const response = await apiClient.post(AUTH_ENDPOINTS.LOGIN, {
        email: credentials.email.toLowerCase(),
        password: credentials.password,
        remember_me: credentials.rememberMe || false
      });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Login failed');
    }
  },

  /**
   * User registration
   */
  async register(userData) {
    try {
      const response = await apiClient.post(AUTH_ENDPOINTS.REGISTER, {
        first_name: userData.firstName,
        last_name: userData.lastName,
        email: userData.email.toLowerCase(),
        password: userData.password
      });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Registration failed');
    }
  },

  /**
   * User logout
   */
  async logout() {
    try {
      const refreshToken = tokenManager.getRefreshToken();

      if (refreshToken) {
        await apiClient.post(AUTH_ENDPOINTS.LOGOUT, {
          refresh_token: refreshToken
        });
      }
    } catch (error) {
      // Don't throw error for logout - always succeed locally
      // // console.warn('Logout API call failed:', error.message);
    }
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken) {
    try {
      const response = await axios.post(
        `${API_BASE_URL}${AUTH_ENDPOINTS.REFRESH}`,
        { refresh_token: refreshToken }
      );

      return response;
    } catch (error) {
      throw this.handleError(error, 'Token refresh failed');
    }
  },

  /**
   * Verify email address
   */
  async verifyEmail(token) {
    try {
      const response = await apiClient.post(AUTH_ENDPOINTS.VERIFY_EMAIL, {
        token
      });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Email verification failed');
    }
  },

  /**
   * Resend email verification
   */
  async resendVerification(email) {
    try {
      const response = await apiClient.post(AUTH_ENDPOINTS.RESEND_VERIFICATION, {
        email: email.toLowerCase()
      });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to resend verification email');
    }
  },

  /**
   * Forgot password
   */
  async forgotPassword(email) {
    try {
      const response = await apiClient.post(AUTH_ENDPOINTS.FORGOT_PASSWORD, {
        email: email.toLowerCase()
      });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to send password reset email');
    }
  },

  /**
   * Reset password
   */
  async resetPassword(token, newPassword) {
    try {
      const response = await apiClient.post(AUTH_ENDPOINTS.RESET_PASSWORD, {
        token,
        new_password: newPassword
      });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Password reset failed');
    }
  },

  /**
   * Change password
   */
  async changePassword(passwordData) {
    try {
      const response = await apiClient.post(AUTH_ENDPOINTS.CHANGE_PASSWORD, {
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword
      });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Password change failed');
    }
  },

  /**
   * Verify current token
   */
  async verifyToken() {
    try {
      const response = await apiClient.get(AUTH_ENDPOINTS.VERIFY_TOKEN);
      return response;
    } catch (error) {
      throw this.handleError(error, 'Token verification failed');
    }
  },

  /**
   * Setup MFA
   */
  async setupMFA(method) {
    try {
      const response = await apiClient.post(AUTH_ENDPOINTS.MFA_SETUP, {
        method
      });

      return response;
    } catch (error) {
      throw this.handleError(error, 'MFA setup failed');
    }
  },

  /**
   * Verify MFA code
   */
  async verifyMFA(mfaData) {
    try {
      const response = await apiClient.post(AUTH_ENDPOINTS.MFA_VERIFY, {
        method: mfaData.method,
        code: mfaData.code,
        session: mfaData.session,
        setup_token: mfaData.setupToken
      });

      return response;
    } catch (error) {
      throw this.handleError(error, 'MFA verification failed');
    }
  },

  /**
   * Disable MFA
   */
  async disableMFA(password) {
    try {
      const response = await apiClient.post(AUTH_ENDPOINTS.MFA_DISABLE, {
        password
      });

      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to disable MFA');
    }
  },

  /**
   * Get user profile
   */
  async getProfile() {
    try {
      const response = await apiClient.get(AUTH_ENDPOINTS.PROFILE);
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch profile');
    }
  },

  /**
   * Update user profile
   */
  async updateProfile(userData) {
    try {
      const response = await apiClient.put(AUTH_ENDPOINTS.PROFILE, userData);
      return response;
    } catch (error) {
      throw this.handleError(error, 'Profile update failed');
    }
  },

  /**
   * Get active sessions
   */
  async getSessions() {
    try {
      const response = await apiClient.get(AUTH_ENDPOINTS.SESSIONS);
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to fetch sessions');
    }
  },

  /**
   * Revoke session
   */
  async revokeSession(sessionId) {
    try {
      const response = await apiClient.delete(`${AUTH_ENDPOINTS.SESSIONS}/${sessionId}`);
      return response;
    } catch (error) {
      throw this.handleError(error, 'Failed to revoke session');
    }
  },

  /**
   * Handle API errors consistently
   */
  handleError(error, defaultMessage) {
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;

      // Enhance error with more context
      error.status = status;
      error.message = data?.message || data?.detail || defaultMessage;

      // Handle specific error cases
      if (status === 422 && data?.errors) {
        // Validation errors
        error.validationErrors = data.errors;
      } else if (status === 429) {
        // Rate limiting
        error.retryAfter = data?.retry_after || 60;
      }
    } else if (error.request) {
      // Network error
      error.message = 'Network error. Please check your connection.';
    } else {
      // Other error
      error.message = defaultMessage;
    }

    return error;
  }
};

// Export configured axios instance for other modules
export { apiClient };