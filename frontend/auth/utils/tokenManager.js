/**
 * Token Manager - Handles secure storage and management of authentication tokens
 * Supports both localStorage and httpOnly cookies based on configuration
 */

class TokenManager {
  constructor() {
    this.ACCESS_TOKEN_KEY = 'auth_access_token';
    this.REFRESH_TOKEN_KEY = 'auth_refresh_token';
    this.TOKEN_EXPIRY_KEY = 'auth_token_expiry';
    this.STORAGE_TYPE_KEY = 'auth_storage_type';

    // Default to localStorage, can be overridden
    this.storageType = this.getStorageType() || 'localStorage';
  }

  /**
   * Get current storage type
   */
  getStorageType() {
    return localStorage.getItem(this.STORAGE_TYPE_KEY);
  }

  /**
   * Set storage type preference
   */
  setStorageType(type) {
    localStorage.setItem(this.STORAGE_TYPE_KEY, type);
    this.storageType = type;
  }

  /**
   * Store authentication tokens
   */
  setTokens(tokens, rememberMe = false) {
    const { access, refresh, expiresIn } = tokens;

    if (!access) {
      throw new Error('Access token is required');
    }

    // Calculate expiry time
    const expiryTime = Date.now() + (expiresIn * 1000);

    if (this.storageType === 'cookie' || rememberMe) {
      // Use secure cookies for persistent storage
      this.setCookie(this.ACCESS_TOKEN_KEY, access, expiresIn);
      if (refresh) {
        this.setCookie(this.REFRESH_TOKEN_KEY, refresh, 30 * 24 * 60 * 60); // 30 days
      }
      this.setCookie(this.TOKEN_EXPIRY_KEY, expiryTime.toString(), expiresIn);
    } else {
      // Use sessionStorage for temporary storage (tab-specific)
      sessionStorage.setItem(this.ACCESS_TOKEN_KEY, access);
      if (refresh) {
        sessionStorage.setItem(this.REFRESH_TOKEN_KEY, refresh);
      }
      sessionStorage.setItem(this.TOKEN_EXPIRY_KEY, expiryTime.toString());
    }
  }

  /**
   * Get access token
   */
  getAccessToken() {
    if (this.storageType === 'cookie') {
      return this.getCookie(this.ACCESS_TOKEN_KEY);
    }

    return sessionStorage.getItem(this.ACCESS_TOKEN_KEY) ||
           localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  /**
   * Get refresh token
   */
  getRefreshToken() {
    if (this.storageType === 'cookie') {
      return this.getCookie(this.REFRESH_TOKEN_KEY);
    }

    return sessionStorage.getItem(this.REFRESH_TOKEN_KEY) ||
           localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Get all tokens
   */
  getTokens() {
    const access = this.getAccessToken();
    const refresh = this.getRefreshToken();

    if (!access) {
      return null;
    }

    return { access, refresh };
  }

  /**
   * Check if token is expired
   */
  isTokenExpired() {
    const expiryTime = this.getTokenExpiry();

    if (!expiryTime) {
      return true;
    }

    // Add 1 minute buffer to account for clock skew
    return Date.now() >= (expiryTime - 60000);
  }

  /**
   * Get token expiry time
   */
  getTokenExpiry() {
    let expiryString;

    if (this.storageType === 'cookie') {
      expiryString = this.getCookie(this.TOKEN_EXPIRY_KEY);
    } else {
      expiryString = sessionStorage.getItem(this.TOKEN_EXPIRY_KEY) ||
                    localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    }

    return expiryString ? parseInt(expiryString) : null;
  }

  /**
   * Clear all stored tokens
   */
  clearTokens() {
    // Clear from all possible storage locations
    sessionStorage.removeItem(this.ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(this.TOKEN_EXPIRY_KEY);

    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY);

    // Clear cookies
    this.deleteCookie(this.ACCESS_TOKEN_KEY);
    this.deleteCookie(this.REFRESH_TOKEN_KEY);
    this.deleteCookie(this.TOKEN_EXPIRY_KEY);
  }

  /**
   * Set secure cookie
   */
  setCookie(name, value, maxAge) {
    const secure = window.location.protocol === 'https:';
    const sameSite = 'Strict';

    let cookieString = `${name}=${encodeURIComponent(value)}; `;
    cookieString += `Max-Age=${maxAge}; `;
    cookieString += `Path=/; `;
    cookieString += `SameSite=${sameSite}; `;

    if (secure) {
      cookieString += 'Secure; ';
    }

    // HttpOnly flag should be set by the server for maximum security
    // We can't set it from JavaScript, but we can implement server-side cookie setting

    document.cookie = cookieString;
  }

  /**
   * Get cookie value
   */
  getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);

    if (parts.length === 2) {
      return decodeURIComponent(parts.pop().split(';').shift());
    }

    return null;
  }

  /**
   * Delete cookie
   */
  deleteCookie(name) {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
  }

  /**
   * Get token payload (decode JWT without verification)
   */
  getTokenPayload(token = null) {
    const accessToken = token || this.getAccessToken();

    if (!accessToken) {
      return null;
    }

    try {
      // JWT tokens have 3 parts separated by dots
      const parts = accessToken.split('.');
      if (parts.length !== 3) {
        return null;
      }

      // Decode the payload (second part)
      const payload = parts[1];

      // Add padding if needed for base64 decoding
      const paddedPayload = payload + '='.repeat((4 - payload.length % 4) % 4);

      // Decode from base64url to JSON
      const decoded = atob(paddedPayload.replace(/-/g, '+').replace(/_/g, '/'));

      return JSON.parse(decoded);
    } catch (error) {
      console.error('Failed to decode token payload:', error);
      return null;
    }
  }

  /**
   * Get user information from token
   */
  getUserFromToken() {
    const payload = this.getTokenPayload();

    if (!payload) {
      return null;
    }

    return {
      id: payload.sub || payload.user_id,
      email: payload.email,
      name: payload.name,
      roles: payload.roles || [],
      permissions: payload.permissions || []
    };
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(permission) {
    const user = this.getUserFromToken();
    return user?.permissions?.includes(permission) || false;
  }

  /**
   * Check if user has specific role
   */
  hasRole(role) {
    const user = this.getUserFromToken();
    return user?.roles?.includes(role) || false;
  }

  /**
   * Get time until token expires (in seconds)
   */
  getTimeToExpiry() {
    const expiryTime = this.getTokenExpiry();

    if (!expiryTime) {
      return 0;
    }

    const timeLeft = Math.max(0, expiryTime - Date.now());
    return Math.floor(timeLeft / 1000);
  }

  /**
   * Auto-refresh token before expiry
   */
  scheduleTokenRefresh(refreshCallback, bufferMinutes = 5) {
    const timeToExpiry = this.getTimeToExpiry();
    const bufferSeconds = bufferMinutes * 60;

    if (timeToExpiry > bufferSeconds) {
      const refreshTime = (timeToExpiry - bufferSeconds) * 1000;

      setTimeout(async () => {
        try {
          await refreshCallback();
          // Schedule next refresh
          this.scheduleTokenRefresh(refreshCallback, bufferMinutes);
        } catch (error) {
          console.error('Auto token refresh failed:', error);
        }
      }, refreshTime);
    }
  }
}

// Create and export singleton instance
export const tokenManager = new TokenManager();

// Also export the class for testing
export { TokenManager };