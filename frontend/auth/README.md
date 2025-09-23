# Frontend Authentication System

A comprehensive React-based authentication system with modern security features.

## Features

### 🔐 Core Authentication
- **User Registration** - Complete signup flow with validation
- **User Login** - Secure login with remember me option
- **Password Reset** - Forgot password with email verification
- **Multi-Factor Authentication (MFA)** - TOTP, SMS, and email support
- **Token Management** - Automatic refresh and secure storage

### 🛡️ Security Features
- **JWT Token Management** - Automatic refresh and secure storage
- **Route Protection** - Role and permission-based access control
- **Password Strength Validation** - Real-time strength indicator
- **Rate Limiting Protection** - Built-in error handling for rate limits
- **Secure Storage** - Support for localStorage, sessionStorage, and cookies

### 🎨 User Experience
- **Responsive Design** - Mobile-first responsive layout
- **Real-time Validation** - Instant feedback on form inputs
- **Loading States** - Smooth loading indicators
- **Notifications** - Toast notifications for user feedback
- **Accessibility** - WCAG compliant components

## Quick Start

### 1. Installation

```bash
# Install dependencies
npm install react react-dom axios

# Import the authentication system
import { AuthProvider, AuthLayout } from './frontend/auth';
```

### 2. Basic Setup

```jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider, AuthLayout, ProtectedRoute } from './frontend/auth';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/auth/*" element={<AuthLayout />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
```

### 3. Environment Configuration

Create a `.env` file:

```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_APP_NAME=Claude Enhancer
```

## Components

### AuthProvider
Context provider that manages authentication state.

```jsx
import { AuthProvider, useAuth } from './frontend/auth';

function MyComponent() {
  const { user, login, logout, isAuthenticated } = useAuth();

  return (
    <div>
      {isAuthenticated ? (
        <div>Welcome, {user.firstName}!</div>
      ) : (
        <button onClick={() => login(credentials)}>Login</button>
      )}
    </div>
  );
}
```

### ProtectedRoute
Wrapper component for protecting routes.

```jsx
import { ProtectedRoute } from './frontend/auth';

// Basic protection
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>

// Role-based protection
<ProtectedRoute requiredRoles={['admin']}>
  <AdminPanel />
</ProtectedRoute>

// Permission-based protection
<ProtectedRoute requiredPermissions={['user:read', 'user:write']}>
  <UserManagement />
</ProtectedRoute>
```

### AuthLayout
Complete authentication interface with login, register, and password reset.

```jsx
import { AuthLayout } from './frontend/auth';

// Basic usage
<AuthLayout />

// Custom initial view
<AuthLayout initialView="register" />
```

## API Integration

### Backend Endpoints

The system expects these API endpoints:

```
POST /api/auth/login
POST /api/auth/register
POST /api/auth/logout
POST /api/auth/refresh
POST /api/auth/forgot-password
POST /api/auth/reset-password
POST /api/auth/verify-email
GET  /api/auth/verify-token
POST /api/auth/mfa/setup
POST /api/auth/mfa/verify
```

### Token Management

```jsx
import { tokenManager } from './frontend/auth';

// Get current tokens
const tokens = tokenManager.getTokens();

// Check if user has permission
const canEdit = tokenManager.hasPermission('user:edit');

// Get user info from token
const user = tokenManager.getUserFromToken();
```

## Advanced Usage

### Custom Validation

```jsx
import { validateForm, validationRules } from './frontend/auth';

const rules = {
  email: validationRules.email,
  password: validationRules.password,
  customField: {
    required: true,
    custom: (value) => value.length > 5,
    customMessage: 'Must be longer than 5 characters'
  }
};

const { isValid, errors } = validateForm(formData, rules);
```

### Permission-Based UI

```jsx
import { PermissionGate } from './frontend/auth';

<PermissionGate permissions={['admin']}>
  <AdminButton />
</PermissionGate>

<PermissionGate roles={['moderator']} fallback={<div>Access denied</div>}>
  <ModeratorPanel />
</PermissionGate>
```

### Notifications

```jsx
import { useNotification } from './frontend/auth';

function MyComponent() {
  const { showSuccess, showError } = useNotification();

  const handleAction = async () => {
    try {
      await someAction();
      showSuccess('Action completed successfully!');
    } catch (error) {
      showError('Action failed. Please try again.');
    }
  };
}
```

## Styling

### CSS Classes

The system uses BEM-style CSS classes:

```css
/* Form elements */
.auth-form
.form-group
.form-input
.submit-button

/* Layout */
.auth-layout
.auth-container
.auth-brand

/* Components */
.password-strength-indicator
.mfa-setup-container
.notification-container
```

### Customization

Override default styles:

```css
/* Custom theme */
:root {
  --auth-primary-color: #your-color;
  --auth-secondary-color: #your-color;
}

.auth-layout {
  background: linear-gradient(135deg, #your-gradient);
}
```

## Security Considerations

### Token Storage
- **SessionStorage**: Default, tab-specific storage
- **LocalStorage**: Persistent storage (remember me)
- **Cookies**: Server-controlled storage (recommended for production)

### CSRF Protection
- SameSite cookie attributes
- CSRF tokens for state-changing operations

### Rate Limiting
- Built-in handling for 429 responses
- Exponential backoff for retries

## Browser Support

- **Modern Browsers**: Chrome 70+, Firefox 65+, Safari 12+, Edge 79+
- **Mobile**: iOS Safari 12+, Chrome Mobile 70+
- **Features**: ES6+, Fetch API, localStorage

## Performance

### Bundle Size
- **Gzipped**: ~45KB (including dependencies)
- **Tree Shaking**: Supports ES6 modules
- **Code Splitting**: Route-based splitting ready

### Optimizations
- Lazy loading for heavy components
- Memoized validation functions
- Efficient re-renders with React.memo

## Testing

### Unit Tests
```bash
# Run tests
npm test

# Coverage
npm run test:coverage
```

### Integration Tests
```bash
# E2E tests
npm run test:e2e
```

## Troubleshooting

### Common Issues

**Token Refresh Loop**
- Check API endpoint responses
- Verify token expiry handling

**CORS Errors**
- Configure backend CORS settings
- Check API_URL environment variable

**Validation Not Working**
- Ensure validation rules are properly configured
- Check console for JavaScript errors

### Debug Mode

Enable debug logging:

```jsx
localStorage.setItem('auth_debug', 'true');
```

## Migration Guide

### From v1.x to v2.x
- Update imports: `import { AuthProvider } from './frontend/auth'`
- Replace deprecated `useAuthContext` with `useAuth`
- Update CSS class names (breaking change)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.