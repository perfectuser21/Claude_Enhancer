import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  HStack,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Button,
  Text,
  Code,
  Badge,
  useColorModeValue,
  IconButton,
  Flex,
  Divider,
} from '@chakra-ui/react';
import { FiSearch, FiRefreshCw, FiDownload, FiFilter } from 'react-icons/fi';
import { useWorkflowWebSocket } from '../../hooks/useWorkflowWebSocket';

interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  source: string;
  message: string;
  session_id?: string;
}

const LogViewerPage: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [autoScroll, setAutoScroll] = useState(true);

  const logsEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { isConnected, lastMessage } = useWorkflowWebSocket({ autoConnect: true });

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const logBgColor = useColorModeValue('gray.50', 'gray.900');

  // Mock initial logs (replace with API call)
  useEffect(() => {
    const mockLogs: LogEntry[] = [
      {
        timestamp: new Date().toISOString(),
        level: 'info',
        source: 'workflow',
        message: 'Starting Phase 0 (Discovery)',
      },
      {
        timestamp: new Date().toISOString(),
        level: 'info',
        source: 'agent',
        message: 'Launching backend-architect agent',
      },
      {
        timestamp: new Date().toISOString(),
        level: 'warning',
        source: 'hook',
        message: 'branch_helper.sh: Current branch is main, should create feature branch',
      },
      {
        timestamp: new Date().toISOString(),
        level: 'info',
        source: 'api',
        message: 'GET /api/v1/workflow/sessions - 200 OK (45ms)',
      },
    ];
    setLogs(mockLogs);
  }, []);

  // Handle WebSocket messages for real-time logs
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'log') {
      const newLog: LogEntry = {
        timestamp: new Date().toISOString(),
        level: lastMessage.data.level || 'info',
        source: lastMessage.data.source || 'system',
        message: lastMessage.data.message,
      };
      setLogs((prev) => [...prev, newLog]);
    }
  }, [lastMessage]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Filter logs
  useEffect(() => {
    let filtered = logs;

    // Level filter
    if (levelFilter !== 'all') {
      filtered = filtered.filter((log) => log.level === levelFilter);
    }

    // Source filter
    if (sourceFilter !== 'all') {
      filtered = filtered.filter((log) => log.source === sourceFilter);
    }

    // Search query
    if (searchQuery) {
      filtered = filtered.filter(
        (log) =>
          log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
          log.source.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredLogs(filtered);
  }, [logs, searchQuery, levelFilter, sourceFilter]);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'red';
      case 'warning':
        return 'orange';
      case 'debug':
        return 'gray';
      default:
        return 'blue';
    }
  };

  const handleExport = () => {
    const content = filteredLogs
      .map(
        (log) =>
          `[${log.timestamp}] [${log.level.toUpperCase()}] [${log.source}] ${log.message}`
      )
      .join('\n');

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleClear = () => {
    setLogs([]);
  };

  // Get unique sources for filter
  const uniqueSources = Array.from(new Set(logs.map((log) => log.source)));

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <VStack align="start" spacing={1}>
            <Heading size="lg">Log Viewer</Heading>
            <HStack>
              <Text fontSize="sm" color="gray.600">
                {filteredLogs.length} of {logs.length} logs
              </Text>
              {isConnected && (
                <Badge colorScheme="green" variant="subtle">
                  Live
                </Badge>
              )}
            </HStack>
          </VStack>

          <HStack spacing={2}>
            <Button
              leftIcon={<FiDownload />}
              size="sm"
              onClick={handleExport}
              isDisabled={filteredLogs.length === 0}
            >
              Export
            </Button>
            <Button
              leftIcon={<FiRefreshCw />}
              size="sm"
              onClick={handleClear}
              colorScheme="red"
              variant="outline"
            >
              Clear
            </Button>
          </HStack>
        </HStack>

        {/* Filters */}
        <Box
          p={4}
          bg={bgColor}
          borderWidth="1px"
          borderColor={borderColor}
          borderRadius="md"
        >
          <Flex gap={4} wrap="wrap">
            {/* Search */}
            <InputGroup flex="1" minW="200px">
              <InputLeftElement pointerEvents="none">
                <FiSearch color="gray" />
              </InputLeftElement>
              <Input
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </InputGroup>

            {/* Level Filter */}
            <Select
              w="150px"
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              icon={<FiFilter />}
            >
              <option value="all">All Levels</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="debug">Debug</option>
            </Select>

            {/* Source Filter */}
            <Select
              w="150px"
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              icon={<FiFilter />}
            >
              <option value="all">All Sources</option>
              {uniqueSources.map((source) => (
                <option key={source} value={source}>
                  {source}
                </option>
              ))}
            </Select>

            {/* Auto Scroll Toggle */}
            <Button
              size="sm"
              variant={autoScroll ? 'solid' : 'outline'}
              colorScheme={autoScroll ? 'blue' : 'gray'}
              onClick={() => setAutoScroll(!autoScroll)}
            >
              Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
            </Button>
          </Flex>
        </Box>

        {/* Log Entries */}
        <Box
          ref={containerRef}
          h="600px"
          overflowY="auto"
          bg={logBgColor}
          borderWidth="1px"
          borderColor={borderColor}
          borderRadius="md"
          p={4}
        >
          <VStack align="stretch" spacing={2}>
            {filteredLogs.length === 0 ? (
              <Text color="gray.500" textAlign="center" py={8}>
                No logs to display
              </Text>
            ) : (
              filteredLogs.map((log, index) => (
                <Box
                  key={index}
                  p={3}
                  bg={bgColor}
                  borderLeftWidth="4px"
                  borderLeftColor={`${getLevelColor(log.level)}.500`}
                  borderRadius="md"
                  fontSize="sm"
                  fontFamily="mono"
                >
                  <HStack spacing={3} wrap="wrap">
                    <Text color="gray.500" fontSize="xs" minW="150px">
                      {new Date(log.timestamp).toLocaleString()}
                    </Text>
                    <Badge colorScheme={getLevelColor(log.level)} fontSize="xs">
                      {log.level.toUpperCase()}
                    </Badge>
                    <Badge variant="outline" fontSize="xs">
                      {log.source}
                    </Badge>
                  </HStack>
                  <Text mt={2}>{log.message}</Text>
                </Box>
              ))
            )}
            <div ref={logsEndRef} />
          </VStack>
        </Box>

        {/* Stats */}
        <HStack justify="space-around" p={4} bg={bgColor} borderRadius="md">
          <VStack>
            <Text fontSize="2xl" fontWeight="bold" color="blue.500">
              {logs.filter((l) => l.level === 'info').length}
            </Text>
            <Text fontSize="sm" color="gray.600">
              Info
            </Text>
          </VStack>
          <Divider orientation="vertical" h="50px" />
          <VStack>
            <Text fontSize="2xl" fontWeight="bold" color="orange.500">
              {logs.filter((l) => l.level === 'warning').length}
            </Text>
            <Text fontSize="sm" color="gray.600">
              Warnings
            </Text>
          </VStack>
          <Divider orientation="vertical" h="50px" />
          <VStack>
            <Text fontSize="2xl" fontWeight="bold" color="red.500">
              {logs.filter((l) => l.level === 'error').length}
            </Text>
            <Text fontSize="sm" color="gray.600">
              Errors
            </Text>
          </VStack>
          <Divider orientation="vertical" h="50px" />
          <VStack>
            <Text fontSize="2xl" fontWeight="bold" color="gray.500">
              {logs.filter((l) => l.level === 'debug').length}
            </Text>
            <Text fontSize="sm" color="gray.600">
              Debug
            </Text>
          </VStack>
        </HStack>
      </VStack>
    </Container>
  );
};

export default LogViewerPage;
