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
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Progress,
  Code,
  Divider,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
  useColorModeValue,
  Icon,
} from '@chakra-ui/react';
import { useParams } from 'react-router-dom';
import {
  FiTool,
  FiCheckCircle,
  FiXCircle,
  FiClock,
  FiFileText,
} from 'react-icons/fi';

interface ToolCall {
  tool_name: string;
  input_parameters: Record<string, any>;
  output_result: any;
  duration_ms: number;
  status: 'success' | 'failed' | 'in_progress';
  error_message?: string;
}

interface AgentExecution {
  execution_id: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  tool_calls: ToolCall[];
  output_summary?: string;
  error_message?: string;
}

const AgentWorkflowPage: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>();
  const [agentData, setAgentData] = useState<AgentExecution | null>(null);
  const [loading, setLoading] = useState(true);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const codeBgColor = useColorModeValue('gray.50', 'gray.900');

  useEffect(() => {
    // Mock data - replace with API call
    const mockData: AgentExecution = {
      execution_id: executionId || '1',
      agent_name: 'backend-architect',
      status: 'completed',
      started_at: new Date().toISOString(),
      completed_at: new Date(Date.now() + 45000).toISOString(),
      duration_ms: 45000,
      tool_calls: [
        {
          tool_name: 'Read',
          input_parameters: {
            file_path: '/home/xx/dev/Claude Enhancer 5.0/src/models/workflow.py',
          },
          output_result: { lines: 422, success: true },
          duration_ms: 150,
          status: 'success',
        },
        {
          tool_name: 'Grep',
          input_parameters: {
            pattern: 'class.*BaseModel',
            path: 'src/models/',
          },
          output_result: { matches: 8, files: ['workflow.py'] },
          duration_ms: 89,
          status: 'success',
        },
        {
          tool_name: 'Write',
          input_parameters: {
            file_path: '/home/xx/dev/Claude Enhancer 5.0/src/api/routes/workflow_dashboard.py',
            content: '# API Routes...',
          },
          output_result: { bytes_written: 31630 },
          duration_ms: 250,
          status: 'success',
        },
      ],
      output_summary: 'Successfully created workflow dashboard API with 22 endpoints',
    };

    setTimeout(() => {
      setAgentData(mockData);
      setLoading(false);
    }, 500);
  }, [executionId]);

  if (loading || !agentData) {
    return (
      <Container maxW="container.xl" py={8}>
        <VStack spacing={4}>
          <Heading size="lg">Loading Agent Workflow...</Heading>
          <Progress size="xs" isIndeterminate w="100%" />
        </VStack>
      </Container>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'success':
        return 'green';
      case 'running':
      case 'in_progress':
        return 'blue';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'success':
        return FiCheckCircle;
      case 'failed':
        return FiXCircle;
      default:
        return FiClock;
    }
  };

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <VStack align="start" spacing={1}>
            <Heading size="lg">Agent: {agentData.agent_name}</Heading>
            <HStack>
              <Badge colorScheme={getStatusColor(agentData.status)}>
                {agentData.status}
              </Badge>
              <Text fontSize="sm" color="gray.600">
                ID: {agentData.execution_id}
              </Text>
            </HStack>
          </VStack>
        </HStack>

        {/* Stats */}
        <SimpleGrid columns={{ base: 1, md: 4 }} spacing={4}>
          <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
            <CardBody>
              <Stat>
                <StatLabel>Duration</StatLabel>
                <StatNumber>
                  {agentData.duration_ms
                    ? `${(agentData.duration_ms / 1000).toFixed(1)}s`
                    : 'N/A'}
                </StatNumber>
                <StatHelpText>Total execution time</StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
            <CardBody>
              <Stat>
                <StatLabel>Tool Calls</StatLabel>
                <StatNumber>{agentData.tool_calls.length}</StatNumber>
                <StatHelpText>Total tools used</StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
            <CardBody>
              <Stat>
                <StatLabel>Success Rate</StatLabel>
                <StatNumber>
                  {(
                    (agentData.tool_calls.filter((t) => t.status === 'success')
                      .length /
                      agentData.tool_calls.length) *
                    100
                  ).toFixed(0)}
                  %
                </StatNumber>
                <StatHelpText>
                  {agentData.tool_calls.filter((t) => t.status === 'success').length}/
                  {agentData.tool_calls.length} successful
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>

          <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
            <CardBody>
              <Stat>
                <StatLabel>Avg Tool Time</StatLabel>
                <StatNumber>
                  {(
                    agentData.tool_calls.reduce(
                      (sum, t) => sum + t.duration_ms,
                      0
                    ) / agentData.tool_calls.length
                  ).toFixed(0)}
                  ms
                </StatNumber>
                <StatHelpText>Per tool call</StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Output Summary */}
        {agentData.output_summary && (
          <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
            <CardHeader>
              <Heading size="md">Output Summary</Heading>
            </CardHeader>
            <CardBody>
              <Text>{agentData.output_summary}</Text>
            </CardBody>
          </Card>
        )}

        {/* Tool Calls */}
        <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
          <CardHeader>
            <Heading size="md">Tool Calls Timeline</Heading>
          </CardHeader>
          <CardBody>
            <Accordion allowMultiple>
              {agentData.tool_calls.map((toolCall, index) => (
                <AccordionItem key={index}>
                  <h2>
                    <AccordionButton>
                      <HStack flex="1" textAlign="left" spacing={4}>
                        <Icon
                          as={getStatusIcon(toolCall.status)}
                          color={`${getStatusColor(toolCall.status)}.500`}
                        />
                        <Icon as={FiTool} />
                        <Text fontWeight="bold">{toolCall.tool_name}</Text>
                        <Badge colorScheme={getStatusColor(toolCall.status)}>
                          {toolCall.status}
                        </Badge>
                        <Text fontSize="sm" color="gray.600">
                          {toolCall.duration_ms}ms
                        </Text>
                      </HStack>
                      <AccordionIcon />
                    </AccordionButton>
                  </h2>
                  <AccordionPanel pb={4}>
                    <VStack align="stretch" spacing={4}>
                      {/* Input Parameters */}
                      <Box>
                        <Text fontWeight="bold" mb={2}>
                          Input Parameters:
                        </Text>
                        <Code
                          display="block"
                          whiteSpace="pre"
                          p={3}
                          borderRadius="md"
                          bg={codeBgColor}
                          fontSize="sm"
                        >
                          {JSON.stringify(
                            toolCall.input_parameters,
                            null,
                            2
                          )}
                        </Code>
                      </Box>

                      <Divider />

                      {/* Output Result */}
                      <Box>
                        <Text fontWeight="bold" mb={2}>
                          Output Result:
                        </Text>
                        <Code
                          display="block"
                          whiteSpace="pre"
                          p={3}
                          borderRadius="md"
                          bg={codeBgColor}
                          fontSize="sm"
                        >
                          {JSON.stringify(toolCall.output_result, null, 2)}
                        </Code>
                      </Box>

                      {/* Error Message (if any) */}
                      {toolCall.error_message && (
                        <>
                          <Divider />
                          <Box>
                            <Text fontWeight="bold" mb={2} color="red.500">
                              Error:
                            </Text>
                            <Text color="red.600" fontSize="sm">
                              {toolCall.error_message}
                            </Text>
                          </Box>
                        </>
                      )}

                      {/* Performance */}
                      <Divider />
                      <HStack justify="space-between">
                        <Text fontSize="sm" color="gray.600">
                          Execution Time:
                        </Text>
                        <Badge>{toolCall.duration_ms}ms</Badge>
                      </HStack>
                    </VStack>
                  </AccordionPanel>
                </AccordionItem>
              ))}
            </Accordion>
          </CardBody>
        </Card>

        {/* Timeline */}
        <Card bg={bgColor} borderWidth="1px" borderColor={borderColor}>
          <CardHeader>
            <Heading size="md">Execution Timeline</Heading>
          </CardHeader>
          <CardBody>
            <VStack align="stretch" spacing={3}>
              <HStack justify="space-between">
                <Text fontWeight="bold">Started At</Text>
                <Text>{new Date(agentData.started_at).toLocaleString()}</Text>
              </HStack>
              <Divider />
              <HStack justify="space-between">
                <Text fontWeight="bold">Completed At</Text>
                <Text>
                  {agentData.completed_at
                    ? new Date(agentData.completed_at).toLocaleString()
                    : 'N/A'}
                </Text>
              </HStack>
              <Divider />
              <HStack justify="space-between">
                <Text fontWeight="bold">Total Duration</Text>
                <Text>
                  {agentData.duration_ms
                    ? `${(agentData.duration_ms / 1000).toFixed(2)}s`
                    : 'N/A'}
                </Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default AgentWorkflowPage;
