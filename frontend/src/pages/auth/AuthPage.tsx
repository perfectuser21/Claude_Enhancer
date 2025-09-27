import React, { useState } from 'react';
import {
  Box,
  Container,
  VStack,
  HStack,
  Text,
  Button,
  useColorModeValue,
  Image,
  Flex,
  Heading,
} from '@chakra-ui/react';
import { LoginForm, RegisterForm } from '../../components/organisms';
import { useAuth } from '../../hooks';

export const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const { isLoading } = useAuth();

  const bg = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  const handleAuthSuccess = () => {
    // Navigation will be handled by the app-level router
    // when the authentication state changes
  };

  return (
    <Box minH="100vh" bg={bg}>
      <Container maxW="7xl" py={12}>
        <Flex
          minH="calc(100vh - 96px)"
          align="center"
          justify="center"
          direction={{ base: 'column', lg: 'row' }}
          gap={12}
        >
          {/* Left Side - Branding */}
          <VStack
            flex="1"
            spacing={8}
            align={{ base: 'center', lg: 'flex-start' }}
            textAlign={{ base: 'center', lg: 'left' }}
            maxW={{ base: 'full', lg: 'lg' }}
          >
            <VStack spacing={4} align={{ base: 'center', lg: 'flex-start' }}>
              <Heading
                size="2xl"
                bgGradient="linear(to-r, brand.400, brand.600)"
                bgClip="text"
                fontWeight="800"
              >
                TaskFlow Pro
              </Heading>
              <Text fontSize="xl" color="gray.600" _dark={{ color: 'gray.400' }} lineHeight="1.6">
                The ultimate task management solution for teams and individuals.
                Organize, collaborate, and achieve more with our intuitive interface.
              </Text>
            </VStack>

            <VStack spacing={6} align={{ base: 'center', lg: 'flex-start' }}>
              <HStack spacing={4} flexWrap="wrap" justify={{ base: 'center', lg: 'flex-start' }}>
                <Box
                  bg={cardBg}
                  p={4}
                  borderRadius="lg"
                  shadow="sm"
                  textAlign="center"
                  minW="120px"
                >
                  <Text fontSize="2xl" fontWeight="700" color="brand.500">
                    1M+
                  </Text>
                  <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.400' }}>
                    Tasks Completed
                  </Text>
                </Box>
                <Box
                  bg={cardBg}
                  p={4}
                  borderRadius="lg"
                  shadow="sm"
                  textAlign="center"
                  minW="120px"
                >
                  <Text fontSize="2xl" fontWeight="700" color="brand.500">
                    50K+
                  </Text>
                  <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.400' }}>
                    Active Users
                  </Text>
                </Box>
                <Box
                  bg={cardBg}
                  p={4}
                  borderRadius="lg"
                  shadow="sm"
                  textAlign="center"
                  minW="120px"
                >
                  <Text fontSize="2xl" fontWeight="700" color="brand.500">
                    99.9%
                  </Text>
                  <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.400' }}>
                    Uptime
                  </Text>
                </Box>
              </HStack>

              <VStack spacing={3} align={{ base: 'center', lg: 'flex-start' }}>
                <Text fontSize="lg" fontWeight="600" color="gray.700" _dark={{ color: 'gray.300' }}>
                  ✨ Why choose TaskFlow Pro?
                </Text>
                <VStack spacing={2} align={{ base: 'center', lg: 'flex-start' }}>
                  {[
                    '🚀 Lightning-fast kanban boards',
                    '🎯 Smart task prioritization',
                    '👥 Seamless team collaboration',
                    '📊 Advanced analytics dashboard',
                    '🔒 Enterprise-grade security',
                    '📱 Mobile-first responsive design',
                  ].map((feature, index) => (
                    <Text
                      key={index}
                      fontSize="md"
                      color="gray.600"
                      _dark={{ color: 'gray.400' }}
                    >
                      {feature}
                    </Text>
                  ))}
                </VStack>
              </VStack>
            </VStack>
          </VStack>

          {/* Right Side - Auth Forms */}
          <Box flex="1" maxW="lg" w="full">
            <VStack spacing={6}>
              {/* Form Toggle */}
              <HStack
                bg={cardBg}
                p={1}
                borderRadius="lg"
                border="1px solid"
                borderColor="gray.200"
                _dark={{ borderColor: 'gray.600' }}
              >
                <Button
                  variant={isLogin ? 'solid' : 'ghost'}
                  colorScheme={isLogin ? 'brand' : 'gray'}
                  size="sm"
                  flex="1"
                  onClick={() => setIsLogin(true)}
                  isDisabled={isLoading}
                >
                  Sign In
                </Button>
                <Button
                  variant={!isLogin ? 'solid' : 'ghost'}
                  colorScheme={!isLogin ? 'brand' : 'gray'}
                  size="sm"
                  flex="1"
                  onClick={() => setIsLogin(false)}
                  isDisabled={isLoading}
                >
                  Sign Up
                </Button>
              </HStack>

              {/* Auth Form */}
              {isLogin ? (
                <LoginForm
                  onSwitchToRegister={() => setIsLogin(false)}
                  onSuccess={handleAuthSuccess}
                />
              ) : (
                <RegisterForm
                  onSwitchToLogin={() => setIsLogin(true)}
                  onSuccess={handleAuthSuccess}
                />
              )}
            </VStack>
          </Box>
        </Flex>
      </Container>
    </Box>
  );
};