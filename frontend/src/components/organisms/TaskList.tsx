import React, { useState, useMemo } from 'react';
import {
  VStack,
  HStack,
  Text,
  Select,
  Input,
  InputGroup,
  InputLeftElement,
  Box,
  Button,
  Flex,
  Badge,
  useColorModeValue,
  Skeleton,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from '@chakra-ui/react';
import { Search, Filter, Plus, ArrowUpDown } from 'lucide-react';
import { Task, TaskFilter, TaskSort, TaskListProps } from '../../types';
import { TaskCard } from '../molecules/TaskCard';
import { LoadingSpinner } from '../atoms';

interface TaskListState {
  searchTerm: string;
  statusFilter: string;
  priorityFilter: string;
  sortBy: string;
  sortDirection: 'asc' | 'desc';
}

export const TaskList: React.FC<TaskListProps> = ({
  tasks,
  loading = false,
  onTaskSelect,
  onTaskUpdate,
  onTaskDelete,
}) => {
  const [listState, setListState] = useState<TaskListState>({
    searchTerm: '',
    statusFilter: 'all',
    priorityFilter: 'all',
    sortBy: 'createdAt',
    sortDirection: 'desc',
  });

  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Filter and sort tasks
  const filteredAndSortedTasks = useMemo(() => {
    let result = [...tasks];

    // Apply search filter
    if (listState.searchTerm) {
      const searchLower = listState.searchTerm.toLowerCase();
      result = result.filter(
        (task) =>
          task.title.toLowerCase().includes(searchLower) ||
          task.description?.toLowerCase().includes(searchLower) ||
          task.tags.some((tag) => tag.toLowerCase().includes(searchLower))
      );
    }

    // Apply status filter
    if (listState.statusFilter !== 'all') {
      result = result.filter((task) => task.status === listState.statusFilter);
    }

    // Apply priority filter
    if (listState.priorityFilter !== 'all') {
      result = result.filter((task) => task.priority === listState.priorityFilter);
    }

    // Apply sorting
    result.sort((a, b) => {
      const aValue = a[listState.sortBy as keyof Task];
      const bValue = b[listState.sortBy as keyof Task];

      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;

      let comparison = 0;
      if (aValue < bValue) comparison = -1;
      if (aValue > bValue) comparison = 1;

      return listState.sortDirection === 'desc' ? -comparison : comparison;
    });

    return result;
  }, [tasks, listState]);

  const handleSearch = (value: string) => {
    setListState((prev) => ({ ...prev, searchTerm: value }));
  };

  const handleStatusFilter = (value: string) => {
    setListState((prev) => ({ ...prev, statusFilter: value }));
  };

  const handlePriorityFilter = (value: string) => {
    setListState((prev) => ({ ...prev, priorityFilter: value }));
  };

  const handleSort = (field: string) => {
    setListState((prev) => ({
      ...prev,
      sortBy: field,
      sortDirection:
        prev.sortBy === field && prev.sortDirection === 'asc' ? 'desc' : 'asc',
    }));
  };

  const handleTaskEdit = (task: Task) => {
    onTaskSelect?.(task);
  };

  const handleTaskDelete = (taskId: string) => {
    onTaskDelete?.(taskId);
  };

  const handleStatusChange = (taskId: string, newStatus: string) => {
    const task = tasks.find((t) => t.id === taskId);
    if (task) {
      onTaskUpdate?.(taskId, { status: newStatus as any });
    }
  };

  const clearFilters = () => {
    setListState({
      searchTerm: '',
      statusFilter: 'all',
      priorityFilter: 'all',
      sortBy: 'createdAt',
      sortDirection: 'desc',
    });
  };

  if (loading) {
    return (
      <Box p={6}>
        <VStack spacing={4}>
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} height="120px" borderRadius="lg" />
          ))}
        </VStack>
      </Box>
    );
  }

  return (
    <Box bg={bg} borderRadius="lg" border="1px solid" borderColor={borderColor} p={6}>
      {/* Header */}
      <Flex justify="space-between" align="center" mb={6}>
        <VStack align="start" spacing={1}>
          <Text fontSize="xl" fontWeight="600">
            Task List
          </Text>
          <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.400' }}>
            {filteredAndSortedTasks.length} of {tasks.length} tasks
          </Text>
        </VStack>
        <Button leftIcon={<Plus size={16} />} colorScheme="brand" size="sm">
          Add Task
        </Button>
      </Flex>

      {/* Filters */}
      <VStack spacing={4} mb={6}>
        <HStack spacing={4} w="full" flexWrap="wrap">
          {/* Search */}
          <InputGroup maxW="300px">
            <InputLeftElement>
              <Search size={16} />
            </InputLeftElement>
            <Input
              placeholder="Search tasks..."
              value={listState.searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              variant="filled"
            />
          </InputGroup>

          {/* Status Filter */}
          <Select
            value={listState.statusFilter}
            onChange={(e) => handleStatusFilter(e.target.value)}
            maxW="150px"
            variant="filled"
          >
            <option value="all">All Status</option>
            <option value="todo">To Do</option>
            <option value="in_progress">In Progress</option>
            <option value="review">Review</option>
            <option value="done">Done</option>
          </Select>

          {/* Priority Filter */}
          <Select
            value={listState.priorityFilter}
            onChange={(e) => handlePriorityFilter(e.target.value)}
            maxW="150px"
            variant="filled"
          >
            <option value="all">All Priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </Select>

          {/* Sort */}
          <Select
            value={listState.sortBy}
            onChange={(e) => handleSort(e.target.value)}
            maxW="150px"
            variant="filled"
          >
            <option value="createdAt">Created Date</option>
            <option value="updatedAt">Updated Date</option>
            <option value="dueDate">Due Date</option>
            <option value="priority">Priority</option>
            <option value="title">Title</option>
          </Select>

          <Button
            variant="ghost"
            size="sm"
            leftIcon={<ArrowUpDown size={16} />}
            onClick={() =>
              setListState((prev) => ({
                ...prev,
                sortDirection: prev.sortDirection === 'asc' ? 'desc' : 'asc',
              }))
            }
          >
            {listState.sortDirection === 'asc' ? 'Ascending' : 'Descending'}
          </Button>

          {/* Clear Filters */}
          {(listState.searchTerm ||
            listState.statusFilter !== 'all' ||
            listState.priorityFilter !== 'all') && (
            <Button variant="outline" size="sm" onClick={clearFilters}>
              Clear Filters
            </Button>
          )}
        </HStack>

        {/* Active Filters */}
        <HStack spacing={2} w="full" flexWrap="wrap">
          {listState.searchTerm && (
            <Badge colorScheme="blue">Search: {listState.searchTerm}</Badge>
          )}
          {listState.statusFilter !== 'all' && (
            <Badge colorScheme="green">Status: {listState.statusFilter}</Badge>
          )}
          {listState.priorityFilter !== 'all' && (
            <Badge colorScheme="orange">Priority: {listState.priorityFilter}</Badge>
          )}
        </HStack>
      </VStack>

      {/* Task List */}
      {filteredAndSortedTasks.length === 0 ? (
        <Alert status="info" borderRadius="lg">
          <AlertIcon />
          <Box>
            <AlertTitle>No tasks found</AlertTitle>
            <AlertDescription>
              {tasks.length === 0
                ? 'Start by creating your first task.'
                : 'Try adjusting your search or filter criteria.'}
            </AlertDescription>
          </Box>
        </Alert>
      ) : (
        <VStack spacing={4} align="stretch">
          {filteredAndSortedTasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onEdit={handleTaskEdit}
              onDelete={handleTaskDelete}
              onStatusChange={handleStatusChange}
            />
          ))}
        </VStack>
      )}
    </Box>
  );
};