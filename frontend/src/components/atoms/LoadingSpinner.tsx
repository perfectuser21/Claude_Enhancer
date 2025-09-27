import React from 'react';
import { Box, Spinner, Text, VStack, SpinnerProps } from '@chakra-ui/react';

interface LoadingSpinnerProps extends SpinnerProps {
  message?: string;
  fullScreen?: boolean;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  fullScreen = false,
  ...props
}) => {
  const spinner = (
    <VStack spacing={4}>
      <Spinner
        thickness="4px"
        speed="0.65s"
        emptyColor="gray.200"
        color="brand.500"
        size="xl"
        {...props}
      />
      {message && (
        <Text fontSize="md" color="gray.600" _dark={{ color: 'gray.400' }}>
          {message}
        </Text>
      )}
    </VStack>
  );

  if (fullScreen) {
    return (
      <Box
        position="fixed"
        top={0}
        left={0}
        right={0}
        bottom={0}
        bg="white"
        _dark={{ bg: 'gray.900' }}
        display="flex"
        alignItems="center"
        justifyContent="center"
        zIndex={9999}
      >
        {spinner}
      </Box>
    );
  }

  return (
    <Box
      display="flex"
      alignItems="center"
      justifyContent="center"
      py={8}
    >
      {spinner}
    </Box>
  );
};