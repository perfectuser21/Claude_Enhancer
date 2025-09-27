import React from 'react';
import {
  Box,
  Card,
  CardBody,
  Text,
  HStack,
  VStack,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useColorModeValue,
  Tooltip,
  Flex,
  Spacer,
} from '@chakra-ui/react';
import {
  MoreVertical,
  Edit,
  Trash2,
  Clock,
  Calendar,
  Tag,
  User,
} from 'lucide-react';
import { format } from 'date-fns';
import { Task, TaskCardProps } from '../../types';
import { PriorityBadge, StatusBadge, Avatar } from '../atoms';

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onEdit,
  onDelete,
  onStatusChange,
  isDragging = false,
}) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.800', 'white');
  const subtextColor = useColorModeValue('gray.600', 'gray.400');

  const handleEdit = () => {
    onEdit?.(task);
  };

  const handleDelete = () => {
    onDelete?.(task.id);
  };

  const handleStatusChange = (newStatus: string) => {
    onStatusChange?.(task.id, newStatus as any);
  };

  const isOverdue = task.dueDate && new Date(task.dueDate) < new Date() && task.status !== 'done';

  return (
    <Card
      variant="task"
      bg={cardBg}
      borderColor={isOverdue ? 'red.300' : borderColor}
      borderWidth={isOverdue ? '2px' : '1px'}
      opacity={isDragging ? 0.5 : 1}
      transform={isDragging ? 'rotate(5deg)' : 'none'}
      cursor="grab"
      _active={{ cursor: 'grabbing' }}
      transition="all 0.2s"
      _hover={{
        transform: isDragging ? 'rotate(5deg)' : 'translateY(-2px)',
        shadow: 'lg',
      }}
    >
      <CardBody p={4}>
        <VStack align="stretch" spacing={3}>
          {/* Header */}
          <Flex align="flex-start">
            <VStack align="stretch" flex="1" spacing={2}>
              <Text
                fontSize="md"
                fontWeight="600"
                color={textColor}
                lineHeight="1.2"
                noOfLines={2}
              >
                {task.title}
              </Text>
              {task.description && (
                <Text
                  fontSize="sm"
                  color={subtextColor}
                  noOfLines={3}
                  lineHeight="1.4"
                >
                  {task.description}
                </Text>
              )}
            </VStack>

            {/* Menu */}
            <Menu>
              <MenuButton
                as={IconButton}
                icon={<MoreVertical size={16} />}
                variant="ghost"
                size="sm"
                ml={2}
                aria-label="Task options"
              />
              <MenuList>
                <MenuItem icon={<Edit size={16} />} onClick={handleEdit}>
                  Edit Task
                </MenuItem>
                <MenuItem icon={<Trash2 size={16} />} onClick={handleDelete} color="red.500">
                  Delete Task
                </MenuItem>
                {task.status !== 'todo' && (
                  <MenuItem onClick={() => handleStatusChange('todo')}>
                    Move to To Do
                  </MenuItem>
                )}
                {task.status !== 'in_progress' && (
                  <MenuItem onClick={() => handleStatusChange('in_progress')}>
                    Move to In Progress
                  </MenuItem>
                )}
                {task.status !== 'review' && (
                  <MenuItem onClick={() => handleStatusChange('review')}>
                    Move to Review
                  </MenuItem>
                )}
                {task.status !== 'done' && (
                  <MenuItem onClick={() => handleStatusChange('done')}>
                    Move to Done
                  </MenuItem>
                )}
              </MenuList>
            </Menu>
          </Flex>

          {/* Tags */}
          {task.tags.length > 0 && (
            <HStack spacing={1} flexWrap="wrap">
              <Tag size={12} color={subtextColor} />
              {task.tags.slice(0, 3).map((tag, index) => (
                <Text
                  key={index}
                  fontSize="xs"
                  color="blue.500"
                  bg="blue.50"
                  _dark={{ bg: 'blue.900', color: 'blue.200' }}
                  px={2}
                  py={1}
                  borderRadius="full"
                >
                  #{tag}
                </Text>
              ))}
              {task.tags.length > 3 && (
                <Text fontSize="xs" color={subtextColor}>
                  +{task.tags.length - 3} more
                </Text>
              )}
            </HStack>
          )}

          {/* Metadata */}
          <VStack spacing={2} align="stretch">
            {/* Priority and Status */}
            <HStack spacing={2}>
              <PriorityBadge priority={task.priority} />
              <StatusBadge status={task.status} />
              <Spacer />
              {task.assignee && (
                <Tooltip label={`Assigned to ${task.assignee.firstName} ${task.assignee.lastName}`}>
                  <Box>
                    <Avatar user={task.assignee} size="sm" />
                  </Box>
                </Tooltip>
              )}
            </HStack>

            {/* Due Date and Time Info */}
            <HStack spacing={3} fontSize="xs" color={subtextColor}>
              {task.dueDate && (
                <HStack spacing={1}>
                  <Calendar size={12} />
                  <Text color={isOverdue ? 'red.500' : subtextColor}>
                    {format(new Date(task.dueDate), 'MMM dd')}
                  </Text>
                </HStack>
              )}

              {task.estimatedHours && (
                <HStack spacing={1}>
                  <Clock size={12} />
                  <Text>{task.estimatedHours}h</Text>
                </HStack>
              )}

              {task.project && (
                <HStack spacing={1}>
                  <Box
                    w={3}
                    h={3}
                    borderRadius="full"
                    bg={task.project.color}
                  />
                  <Text noOfLines={1} maxW="100px">
                    {task.project.name}
                  </Text>
                </HStack>
              )}
            </HStack>
          </VStack>

          {/* Progress indicator for In Progress tasks */}
          {task.status === 'in_progress' && task.estimatedHours && task.actualHours && (
            <Box>
              <HStack justify="space-between" fontSize="xs" color={subtextColor} mb={1}>
                <Text>Progress</Text>
                <Text>
                  {Math.round((task.actualHours / task.estimatedHours) * 100)}%
                </Text>
              </HStack>
              <Box bg="gray.200" _dark={{ bg: 'gray.600' }} borderRadius="full" h={2}>
                <Box
                  bg="blue.500"
                  h="100%"
                  borderRadius="full"
                  w={`${Math.min((task.actualHours / task.estimatedHours) * 100, 100)}%`}
                  transition="width 0.3s"
                />
              </Box>
            </Box>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};