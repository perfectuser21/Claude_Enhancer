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
  CardBody,
  SimpleGrid,
  Progress,
  useColorModeValue,
  Icon,
  Tooltip,
  Flex,
  Circle,
  Divider,
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import {
  FiActivity,
  FiCpu,
  FiZap,
  FiHeart,
  FiTrendingUp,
  FiShield,
  FiCode,
  FiDatabase,
  FiUsers,
} from 'react-icons/fi';

/**
 * 系统生命体监控台
 * ==================
 *
 * 可视化Claude Enhancer系统为一个有机生命体：
 * - 大脑：Phase执行中心
 * - 血管：数据流和WebSocket
 * - 神经：Agent网络
 * - 心跳：实时健康指标
 */

interface SystemHealth {
  overall: 'healthy' | 'warning' | 'critical';
  score: number;
}

interface Organ {
  name: string;
  icon: any;
  health: 'healthy' | 'warning' | 'critical';
  metrics: { label: string; value: string | number }[];
  path: string;
  description: string;
}

const SystemLifeDashboard: React.FC = () => {
  const [systemHealth, setSystemHealth] = useState<SystemHealth>({
    overall: 'healthy',
    score: 95,
  });

  const [heartbeat, setHeartbeat] = useState(0);
  const [dataFlow, setDataFlow] = useState(0);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // 模拟心跳动画
  useEffect(() => {
    const interval = setInterval(() => {
      setHeartbeat((prev) => (prev + 1) % 100);
      setDataFlow((prev) => (prev + 5) % 100);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // 系统"器官"定义
  const organs: Organ[] = [
    {
      name: '大脑 - Phase执行中心',
      icon: FiCpu,
      health: 'healthy',
      metrics: [
        { label: '当前Phase', value: 'Phase 2 实现' },
        { label: '完成度', value: '67%' },
        { label: '执行时间', value: '12分35秒' },
      ],
      path: '/workflow/phases/current',
      description: '系统的决策中心，控制整个工作流的执行',
    },
    {
      name: '神经网络 - Agent系统',
      icon: FiUsers,
      health: 'healthy',
      metrics: [
        { label: '活跃Agents', value: 5 },
        { label: '总调用次数', value: 142 },
        { label: '平均响应', value: '1.2s' },
      ],
      path: '/workflow/agents/current',
      description: '分布式任务执行单元，并行处理开发任务',
    },
    {
      name: '血管 - 数据流',
      icon: FiActivity,
      health: 'healthy',
      metrics: [
        { label: 'WebSocket', value: '已连接' },
        { label: '实时日志', value: '235条/分' },
        { label: '数据吞吐', value: '1.2MB/s' },
      ],
      path: '/workflow/logs',
      description: '实时数据传输通道，连接所有系统组件',
    },
    {
      name: '免疫系统 - Quality Gates',
      icon: FiShield,
      health: 'healthy',
      metrics: [
        { label: 'Phase 3测试', value: '通过 ✓' },
        { label: 'Phase 4审查', value: '进行中' },
        { label: '问题检测', value: '0个阻塞' },
      ],
      path: '/workflow/quality-gates',
      description: '质量保障系统，防止有缺陷的代码进入主干',
    },
    {
      name: '循环系统 - 性能监控',
      icon: FiTrendingUp,
      health: 'warning',
      metrics: [
        { label: 'API响应', value: '125ms' },
        { label: 'WebSocket延迟', value: '45ms' },
        { label: '数据库查询', value: '89ms' },
      ],
      path: '/workflow/performance',
      description: '90+性能指标实时监控，确保系统健康运行',
    },
    {
      name: '存储器官 - 数据库',
      icon: FiDatabase,
      health: 'healthy',
      metrics: [
        { label: 'Workflow Sessions', value: 23 },
        { label: 'Agent执行记录', value: 456 },
        { label: '存储使用', value: '234MB' },
      ],
      path: '/workflow/sessions',
      description: '持久化存储所有工作流历史和状态',
    },
  ];

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy':
        return 'green';
      case 'warning':
        return 'orange';
      case 'critical':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getOverallHealthColor = () => {
    if (systemHealth.score >= 80) return 'green';
    if (systemHealth.score >= 60) return 'orange';
    return 'red';
  };

  return (
    <Box minH="100vh" bg={bgColor}>
      <Container maxW="container.xl" py={8}>
        <VStack spacing={8} align="stretch">
          {/* 系统总览 - 生命体征 */}
          <Card bg={cardBg} borderWidth="2px" borderColor={`${getOverallHealthColor()}.400`}>
            <CardBody>
              <VStack spacing={6}>
                {/* 标题 */}
                <HStack justify="space-between" w="100%">
                  <VStack align="start" spacing={1}>
                    <Heading size="lg">🧬 Claude Enhancer 系统生命体</Heading>
                    <Text color="gray.600" fontSize="md">
                      实时监控系统的每个"器官"，像观察一个活生生的有机体
                    </Text>
                  </VStack>
                  <VStack align="end">
                    <Badge
                      colorScheme={getOverallHealthColor()}
                      fontSize="lg"
                      px={4}
                      py={2}
                      borderRadius="full"
                    >
                      {systemHealth.overall.toUpperCase()}
                    </Badge>
                    <Text fontSize="2xl" fontWeight="bold" color={`${getOverallHealthColor()}.500`}>
                      健康度: {systemHealth.score}/100
                    </Text>
                  </VStack>
                </HStack>

                <Divider />

                {/* 心跳和数据流动画 */}
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} w="100%">
                  <Card bg={useColorModeValue('green.50', 'green.900')} borderWidth="1px">
                    <CardBody>
                      <HStack spacing={4}>
                        <Icon as={FiHeart} boxSize={8} color="green.500" />
                        <VStack align="start" spacing={1} flex={1}>
                          <Text fontWeight="bold" fontSize="lg">
                            系统心跳
                          </Text>
                          <Progress
                            value={heartbeat}
                            size="sm"
                            colorScheme="green"
                            w="100%"
                            borderRadius="full"
                            hasStripe
                            isAnimated
                          />
                          <Text fontSize="sm" color="gray.600">
                            每秒1次，运行正常
                          </Text>
                        </VStack>
                      </HStack>
                    </CardBody>
                  </Card>

                  <Card bg={useColorModeValue('blue.50', 'blue.900')} borderWidth="1px">
                    <CardBody>
                      <HStack spacing={4}>
                        <Icon as={FiZap} boxSize={8} color="blue.500" />
                        <VStack align="start" spacing={1} flex={1}>
                          <Text fontWeight="bold" fontSize="lg">
                            数据流动
                          </Text>
                          <Progress
                            value={dataFlow}
                            size="sm"
                            colorScheme="blue"
                            w="100%"
                            borderRadius="full"
                            hasStripe
                            isAnimated
                          />
                          <Text fontSize="sm" color="gray.600">
                            WebSocket实时传输
                          </Text>
                        </VStack>
                      </HStack>
                    </CardBody>
                  </Card>
                </SimpleGrid>
              </VStack>
            </CardBody>
          </Card>

          {/* 系统器官网格 - 可点击深入 */}
          <Box>
            <Heading size="md" mb={4}>
              🫀 系统器官监控（点击深入查看）
            </Heading>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
              {organs.map((organ, index) => (
                <Card
                  key={index}
                  as={RouterLink}
                  to={organ.path}
                  bg={cardBg}
                  borderWidth="2px"
                  borderColor={`${getHealthColor(organ.health)}.400`}
                  transition="all 0.3s"
                  _hover={{
                    transform: 'translateY(-8px)',
                    boxShadow: '2xl',
                    borderColor: `${getHealthColor(organ.health)}.600`,
                  }}
                  cursor="pointer"
                  position="relative"
                  overflow="hidden"
                >
                  {/* 健康状态指示器 */}
                  <Circle
                    size="12px"
                    bg={`${getHealthColor(organ.health)}.500`}
                    position="absolute"
                    top={4}
                    right={4}
                    boxShadow={`0 0 10px ${getHealthColor(organ.health)}.500`}
                  />

                  <CardBody>
                    <VStack align="start" spacing={4}>
                      {/* 器官图标和名称 */}
                      <HStack spacing={3}>
                        <Icon
                          as={organ.icon}
                          boxSize={8}
                          color={`${getHealthColor(organ.health)}.500`}
                        />
                        <VStack align="start" spacing={0}>
                          <Text fontWeight="bold" fontSize="lg">
                            {organ.name}
                          </Text>
                          <Badge colorScheme={getHealthColor(organ.health)} fontSize="xs">
                            {organ.health}
                          </Badge>
                        </VStack>
                      </HStack>

                      {/* 描述 */}
                      <Text fontSize="sm" color="gray.600" noOfLines={2}>
                        {organ.description}
                      </Text>

                      <Divider />

                      {/* 关键指标 */}
                      <VStack align="start" spacing={2} w="100%">
                        {organ.metrics.map((metric, idx) => (
                          <HStack key={idx} justify="space-between" w="100%">
                            <Text fontSize="sm" color="gray.600">
                              {metric.label}:
                            </Text>
                            <Text fontSize="sm" fontWeight="bold">
                              {metric.value}
                            </Text>
                          </HStack>
                        ))}
                      </VStack>

                      {/* 查看详情提示 */}
                      <Text fontSize="xs" color="blue.500" fontWeight="600" textAlign="center" w="100%">
                        点击查看详细信息 →
                      </Text>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          </Box>

          {/* 系统连接图（简化版） */}
          <Card bg={cardBg}>
            <CardBody>
              <VStack spacing={4}>
                <Heading size="md">🔗 系统连接拓扑</Heading>
                <Text fontSize="sm" color="gray.600">
                  展示各个器官之间的连接关系（实时数据流动）
                </Text>
                <Box
                  p={8}
                  bg={useColorModeValue('gray.100', 'gray.700')}
                  borderRadius="lg"
                  w="100%"
                  textAlign="center"
                >
                  <Text fontSize="3xl" mb={2}>
                    🧠 → 🧬 → 🩸 → 🫀 → 💉
                  </Text>
                  <Text fontSize="sm" color="gray.600">
                    Phase中心 → Agent网络 → 数据流 → Quality Gates → Performance
                  </Text>
                  <Text fontSize="xs" color="gray.500" mt={4}>
                    （后续可以添加交互式D3.js网络图）
                  </Text>
                </Box>
              </VStack>
            </CardBody>
          </Card>

          {/* 快速统计 */}
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            <Card bg={cardBg} borderLeftWidth="4px" borderLeftColor="blue.500">
              <CardBody>
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.600">
                    当前Phase
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold">
                    Phase 2
                  </Text>
                  <Text fontSize="xs" color="blue.500">
                    实现阶段
                  </Text>
                </VStack>
              </CardBody>
            </Card>

            <Card bg={cardBg} borderLeftWidth="4px" borderLeftColor="green.500">
              <CardBody>
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.600">
                    活跃Agents
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold" color="green.500">
                    5/8
                  </Text>
                  <Text fontSize="xs" color="green.500">
                    运行中
                  </Text>
                </VStack>
              </CardBody>
            </Card>

            <Card bg={cardBg} borderLeftWidth="4px" borderLeftColor="purple.500">
              <CardBody>
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.600">
                    实时日志
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold" color="purple.500">
                    1,234
                  </Text>
                  <Text fontSize="xs" color="purple.500">
                    条消息
                  </Text>
                </VStack>
              </CardBody>
            </Card>

            <Card bg={cardBg} borderLeftWidth="4px" borderLeftColor="orange.500">
              <CardBody>
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.600">
                    系统负载
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold" color="orange.500">
                    45%
                  </Text>
                  <Text fontSize="xs" color="orange.500">
                    正常范围
                  </Text>
                </VStack>
              </CardBody>
            </Card>
          </SimpleGrid>
        </VStack>
      </Container>
    </Box>
  );
};

export default SystemLifeDashboard;
