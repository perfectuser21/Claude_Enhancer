import React from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  SimpleGrid,
  Card,
  CardHeader,
  CardBody,
  Text,
  Icon,
  HStack,
  Badge,
  useColorModeValue,
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import {
  FiActivity,
  FiCode,
  FiFileText,
  FiShield,
  FiTrendingUp,
  FiList,
} from 'react-icons/fi';

interface DashboardCard {
  title: string;
  description: string;
  icon: any;
  path: string;
  badge?: string;
  badgeColor?: string;
}

const WorkflowDashboardPage: React.FC = () => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  const dashboardCards: DashboardCard[] = [
    {
      title: 'Phase Details',
      description: 'View detailed execution flow of each workflow phase',
      icon: FiActivity,
      path: '/workflow/phases/phase-123',
      badge: 'Live',
      badgeColor: 'green',
    },
    {
      title: 'Agent Workflows',
      description: 'Track agent tool calls and execution details',
      icon: FiCode,
      path: '/workflow/agents/agent-456',
      badge: 'New',
      badgeColor: 'blue',
    },
    {
      title: 'Log Viewer',
      description: 'Real-time log streaming with search and filters',
      icon: FiFileText,
      path: '/workflow/logs',
      badge: 'Live',
      badgeColor: 'green',
    },
    {
      title: 'Quality Gates',
      description: 'Phase 3 and Phase 4 quality assurance results',
      icon: FiShield,
      path: '/workflow/quality-gates',
    },
    {
      title: 'Performance Budget',
      description: '90+ metrics monitoring and trending',
      icon: FiTrendingUp,
      path: '/workflow/performance',
    },
    {
      title: 'All Sessions',
      description: 'Browse workflow execution history',
      icon: FiList,
      path: '/workflow/sessions',
    },
  ];

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Header */}
        <VStack align="start" spacing={2}>
          <Heading size="xl">Workflow Dashboard</Heading>
          <Text fontSize="lg" color="gray.600">
            Real-time insights into Claude Enhancer execution details
          </Text>
        </VStack>

        {/* Dashboard Cards Grid */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
          {dashboardCards.map((card, index) => (
            <Card
              key={index}
              as={RouterLink}
              to={card.path}
              bg={bgColor}
              borderWidth="1px"
              borderColor={borderColor}
              transition="all 0.2s"
              _hover={{
                transform: 'translateY(-4px)',
                boxShadow: 'lg',
                bg: hoverBg,
              }}
              cursor="pointer"
            >
              <CardHeader>
                <HStack justify="space-between">
                  <HStack spacing={3}>
                    <Icon as={card.icon} boxSize={6} color="blue.500" />
                    <Heading size="md">{card.title}</Heading>
                  </HStack>
                  {card.badge && (
                    <Badge colorScheme={card.badgeColor || 'gray'}>
                      {card.badge}
                    </Badge>
                  )}
                </HStack>
              </CardHeader>
              <CardBody>
                <Text color="gray.600">{card.description}</Text>
              </CardBody>
            </Card>
          ))}
        </SimpleGrid>

        {/* Quick Stats */}
        <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4}>
          <Card bg={bgColor} borderWidth="1px">
            <CardBody>
              <VStack align="start">
                <Text fontSize="sm" color="gray.600">
                  Active Sessions
                </Text>
                <Text fontSize="2xl" fontWeight="bold">
                  3
                </Text>
              </VStack>
            </CardBody>
          </Card>

          <Card bg={bgColor} borderWidth="1px">
            <CardBody>
              <VStack align="start">
                <Text fontSize="sm" color="gray.600">
                  Agents Running
                </Text>
                <Text fontSize="2xl" fontWeight="bold">
                  5
                </Text>
              </VStack>
            </CardBody>
          </Card>

          <Card bg={bgColor} borderWidth="1px">
            <CardBody>
              <VStack align="start">
                <Text fontSize="sm" color="gray.600">
                  Quality Gates Passed
                </Text>
                <Text fontSize="2xl" fontWeight="bold" color="green.500">
                  2/2
                </Text>
              </VStack>
            </CardBody>
          </Card>

          <Card bg={bgColor} borderWidth="1px">
            <CardBody>
              <VStack align="start">
                <Text fontSize="sm" color="gray.600">
                  Metrics Monitored
                </Text>
                <Text fontSize="2xl" fontWeight="bold">
                  90+
                </Text>
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>
      </VStack>
    </Container>
  );
};

export default WorkflowDashboardPage;
