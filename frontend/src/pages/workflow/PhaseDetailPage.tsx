import React from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  Card,
  CardBody,
  useColorModeValue,
} from '@chakra-ui/react';
import { useParams } from 'react-router-dom';

const PhaseDetailPage: React.FC = () => {
  const { phaseId } = useParams<{ phaseId: string }>();
  const bgColor = useColorModeValue('white', 'gray.800');

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        <HStack justify="space-between">
          <Heading size="lg">Phase Detail: {phaseId}</Heading>
          <Badge colorScheme="green">Completed</Badge>
        </HStack>

        <Card bg={bgColor}>
          <CardBody>
            <Text>Phase execution details will appear here.</Text>
            <Text fontSize="sm" color="gray.600" mt={2}>
              Real-time phase tracking with WebSocket updates.
            </Text>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default PhaseDetailPage;
