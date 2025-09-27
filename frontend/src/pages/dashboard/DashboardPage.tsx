import React, { useState } from 'react';
import {
  Box,
  Container,
  HStack,
  VStack,
  Text,
  Button,
  ButtonGroup,
  Card,
  CardBody,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  useColorModeValue,
  Heading,
  Flex,
  Spacer,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Badge,
} from '@chakra-ui/react';
import {
  LayoutGrid,
  List,
  Calendar,
  Timeline,
  Plus,
  Settings,
  Filter,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { KanbanBoard, TaskList } from '../../components/organisms';
import { LoadingSpinner } from '../../components/atoms';
import { useTasks, useKanban } from '../../hooks';
import { useUIStore } from '../../store';
import { ViewType, TaskStatus } from '../../types';

export const DashboardPage: React.FC = () => {
  const { currentView, setCurrentView } = useUIStore();
  const { tasks, loading, error, createTask } = useTasks();
  const { columns, moveTask } = useKanban();

  const bg = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');

  // Calculate statistics
  const stats = React.useMemo(() => {
    const total = tasks.length;
    const completed = tasks.filter(task => task.status === 'done').length;
    const inProgress = tasks.filter(task => task.status === 'in_progress').length;
    const overdue = tasks.filter(task =>
      task.dueDate &&
      new Date(task.dueDate) < new Date() &&
      task.status !== 'done'
    ).length;

    const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;

    return {
      total,
      completed,
      inProgress,
      overdue,
      completionRate,
    };
  }, [tasks]);

  const handleViewChange = (view: ViewType) => {
    setCurrentView(view);
  };

  const handleTaskMove = async (taskId: string, newStatus: TaskStatus) => {
    await moveTask(taskId, newStatus);
  };

  const handleAddTask = (status?: TaskStatus) => {
    // This would typically open a task creation modal
    console.log('Add task with status:', status);
  };

  const viewIcons = {
    kanban: LayoutGrid,
    list: List,
    calendar: Calendar,
    timeline: Timeline,
  };

  const viewLabels = {
    kanban: 'Kanban',
    list: 'List',
    calendar: 'Calendar',
    timeline: 'Timeline',
  };

  if (loading && tasks.length === 0) {
    return <LoadingSpinner fullScreen message="Loading your dashboard..." />;
  }

  return (
    <Box minH="100vh" bg={bg}>
      <Container maxW="7xl" py={6}>
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <Flex align="center" gap={4}>
            <VStack align="start" spacing={1}>
              <Heading size="lg">Dashboard</Heading>
              <Text color="gray.600" _dark={{ color: 'gray.400' }}>
                Overview of your tasks and projects
              </Text>
            </VStack>
            <Spacer />
            <HStack spacing={3}>
              <Menu>
                <MenuButton
                  as={IconButton}
                  icon={<Filter size={18} />}
                  variant="outline"
                  aria-label="Filter tasks"
                />
                <MenuList>
                  <MenuItem>All Tasks</MenuItem>
                  <MenuItem>My Tasks</MenuItem>
                  <MenuItem>High Priority</MenuItem>
                  <MenuItem>Overdue</MenuItem>
                </MenuList>
              </Menu>
              <IconButton
                icon={<Settings size={18} />}
                variant="outline"
                aria-label="Settings"
              />
              <Button
                leftIcon={<Plus size={18} />}
                colorScheme="brand"
                onClick={() => handleAddTask()}
              >
                New Task
              </Button>
            </HStack>
          </Flex>

          {/* Statistics */}
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel>Total Tasks</StatLabel>
                  <StatNumber color="brand.500">{stats.total}</StatNumber>
                  <StatHelpText>
                    <HStack spacing={1}>
                      <TrendingUp size={14} />
                      <Text>Active projects</Text>
                    </HStack>
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>

            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel>Completed</StatLabel>
                  <StatNumber color="green.500">{stats.completed}</StatNumber>
                  <StatHelpText>
                    <HStack spacing={1}>
                      <CheckCircle size={14} />
                      <Text>{stats.completionRate}% completion rate</Text>
                    </HStack>
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>

            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel>In Progress</StatLabel>
                  <StatNumber color="blue.500">{stats.inProgress}</StatNumber>
                  <StatHelpText>
                    <HStack spacing={1}>
                      <Clock size={14} />
                      <Text>Currently working</Text>
                    </HStack>
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>

            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel>Overdue</StatLabel>
                  <StatNumber color={stats.overdue > 0 ? "red.500" : "gray.500"}>
                    {stats.overdue}
                  </StatNumber>
                  <StatHelpText>
                    <HStack spacing={1}>
                      <AlertCircle size={14} />
                      <Text>Need attention</Text>
                      {stats.overdue > 0 && (
                        <Badge colorScheme="red" ml={1}>
                          Action needed
                        </Badge>
                      )}
                    </HStack>
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </SimpleGrid>

          {/* View Selector */}
          <Card bg={cardBg}>
            <CardBody>
              <Flex align="center" gap={4}>
                <Text fontWeight="600">View:</Text>
                <ButtonGroup size="sm" variant="outline" spacing={0}>
                  {Object.entries(viewLabels).map(([view, label]) => {
                    const Icon = viewIcons[view as ViewType];
                    const isActive = currentView === view;

                    return (
                      <Button
                        key={view}
                        leftIcon={<Icon size={16} />}
                        variant={isActive ? 'solid' : 'outline'}
                        colorScheme={isActive ? 'brand' : 'gray'}
                        onClick={() => handleViewChange(view as ViewType)}
                        borderRadius={0}
                        _first={{ borderLeftRadius: 'md' }}
                        _last={{ borderRightRadius: 'md' }}
                      >
                        {label}
                      </Button>
                    );
                  })}
                </ButtonGroup>
                <Spacer />
                <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.400' }}>
                  {tasks.length} tasks total
                </Text>
              </Flex>
            </CardBody>
          </Card>

          {/* Main Content */}
          <Box>
            {currentView === 'kanban' && (
              <KanbanBoard
                tasks={tasks}
                columns={columns}
                loading={loading}
                onTaskMove={handleTaskMove}
                onAddTask={handleAddTask}
              />
            )}

            {currentView === 'list' && (
              <TaskList
                tasks={tasks}
                loading={loading}
                onTaskUpdate={(id, updates) => {
                  // Handle task update
                  console.log('Update task:', id, updates);
                }}
                onTaskDelete={(id) => {
                  // Handle task deletion
                  console.log('Delete task:', id);
                }}
              />
            )}

            {currentView === 'calendar' && (
              <Card bg={cardBg}>
                <CardBody textAlign="center" py={12}>
                  <Calendar size={48} color="gray" style={{ margin: '0 auto 16px' }} />
                  <Text fontSize="lg" fontWeight="600" color="gray.600">
                    Calendar View
                  </Text>
                  <Text color="gray.500" mt={2}>
                    Calendar view is coming soon! Stay tuned for updates.
                  </Text>
                </CardBody>
              </Card>
            )}

            {currentView === 'timeline' && (
              <Card bg={cardBg}>
                <CardBody textAlign="center" py={12}>
                  <Timeline size={48} color="gray" style={{ margin: '0 auto 16px' }} />
                  <Text fontSize="lg" fontWeight="600" color="gray.600">
                    Timeline View
                  </Text>
                  <Text color="gray.500" mt={2}>
                    Timeline view is coming soon! Stay tuned for updates.
                  </Text>
                </CardBody>
              </Card>
            )}
          </Box>

          {/* Error State */}
          {error && (
            <Card bg="red.50" _dark={{ bg: 'red.900' }} borderColor="red.200" _dark={{ borderColor: 'red.700' }}>
              <CardBody>
                <HStack spacing={3}>
                  <AlertCircle size={20} color="red" />
                  <VStack align="start" spacing={1}>
                    <Text fontWeight="600" color="red.700" _dark={{ color: 'red.200' }}>
                      Error Loading Tasks
                    </Text>
                    <Text fontSize="sm" color="red.600" _dark={{ color: 'red.300' }}>
                      {error}
                    </Text>
                  </VStack>
                </HStack>
              </CardBody>
            </Card>
          )}
        </VStack>
      </Container>
    </Box>
  );
};