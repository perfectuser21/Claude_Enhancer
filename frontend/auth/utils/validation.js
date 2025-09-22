/**
 * Validation utilities for authentication forms
 */

// Email validation
export const validateEmail = (email) => {
  if (!email) return false;

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.toLowerCase());
};

// Password validation
export const validatePassword = (password) => {
  if (!password) return false;

  // Minimum 8 characters, at least one uppercase, one lowercase, one number, one special character
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
  return passwordRegex.test(password);
};

// Password strength calculation
export const validatePasswordStrength = (password) => {
  if (!password) return { score: 0, feedback: [] };

  let score = 0;
  const feedback = [];

  // Length check
  if (password.length >= 8) {
    score += 20;
  } else {
    feedback.push('Use at least 8 characters');
  }

  if (password.length >= 12) {
    score += 10;
  }

  // Character variety checks
  if (/[a-z]/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include lowercase letters');
  }

  if (/[A-Z]/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include uppercase letters');
  }

  if (/\d/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include numbers');
  }

  if (/[@$!%*?&]/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include special characters (@$!%*?&)');
  }

  // Additional complexity
  if (/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
    score += 5;
  }

  if (/(?=.*[@$!%*?&])/.test(password)) {
    score += 5;
  }

  // Common patterns that reduce security
  if (/(.)\1{2,}/.test(password)) {
    score -= 10;
    feedback.push('Avoid repeating characters');
  }

  if (/123|abc|qwe|password|admin/i.test(password)) {
    score -= 15;
    feedback.push('Avoid common patterns');
  }

  // Determine strength level
  let level = 'very-weak';
  let message = 'Very Weak';

  if (score >= 80) {
    level = 'very-strong';
    message = 'Very Strong';
  } else if (score >= 60) {
    level = 'strong';
    message = 'Strong';
  } else if (score >= 40) {
    level = 'medium';
    message = 'Medium';
  } else if (score >= 20) {
    level = 'weak';
    message = 'Weak';
  }

  return {
    score: Math.max(0, Math.min(100, score)),
    level,
    message,
    feedback: feedback.slice(0, 3) // Limit feedback to top 3 issues
  };
};

// Name validation
export const validateName = (name) => {
  if (!name) return false;

  // Allow letters, spaces, hyphens, apostrophes
  const nameRegex = /^[a-zA-Z\s'-]{2,50}$/;
  return nameRegex.test(name.trim());
};

// Phone number validation (international format)
export const validatePhone = (phone) => {
  if (!phone) return false;

  // Basic international phone format
  const phoneRegex = /^\+?[\d\s\-\(\)]{10,15}$/;
  return phoneRegex.test(phone);
};

// MFA code validation
export const validateMFACode = (code, type = 'totp') => {
  if (!code) return false;

  const cleanCode = code.replace(/\s/g, '');

  switch (type) {
    case 'totp':
      // 6-digit TOTP code
      return /^\d{6}$/.test(cleanCode);
    case 'sms':
    case 'email':
      // 6-digit verification code
      return /^\d{6}$/.test(cleanCode);
    case 'backup':
      // 8-character backup code
      return /^[A-Z0-9]{8}$/.test(cleanCode.toUpperCase());
    default:
      return false;
  }
};

// URL validation
export const validateURL = (url) => {
  if (!url) return false;

  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

// Date validation
export const validateDate = (date, minAge = 13) => {
  if (!date) return false;

  const inputDate = new Date(date);
  const today = new Date();
  const minDate = new Date(today.getFullYear() - minAge, today.getMonth(), today.getDate());

  return inputDate <= minDate;
};

// Form validation helpers
export const validateForm = (data, rules) => {
  const errors = {};

  Object.keys(rules).forEach(field => {
    const value = data[field];
    const fieldRules = rules[field];

    // Required check
    if (fieldRules.required && (!value || value.toString().trim() === '')) {
      errors[field] = fieldRules.requiredMessage || `${field} is required`;
      return;
    }

    // Skip other validations if field is empty and not required
    if (!value && !fieldRules.required) {
      return;
    }

    // Type-specific validations
    if (fieldRules.type === 'email' && !validateEmail(value)) {
      errors[field] = fieldRules.emailMessage || 'Please enter a valid email address';
    }

    if (fieldRules.type === 'password' && !validatePassword(value)) {
      errors[field] = fieldRules.passwordMessage || 'Password does not meet requirements';
    }

    if (fieldRules.type === 'name' && !validateName(value)) {
      errors[field] = fieldRules.nameMessage || 'Please enter a valid name';
    }

    if (fieldRules.type === 'phone' && !validatePhone(value)) {
      errors[field] = fieldRules.phoneMessage || 'Please enter a valid phone number';
    }

    // Length validations
    if (fieldRules.minLength && value.length < fieldRules.minLength) {
      errors[field] = fieldRules.minLengthMessage ||
        `Must be at least ${fieldRules.minLength} characters`;
    }

    if (fieldRules.maxLength && value.length > fieldRules.maxLength) {
      errors[field] = fieldRules.maxLengthMessage ||
        `Must be no more than ${fieldRules.maxLength} characters`;
    }

    // Pattern validation
    if (fieldRules.pattern && !fieldRules.pattern.test(value)) {
      errors[field] = fieldRules.patternMessage || 'Invalid format';
    }

    // Custom validation function
    if (fieldRules.custom && !fieldRules.custom(value, data)) {
      errors[field] = fieldRules.customMessage || 'Invalid value';
    }
  });

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

// Sanitization helpers
export const sanitizeInput = (input, type = 'text') => {
  if (!input) return '';

  switch (type) {
    case 'email':
      return input.toLowerCase().trim();
    case 'name':
      return input.trim().replace(/\s+/g, ' ');
    case 'phone':
      return input.replace(/[^\d\+\-\(\)\s]/g, '');
    case 'alphanumeric':
      return input.replace(/[^a-zA-Z0-9]/g, '');
    case 'numeric':
      return input.replace(/[^0-9]/g, '');
    default:
      return input.trim();
  }
};

// Common validation rules presets
export const validationRules = {
  email: {
    required: true,
    type: 'email',
    requiredMessage: 'Email is required',
    emailMessage: 'Please enter a valid email address'
  },

  password: {
    required: true,
    type: 'password',
    minLength: 8,
    requiredMessage: 'Password is required',
    passwordMessage: 'Password must be at least 8 characters with uppercase, lowercase, number, and special character'
  },

  firstName: {
    required: true,
    type: 'name',
    minLength: 2,
    maxLength: 50,
    requiredMessage: 'First name is required',
    nameMessage: 'Please enter a valid first name'
  },

  lastName: {
    required: true,
    type: 'name',
    minLength: 2,
    maxLength: 50,
    requiredMessage: 'Last name is required',
    nameMessage: 'Please enter a valid last name'
  },

  phone: {
    required: false,
    type: 'phone',
    phoneMessage: 'Please enter a valid phone number'
  },

  confirmPassword: {
    required: true,
    custom: (value, data) => value === data.password,
    customMessage: 'Passwords do not match'
  }
};