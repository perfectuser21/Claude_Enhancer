import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  Card,
  CardHeader,
  CardBody,
  SimpleGrid,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Alert,
  AlertIcon,
  useColorModeValue,
  Icon,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Select,
} from '@chakra-ui/react';
import { FiActivity, FiClock, FiTrendingUp, FiAlertTriangle } from 'react-icons/fi';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface PerformanceMetric {
  name: string;
  category: string;
  current_value: number;
  budget_value: number;
  unit: string;
  status: 'within_budget' | 'warning' | 'exceeded';
  trend: 'up' | 'down' | 'stable';
}

interface PerformanceTrend {
  timestamp: string;
  value: number;
}

const PerformanceBudgetPage: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    // Mock data - replace with API call
    const mockMetrics: PerformanceMetric[] = [
      {
        name: 'API Response Time',
        category: 'API',
        current_value: 145,
        budget_value: 200,
        unit: 'ms',
        status: 'within_budget',
        trend: 'down',
      },
      {
        name: 'WebSocket Latency',
        category: 'WebSocket',
        current_value: 45,
        budget_value: 100,
        unit: 'ms',
        status: 'within_budget',
        trend: 'stable',
      },
      {
        name: 'Database Query Time',
        category: 'Database',
        current_value: 89,
        budget_value: 150,
        unit: 'ms',
        status: 'within_budget',
        trend: 'down',
      },
      {
        name: 'Hook Execution Time',
        category: 'Hooks',
        current_value: 1850,
        budget_value: 2000,
        unit: 'ms',
        status: 'warning',
        trend: 'up',
      },
      {
        name: 'Agent Task Duration',
        category: 'Agents',
        current_value: 45000,
        budget_value: 60000,
        unit: 'ms',
        status: 'within_budget',
        trend: 'stable',
      },
      {
        name: 'Phase Transition Time',
        category: 'Workflow',
        current_value: 500,
        budget_value: 1000,
        unit: 'ms',
        status: 'within_budget',
        trend: 'down',
      },
      {
        name: 'Log Processing Rate',
        category: 'Logs',
        current_value: 8500,
        budget_value: 10000,
        unit: 'lines/s',
        status: 'within_budget',
        trend: 'up',
      },
      {
        name: 'Memory Usage',
        category: 'System',
        current_value: 512,
        budget_value: 1024,
        unit: 'MB',
        status: 'within_budget',
        trend: 'stable',
      },
    ];

    setTimeout(() => {
      setMetrics(mockMetrics);
      setLoading(false);
    }, 500);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'within_budget':
        return 'green';
      case 'warning':
        return 'orange';
      case 'exceeded':
        return 'red';
      default:
        return 'gray';
    }
  };

  const calculateUsagePercentage = (current: number, budget: number) => {
    return Math.min((current / budget) * 100, 100);
  };

  const filteredMetrics =
    selectedCategory === 'all'
      ? metrics
      : metrics.filter((m) => m.category === selectedCategory);

  const categories = Array.from(new Set(metrics.map((m) => m.category)));

  const withinBudget = metrics.filter((m) => m.status === 'within_budget').length;
  const warnings = metrics.filter((m) => m.status === 'warning').length;
  const exceeded = metrics.filter((m) => m.status === 'exceeded').length;

  // Mock trend data for chart
  const trendData = [
    { timestamp: '10:00', api: 150, websocket: 50, database: 95 },
    { timestamp: '10:15', api: 145, websocket: 48, database: 92 },
    { timestamp: '10:30', api: 148, websocket: 45, database: 89 },
    { timestamp: '10:45', api: 142, websocket: 47, database: 88 },
    { timestamp: '11:00', api: 145, websocket: 45, database: 89 },
  ];

  if (loading) {
    return (
      <Container maxW="container.xl" py={8}>
        <VStack spacing={4}>
          <Heading size="lg">Loading Performance Metrics...</Heading>
          <Progress size="xs" isIndeterminate w="100%" />
        </VStack>
      </Container>
    );
  }

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <VStack align="start" spacing={1}>
          <Heading size="lg">Performance Budget Dashboard</Heading>
          <Text color="gray.600">
            Monitoring 90+ performance metrics across the system
          </Text>
        </VStack>

        {/* Overview Stats */}
        <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4}>
          <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
            <CardBody>
              <Stat>
                <StatLabel>
                  <Icon as={FiActivity} mr={1} />
                  Total Metrics
                </StatLabel>
                <StatNumber>{metrics.length}</StatNumber>
                <StatHelpText>Tracked metrics</StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
            <CardBody>
              <Stat>
                <StatLabel>Within Budget</StatLabel>
                <StatNumber color="green.500">{withinBudget}</StatNumber>
                <StatHelpText>
                  {((withinBudget / metrics.length) * 100).toFixed(0)}%
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
            <CardBody>
              <Stat>
                <StatLabel>Warnings</StatLabel>
                <StatNumber color="orange.500">{warnings}</StatNumber>
                <StatHelpText>Near budget limit</StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
            <CardBody>
              <Stat>
                <StatLabel>Exceeded</StatLabel>
                <StatNumber color="red.500">{exceeded}</StatNumber>
                <StatHelpText>Over budget</StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Alert for exceeded budgets */}
        {exceeded > 0 && (
          <Alert status="error">
            <AlertIcon />
            {exceeded} metric(s) exceeded performance budget. Immediate attention
            required.
          </Alert>
        )}

        {warnings > 0 && (
          <Alert status="warning">
            <AlertIcon />
            {warnings} metric(s) approaching budget limits. Consider optimization.
          </Alert>
        )}

        {/* Trend Chart */}
        <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
          <CardHeader>
            <Heading size="md">Performance Trends (Last Hour)</Heading>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis label={{ value: 'Time (ms)', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="api"
                  stroke="#3182CE"
                  name="API Response"
                />
                <Line
                  type="monotone"
                  dataKey="websocket"
                  stroke="#38A169"
                  name="WebSocket"
                />
                <Line
                  type="monotone"
                  dataKey="database"
                  stroke="#DD6B20"
                  name="Database"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        {/* Metrics Table */}
        <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
          <CardHeader>
            <HStack justify="space-between">
              <Heading size="md">Performance Metrics</Heading>
              <Select
                w="200px"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                <option value="all">All Categories</option>
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </Select>
            </HStack>
          </CardHeader>
          <CardBody>
            <Box overflowX="auto">
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>Metric Name</Th>
                    <Th>Category</Th>
                    <Th isNumeric>Current</Th>
                    <Th isNumeric>Budget</Th>
                    <Th>Usage</Th>
                    <Th>Trend</Th>
                    <Th>Status</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {filteredMetrics.map((metric, index) => {
                    const usage = calculateUsagePercentage(
                      metric.current_value,
                      metric.budget_value
                    );
                    return (
                      <Tr key={index}>
                        <Td fontWeight="medium">{metric.name}</Td>
                        <Td>
                          <Badge variant="subtle">{metric.category}</Badge>
                        </Td>
                        <Td isNumeric>
                          {metric.current_value.toLocaleString()} {metric.unit}
                        </Td>
                        <Td isNumeric>
                          {metric.budget_value.toLocaleString()} {metric.unit}
                        </Td>
                        <Td>
                          <VStack align="start" spacing={1}>
                            <Progress
                              value={usage}
                              colorScheme={getStatusColor(metric.status)}
                              size="sm"
                              w="100px"
                              borderRadius="md"
                            />
                            <Text fontSize="xs" color="gray.600">
                              {usage.toFixed(0)}%
                            </Text>
                          </VStack>
                        </Td>
                        <Td>
                          <StatArrow
                            type={metric.trend === 'up' ? 'increase' : metric.trend === 'down' ? 'decrease' : undefined}
                          />
                        </Td>
                        <Td>
                          <Badge colorScheme={getStatusColor(metric.status)}>
                            {metric.status.replace('_', ' ')}
                          </Badge>
                        </Td>
                      </Tr>
                    );
                  })}
                </Tbody>
              </Table>
            </Box>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default PerformanceBudgetPage;
