import React, { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Text,
  Link,
  Alert,
  AlertIcon,
  InputGroup,
  InputRightElement,
  IconButton,
  useColorModeValue,
  Card,
  CardBody,
  Heading,
  Divider,
  HStack,
  Progress,
  List,
  ListItem,
  ListIcon,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Mail, Lock, User, Check, X } from 'lucide-react';
import { RegisterData } from '../../types';
import { useAuthStore } from '../../store';

const registerSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Invalid email address'),
  username: z
    .string()
    .min(1, 'Username is required')
    .min(3, 'Username must be at least 3 characters')
    .max(20, 'Username must be less than 20 characters')
    .regex(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers, and underscores'),
  firstName: z
    .string()
    .min(1, 'First name is required')
    .min(2, 'First name must be at least 2 characters'),
  lastName: z
    .string()
    .min(1, 'Last name is required')
    .min(2, 'Last name must be at least 2 characters'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character'),
  confirmPassword: z
    .string()
    .min(1, 'Please confirm your password'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

interface RegisterFormProps {
  onSwitchToLogin?: () => void;
  onSuccess?: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({
  onSwitchToLogin,
  onSuccess,
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { register: registerUser, isLoading, error } = useAuthStore();

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch,
    setError,
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    mode: 'onChange',
  });

  const watchedPassword = watch('password', '');

  // Password strength calculation
  const getPasswordStrength = (password: string) => {
    let strength = 0;
    const requirements = [
      { regex: /.{8,}/, text: 'At least 8 characters' },
      { regex: /[A-Z]/, text: 'One uppercase letter' },
      { regex: /[a-z]/, text: 'One lowercase letter' },
      { regex: /[0-9]/, text: 'One number' },
      { regex: /[^A-Za-z0-9]/, text: 'One special character' },
    ];

    const passed = requirements.map(req => ({
      ...req,
      passed: req.regex.test(password)
    }));

    strength = passed.filter(req => req.passed).length;

    return { strength, requirements: passed, total: requirements.length };
  };

  const passwordInfo = getPasswordStrength(watchedPassword);
  const strengthPercent = (passwordInfo.strength / passwordInfo.total) * 100;

  const getStrengthColor = () => {
    if (strengthPercent < 40) return 'red';
    if (strengthPercent < 80) return 'yellow';
    return 'green';
  };

  const getStrengthLabel = () => {
    if (strengthPercent < 40) return 'Weak';
    if (strengthPercent < 80) return 'Medium';
    return 'Strong';
  };

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser({
        email: data.email,
        username: data.username,
        firstName: data.firstName,
        lastName: data.lastName,
        password: data.password,
        confirmPassword: data.confirmPassword,
      });
      onSuccess?.();
    } catch (error: any) {
      setError('root', {
        message: error.message || 'Registration failed',
      });
    }
  };

  return (
    <Card
      maxW="lg"
      w="full"
      bg={cardBg}
      border="1px solid"
      borderColor={borderColor}
      shadow="lg"
    >
      <CardBody p={8}>
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <Box textAlign="center">
            <Heading size="lg" mb={2}>
              Create Account
            </Heading>
            <Text color="gray.600" _dark={{ color: 'gray.400' }}>
              Join us to start managing your tasks efficiently
            </Text>
          </Box>

          {/* Error Alert */}
          {(error || errors.root) && (
            <Alert status="error" borderRadius="md">
              <AlertIcon />
              {error || errors.root?.message}
            </Alert>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)}>
            <VStack spacing={4}>
              {/* Name Fields */}
              <HStack spacing={4} w="full">
                <FormControl isInvalid={!!errors.firstName}>
                  <FormLabel>First Name</FormLabel>
                  <Input
                    {...register('firstName')}
                    placeholder="John"
                    variant="filled"
                    autoComplete="given-name"
                  />
                  {errors.firstName && (
                    <Text fontSize="sm" color="red.500" mt={1}>
                      {errors.firstName.message}
                    </Text>
                  )}
                </FormControl>

                <FormControl isInvalid={!!errors.lastName}>
                  <FormLabel>Last Name</FormLabel>
                  <Input
                    {...register('lastName')}
                    placeholder="Doe"
                    variant="filled"
                    autoComplete="family-name"
                  />
                  {errors.lastName && (
                    <Text fontSize="sm" color="red.500" mt={1}>
                      {errors.lastName.message}
                    </Text>
                  )}
                </FormControl>
              </HStack>

              {/* Email Field */}
              <FormControl isInvalid={!!errors.email}>
                <FormLabel>Email Address</FormLabel>
                <InputGroup>
                  <Input
                    {...register('email')}
                    type="email"
                    placeholder="john.doe@example.com"
                    variant="filled"
                    autoComplete="email"
                  />
                  <InputRightElement>
                    <Mail size={18} color="gray" />
                  </InputRightElement>
                </InputGroup>
                {errors.email && (
                  <Text fontSize="sm" color="red.500" mt={1}>
                    {errors.email.message}
                  </Text>
                )}
              </FormControl>

              {/* Username Field */}
              <FormControl isInvalid={!!errors.username}>
                <FormLabel>Username</FormLabel>
                <InputGroup>
                  <Input
                    {...register('username')}
                    placeholder="johndoe123"
                    variant="filled"
                    autoComplete="username"
                  />
                  <InputRightElement>
                    <User size={18} color="gray" />
                  </InputRightElement>
                </InputGroup>
                {errors.username && (
                  <Text fontSize="sm" color="red.500" mt={1}>
                    {errors.username.message}
                  </Text>
                )}
              </FormControl>

              {/* Password Field */}
              <FormControl isInvalid={!!errors.password}>
                <FormLabel>Password</FormLabel>
                <InputGroup>
                  <Input
                    {...register('password')}
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Create a strong password"
                    variant="filled"
                    autoComplete="new-password"
                  />
                  <InputRightElement>
                    <IconButton
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      icon={showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowPassword(!showPassword)}
                    />
                  </InputRightElement>
                </InputGroup>

                {/* Password Strength Indicator */}
                {watchedPassword && (
                  <Box mt={2}>
                    <HStack justify="space-between" mb={1}>
                      <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.400' }}>
                        Password Strength
                      </Text>
                      <Text fontSize="sm" color={`${getStrengthColor()}.500`} fontWeight="600">
                        {getStrengthLabel()}
                      </Text>
                    </HStack>
                    <Progress
                      value={strengthPercent}
                      colorScheme={getStrengthColor()}
                      size="sm"
                      borderRadius="full"
                    />
                    <List spacing={1} mt={2}>
                      {passwordInfo.requirements.map((req, index) => (
                        <ListItem key={index} fontSize="xs" color="gray.600" _dark={{ color: 'gray.400' }}>
                          <ListIcon
                            as={req.passed ? Check : X}
                            color={req.passed ? 'green.500' : 'red.500'}
                          />
                          {req.text}
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                {errors.password && (
                  <Text fontSize="sm" color="red.500" mt={1}>
                    {errors.password.message}
                  </Text>
                )}
              </FormControl>

              {/* Confirm Password Field */}
              <FormControl isInvalid={!!errors.confirmPassword}>
                <FormLabel>Confirm Password</FormLabel>
                <InputGroup>
                  <Input
                    {...register('confirmPassword')}
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Confirm your password"
                    variant="filled"
                    autoComplete="new-password"
                  />
                  <InputRightElement>
                    <IconButton
                      aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                      icon={showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    />
                  </InputRightElement>
                </InputGroup>
                {errors.confirmPassword && (
                  <Text fontSize="sm" color="red.500" mt={1}>
                    {errors.confirmPassword.message}
                  </Text>
                )}
              </FormControl>

              {/* Submit Button */}
              <Button
                type="submit"
                colorScheme="brand"
                size="lg"
                w="full"
                isLoading={isSubmitting || isLoading}
                loadingText="Creating account..."
              >
                Create Account
              </Button>
            </VStack>
          </form>

          {/* Divider */}
          <HStack>
            <Divider />
            <Text fontSize="sm" color="gray.500" whiteSpace="nowrap">
              or
            </Text>
            <Divider />
          </HStack>

          {/* Switch to Login */}
          <Box textAlign="center">
            <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.400' }}>
              Already have an account?{' '}
              <Link
                color="brand.500"
                fontWeight="600"
                onClick={onSwitchToLogin}
                _hover={{ textDecoration: 'underline', cursor: 'pointer' }}
              >
                Sign in here
              </Link>
            </Text>
          </Box>

          {/* Terms */}
          <Text fontSize="xs" color="gray.500" textAlign="center">
            By creating an account, you agree to our{' '}
            <Link color="brand.500" _hover={{ textDecoration: 'underline' }}>
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link color="brand.500" _hover={{ textDecoration: 'underline' }}>
              Privacy Policy
            </Link>
          </Text>
        </VStack>
      </CardBody>
    </Card>
  );
};