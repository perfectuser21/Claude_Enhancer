import React, { useContext, useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import LoadingSpinner from '../../common/components/LoadingSpinner';
import { tokenManager } from '../utils/tokenManager';

const ProtectedRoute = ({
  children,
  requiredPermissions = [],
  requiredRoles = [],
  requireEmailVerification = true,
  requireMFA = false,
  fallbackPath = '/login'
}) => {
  const {
    isAuthenticated,
    isLoading,
    user,
    mfaRequired
  } = useContext(AuthContext);

  const [isChecking, setIsChecking] = useState(true);
  const location = useLocation();

  useEffect(() => {
    // Check authentication status
    const checkAuth = async () => {
      try {
        // If we have tokens but no user, wait for auth context to initialize
        const tokens = tokenManager.getTokens();
        if (tokens && !user && !isLoading) {
          // Auth context is still initializing
          return;
        }

        setIsChecking(false);
      } catch (error) {
        console.error('Auth check failed:', error);
        setIsChecking(false);
      }
    };

    checkAuth();
  }, [user, isLoading]);

  // Show loading while checking authentication
  if (isLoading || isChecking) {
    return (
      <div className="route-loading">
        <LoadingSpinner size="large" />
        <p>Verifying authentication...</p>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <Navigate
        to={fallbackPath}
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  // Handle MFA requirement
  if (mfaRequired) {
    return (
      <Navigate
        to="/auth/mfa"
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  // Check email verification requirement
  if (requireEmailVerification && user && !user.emailVerified) {
    return (
      <Navigate
        to="/auth/verify-email"
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  // Check MFA requirement
  if (requireMFA && user && !user.mfaEnabled) {
    return (
      <Navigate
        to="/auth/setup-mfa"
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  // Check role requirements
  if (requiredRoles.length > 0 && user) {
    const userRoles = user.roles || [];
    const hasRequiredRole = requiredRoles.some(role =>
      userRoles.includes(role)
    );

    if (!hasRequiredRole) {
      return (
        <Navigate
          to="/unauthorized"
          state={{
            from: location.pathname,
            reason: 'insufficient_role',
            required: requiredRoles
          }}
          replace
        />
      );
    }
  }

  // Check permission requirements
  if (requiredPermissions.length > 0 && user) {
    const userPermissions = user.permissions || [];
    const hasRequiredPermissions = requiredPermissions.every(permission =>
      userPermissions.includes(permission)
    );

    if (!hasRequiredPermissions) {
      return (
        <Navigate
          to="/unauthorized"
          state={{
            from: location.pathname,
            reason: 'insufficient_permissions',
            required: requiredPermissions
          }}
          replace
        />
      );
    }
  }

  // All checks passed, render the protected component
  return children;
};

// Higher-order component for protecting routes
export const withAuthProtection = (Component, options = {}) => {
  return function ProtectedComponent(props) {
    return (
      <ProtectedRoute {...options}>
        <Component {...props} />
      </ProtectedRoute>
    );
  };
};

// Hook for checking permissions in components
export const usePermissions = () => {
  const { user } = useContext(AuthContext);

  const hasPermission = (permission) => {
    return user?.permissions?.includes(permission) || false;
  };

  const hasRole = (role) => {
    return user?.roles?.includes(role) || false;
  };

  const hasAnyPermission = (permissions) => {
    return permissions.some(permission => hasPermission(permission));
  };

  const hasAllPermissions = (permissions) => {
    return permissions.every(permission => hasPermission(permission));
  };

  const hasAnyRole = (roles) => {
    return roles.some(role => hasRole(role));
  };

  return {
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    hasAnyRole,
    permissions: user?.permissions || [],
    roles: user?.roles || []
  };
};

// Component for conditionally rendering content based on permissions
export const PermissionGate = ({
  permissions = [],
  roles = [],
  requireAll = false,
  fallback = null,
  children
}) => {
  const { hasPermission, hasRole } = usePermissions();

  let hasAccess = true;

  if (permissions.length > 0) {
    if (requireAll) {
      hasAccess = hasAccess && permissions.every(p => hasPermission(p));
    } else {
      hasAccess = hasAccess && permissions.some(p => hasPermission(p));
    }
  }

  if (roles.length > 0) {
    if (requireAll) {
      hasAccess = hasAccess && roles.every(r => hasRole(r));
    } else {
      hasAccess = hasAccess && roles.some(r => hasRole(r));
    }
  }

  return hasAccess ? children : fallback;
};

export default ProtectedRoute;