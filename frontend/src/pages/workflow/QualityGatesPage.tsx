import React, { useEffect, useState } from 'react';
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
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  List,
  ListItem,
  ListIcon,
  Divider,
  useColorModeValue,
  Icon,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
} from '@chakra-ui/react';
import {
  FiCheckCircle,
  FiXCircle,
  FiAlertTriangle,
  FiShield,
  FiCode,
  FiFileText,
} from 'react-icons/fi';

interface QualityCheck {
  name: string;
  status: 'passed' | 'failed' | 'warning' | 'skipped';
  message: string;
  details?: string;
}

interface QualityGate {
  phase: 'Phase 3' | 'Phase 4';
  status: 'passed' | 'failed' | 'in_progress';
  timestamp: string;
  checks: QualityCheck[];
  overall_score: number;
}

const QualityGatesPage: React.FC = () => {
  const [phase3Gate, setPhase3Gate] = useState<QualityGate | null>(null);
  const [phase4Gate, setPhase4Gate] = useState<QualityGate | null>(null);
  const [loading, setLoading] = useState(true);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    // Mock data - replace with API call
    const mockPhase3: QualityGate = {
      phase: 'Phase 3',
      status: 'passed',
      timestamp: new Date().toISOString(),
      overall_score: 100,
      checks: [
        {
          name: 'Shell Syntax Check',
          status: 'passed',
          message: 'All shell scripts passed syntax validation',
          details: 'Checked 15 files with bash -n',
        },
        {
          name: 'Shellcheck Linting',
          status: 'passed',
          message: 'No linting issues found',
          details: 'Scanned 15 shell scripts',
        },
        {
          name: 'Code Complexity',
          status: 'passed',
          message: 'All functions under 150 lines',
          details: 'Max function length: 89 lines',
        },
        {
          name: 'Hook Performance',
          status: 'passed',
          message: 'All hooks execute under 2 seconds',
          details: 'Slowest hook: 1.2s (quality_gate.sh)',
        },
        {
          name: 'Unit Tests',
          status: 'passed',
          message: '45/45 tests passed',
          details: 'Coverage: 87%',
        },
      ],
    };

    const mockPhase4: QualityGate = {
      phase: 'Phase 4',
      status: 'passed',
      timestamp: new Date().toISOString(),
      overall_score: 95,
      checks: [
        {
          name: 'Hook Registration',
          status: 'passed',
          message: 'All 17 hooks correctly registered',
          details: 'Verified in .claude/settings.json',
        },
        {
          name: 'Document Count',
          status: 'passed',
          message: 'Root directory has 7 core documents',
          details: 'Within allowed limit',
        },
        {
          name: 'Version Consistency',
          status: 'passed',
          message: 'All version numbers match',
          details: 'VERSION, settings.json, CHANGELOG.md all show 6.5.1',
        },
        {
          name: 'Code Pattern Consistency',
          status: 'passed',
          message: 'SQLAlchemy 2.0 syntax unified',
          details: 'All models use mapped_column()',
        },
        {
          name: 'Documentation Completeness',
          status: 'warning',
          message: 'REVIEW.md generated (370 lines)',
          details: 'Some sections could be expanded',
        },
      ],
    };

    setTimeout(() => {
      setPhase3Gate(mockPhase3);
      setPhase4Gate(mockPhase4);
      setLoading(false);
    }, 500);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed':
        return 'green';
      case 'failed':
        return 'red';
      case 'warning':
        return 'orange';
      case 'in_progress':
        return 'blue';
      default:
        return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return FiCheckCircle;
      case 'failed':
        return FiXCircle;
      case 'warning':
        return FiAlertTriangle;
      default:
        return FiCheckCircle;
    }
  };

  const renderGateCard = (gate: QualityGate) => {
    const passedChecks = gate.checks.filter((c) => c.status === 'passed').length;
    const failedChecks = gate.checks.filter((c) => c.status === 'failed').length;
    const warningChecks = gate.checks.filter((c) => c.status === 'warning').length;

    return (
      <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
        <CardHeader>
          <HStack justify="space-between">
            <HStack>
              <Icon as={FiShield} boxSize={6} />
              <Heading size="md">{gate.phase} Quality Gate</Heading>
            </HStack>
            <Badge
              colorScheme={getStatusColor(gate.status)}
              fontSize="md"
              px={3}
              py={1}
            >
              {gate.status.toUpperCase()}
            </Badge>
          </HStack>
          <Text fontSize="sm" color="gray.600" mt={2}>
            {new Date(gate.timestamp).toLocaleString()}
          </Text>
        </CardHeader>
        <CardBody>
          <VStack align="stretch" spacing={6}>
            {/* Overall Score */}
            <Box>
              <HStack justify="space-between" mb={2}>
                <Text fontWeight="bold">Overall Score</Text>
                <Text fontSize="2xl" fontWeight="bold" color="green.500">
                  {gate.overall_score}/100
                </Text>
              </HStack>
              <Progress
                value={gate.overall_score}
                colorScheme={gate.overall_score >= 80 ? 'green' : 'orange'}
                size="lg"
                borderRadius="md"
              />
            </Box>

            <Divider />

            {/* Summary Stats */}
            <SimpleGrid columns={3} spacing={4}>
              <Stat>
                <StatLabel>
                  <Icon as={FiCheckCircle} color="green.500" mr={1} />
                  Passed
                </StatLabel>
                <StatNumber color="green.500">{passedChecks}</StatNumber>
                <StatHelpText>checks</StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>
                  <Icon as={FiAlertTriangle} color="orange.500" mr={1} />
                  Warnings
                </StatLabel>
                <StatNumber color="orange.500">{warningChecks}</StatNumber>
                <StatHelpText>checks</StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>
                  <Icon as={FiXCircle} color="red.500" mr={1} />
                  Failed
                </StatLabel>
                <StatNumber color="red.500">{failedChecks}</StatNumber>
                <StatHelpText>checks</StatHelpText>
              </Stat>
            </SimpleGrid>

            <Divider />

            {/* Checks List */}
            <Box>
              <Heading size="sm" mb={4}>
                Quality Checks
              </Heading>
              <List spacing={3}>
                {gate.checks.map((check, index) => (
                  <ListItem key={index}>
                    <Card
                      bg={useColorModeValue('gray.50', 'gray.900')}
                      borderLeftWidth="4px"
                      borderLeftColor={`${getStatusColor(check.status)}.500`}
                      p={4}
                    >
                      <HStack align="start">
                        <Icon
                          as={getStatusIcon(check.status)}
                          boxSize={5}
                          color={`${getStatusColor(check.status)}.500`}
                          mt={1}
                        />
                        <VStack align="start" spacing={1} flex={1}>
                          <HStack justify="space-between" w="100%">
                            <Text fontWeight="bold">{check.name}</Text>
                            <Badge colorScheme={getStatusColor(check.status)}>
                              {check.status}
                            </Badge>
                          </HStack>
                          <Text fontSize="sm">{check.message}</Text>
                          {check.details && (
                            <Text fontSize="xs" color="gray.600">
                              {check.details}
                            </Text>
                          )}
                        </VStack>
                      </HStack>
                    </Card>
                  </ListItem>
                ))}
              </List>
            </Box>
          </VStack>
        </CardBody>
      </Card>
    );
  };

  if (loading) {
    return (
      <Container maxW="container.xl" py={8}>
        <VStack spacing={4}>
          <Heading size="lg">Loading Quality Gates...</Heading>
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
          <Heading size="lg">Quality Gates Dashboard</Heading>
          <Text color="gray.600">
            Real-time quality assurance across Phase 3 and Phase 4
          </Text>
        </VStack>

        {/* Overview Alert */}
        <Alert
          status={
            phase3Gate?.status === 'passed' && phase4Gate?.status === 'passed'
              ? 'success'
              : 'warning'
          }
          variant="left-accent"
        >
          <AlertIcon />
          <Box>
            <AlertTitle>Quality Gate Status</AlertTitle>
            <AlertDescription>
              {phase3Gate?.status === 'passed' && phase4Gate?.status === 'passed'
                ? 'All quality gates passed! Ready for Phase 5.'
                : 'Some quality checks need attention.'}
            </AlertDescription>
          </Box>
        </Alert>

        {/* Tabs for Phase 3 and Phase 4 */}
        <Tabs variant="enclosed" colorScheme="blue">
          <TabList>
            <Tab>
              <HStack>
                <Icon as={FiCode} />
                <Text>Phase 3: Testing</Text>
              </HStack>
            </Tab>
            <Tab>
              <HStack>
                <Icon as={FiFileText} />
                <Text>Phase 4: Review</Text>
              </HStack>
            </Tab>
          </TabList>

          <TabPanels>
            <TabPanel>{phase3Gate && renderGateCard(phase3Gate)}</TabPanel>
            <TabPanel>{phase4Gate && renderGateCard(phase4Gate)}</TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Container>
  );
};

export default QualityGatesPage;
