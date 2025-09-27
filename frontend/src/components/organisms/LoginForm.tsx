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
  Checkbox,
  useColorModeValue,
  Card,
  CardBody,
  Heading,
  Divider,
  HStack,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Mail, Lock } from 'lucide-react';
import { LoginCredentials } from '../../types';
import { useAuthStore } from '../../store';

const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Invalid email address'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(6, 'Password must be at least 6 characters'),
  rememberMe: z.boolean().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onSwitchToRegister?: () => void;
  onSuccess?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({
  onSwitchToRegister,
  onSuccess,
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const { login, isLoading, error } = useAuthStore();

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      rememberMe: false,
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login({
        email: data.email,
        password: data.password,
        rememberMe: data.rememberMe,
      });
      onSuccess?.();
    } catch (error: any) {
      setError('root', {
        message: error.message || 'Login failed',
      });
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Card
      maxW="md"
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
              Welcome Back
            </Heading>
            <Text color="gray.600" _dark={{ color: 'gray.400' }}>
              Sign in to your account to continue
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
              {/* Email Field */}
              <FormControl isInvalid={!!errors.email}>
                <FormLabel>Email Address</FormLabel>
                <InputGroup>
                  <Input
                    {...register('email')}
                    type="email"
                    placeholder="Enter your email"
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

              {/* Password Field */}
              <FormControl isInvalid={!!errors.password}>
                <FormLabel>Password</FormLabel>
                <InputGroup>
                  <Input
                    {...register('password')}
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your password"
                    variant="filled"
                    autoComplete="current-password"
                  />
                  <InputRightElement>
                    <IconButton
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      icon={showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      variant="ghost"
                      size="sm"
                      onClick={togglePasswordVisibility}
                    />
                  </InputRightElement>
                </InputGroup>
                {errors.password && (
                  <Text fontSize="sm" color="red.500" mt={1}>
                    {errors.password.message}
                  </Text>
                )}
              </FormControl>

              {/* Remember Me & Forgot Password */}
              <HStack justify="space-between" w="full">
                <Checkbox {...register('rememberMe')} colorScheme="brand">
                  Remember me
                </Checkbox>
                <Link
                  color="brand.500"
                  fontSize="sm"
                  _hover={{ textDecoration: 'underline' }}
                >
                  Forgot password?
                </Link>
              </HStack>

              {/* Submit Button */}
              <Button
                type="submit"
                colorScheme="brand"
                size="lg"
                w="full"
                isLoading={isSubmitting || isLoading}
                loadingText="Signing in..."
              >
                Sign In
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

          {/* Switch to Register */}
          <Box textAlign="center">
            <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.400' }}>
              Don't have an account?{' '}
              <Link
                color="brand.500"
                fontWeight="600"
                onClick={onSwitchToRegister}
                _hover={{ textDecoration: 'underline', cursor: 'pointer' }}
              >
                Sign up here
              </Link>
            </Text>
          </Box>

          {/* Demo Credentials */}
          <Box
            bg="blue.50"
            _dark={{ bg: 'blue.900' }}
            p={4}
            borderRadius="md"
            border="1px solid"
            borderColor="blue.200"
            _dark={{ borderColor: 'blue.700' }}
          >
            <Text fontSize="sm" fontWeight="600" color="blue.800" _dark={{ color: 'blue.200' }} mb={2}>
              Demo Credentials
            </Text>
            <VStack spacing={1} fontSize="sm" color="blue.700" _dark={{ color: 'blue.300' }}>
              <Text>Email: demo@example.com</Text>
              <Text>Password: demo123</Text>
            </VStack>
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
};