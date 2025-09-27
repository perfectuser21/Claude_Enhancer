import React, { useCallback, useState } from 'react';
import {
  Box,
  HStack,
  VStack,
  Text,
  Badge,
  Button,
  useColorModeValue,
  Alert,
  AlertIcon,
  AlertDescription,
  Skeleton,
  Card,
  CardBody,
} from '@chakra-ui/react';
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd';
import { Plus } from 'lucide-react';
import { Task, TaskStatus, KanbanColumn, KanbanColumnProps } from '../../types';
import { TaskCard } from '../molecules/TaskCard';
import { getTaskStatusColor } from '../../theme';

interface KanbanBoardProps {
  tasks: Task[];
  columns: KanbanColumn[];
  loading?: boolean;
  onTaskMove?: (taskId: string, newStatus: TaskStatus) => void;
  onTaskEdit?: (task: Task) => void;
  onTaskDelete?: (taskId: string) => void;
  onAddTask?: (status: TaskStatus) => void;
}

interface KanbanColumnComponentProps extends KanbanColumnProps {
  onAddTask?: (status: TaskStatus) => void;
  onTaskEdit?: (task: Task) => void;
  onTaskDelete?: (taskId: string) => void;
}

const KanbanColumnComponent: React.FC<KanbanColumnComponentProps> = ({
  column,
  tasks,
  onTaskMove,
  onAddTask,
  onTaskEdit,
  onTaskDelete,
}) => {
  const bg = useColorModeValue('gray.50', 'gray.700');
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const handleAddTask = () => {
    onAddTask?.(column.status);
  };

  const isOverLimit = column.limit && tasks.length > column.limit;

  return (
    <Card variant="kanban" bg={bg} minW="300px" flex="1">
      <CardBody>
        <VStack spacing={4} align="stretch" h="full">
          {/* Column Header */}
          <HStack justify="space-between" align="center">
            <HStack spacing={2}>
              <Box
                w={3}
                h={3}
                borderRadius="full"
                bg={column.color}
              />
              <Text fontSize="md" fontWeight="600" color="gray.700" _dark={{ color: 'gray.200' }}>
                {column.title}
              </Text>
              <Badge
                colorScheme={getTaskStatusColor(column.status)}
                variant="subtle"
                borderRadius="full"
              >
                {tasks.length}
                {column.limit && `/${column.limit}`}
              </Badge>
            </HStack>
            <Button
              size="sm"
              variant="ghost"
              leftIcon={<Plus size={14} />}
              onClick={handleAddTask}
            >
              Add
            </Button>
          </HStack>

          {/* Limit Warning */}
          {isOverLimit && (
            <Alert status="warning" size="sm" borderRadius="md">
              <AlertIcon />
              <AlertDescription fontSize="sm">
                Column limit exceeded ({tasks.length}/{column.limit})
              </AlertDescription>
            </Alert>
          )}

          {/* Droppable Area */}
          <Droppable droppableId={column.id}>
            {(provided, snapshot) => (
              <Box
                ref={provided.innerRef}
                {...provided.droppableProps}
                minH="400px"
                bg={snapshot.isDraggingOver ? 'blue.50' : 'transparent'}
                _dark={{
                  bg: snapshot.isDraggingOver ? 'blue.900' : 'transparent',
                }}
                borderRadius="md"
                transition="background-color 0.2s"
                p={2}
              >
                <VStack spacing={3} align="stretch">
                  {tasks.map((task, index) => (
                    <Draggable key={task.id} draggableId={task.id} index={index}>
                      {(provided, snapshot) => (
                        <Box
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                        >
                          <TaskCard
                            task={task}
                            isDragging={snapshot.isDragging}
                            onEdit={onTaskEdit}
                            onDelete={onTaskDelete}
                          />
                        </Box>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </VStack>

                {/* Empty State */}
                {tasks.length === 0 && (
                  <Box
                    textAlign="center"
                    py={8}
                    color="gray.500"
                    _dark={{ color: 'gray.400' }}
                  >
                    <Text fontSize="sm">
                      {column.status === 'todo' && 'No tasks to do'}
                      {column.status === 'in_progress' && 'No tasks in progress'}
                      {column.status === 'review' && 'No tasks in review'}
                      {column.status === 'done' && 'No completed tasks'}
                    </Text>
                    <Button
                      variant="ghost"
                      size="sm"
                      leftIcon={<Plus size={14} />}
                      mt={2}
                      onClick={handleAddTask}
                    >
                      Add first task
                    </Button>
                  </Box>
                )}
              </Box>
            )}
          </Droppable>
        </VStack>
      </CardBody>
    </Card>
  );
};

export const KanbanBoard: React.FC<KanbanBoardProps> = ({
  tasks,
  columns,
  loading = false,
  onTaskMove,
  onTaskEdit,
  onTaskDelete,
  onAddTask,
}) => {
  const [draggedTaskId, setDraggedTaskId] = useState<string | null>(null);

  // Group tasks by status
  const tasksByStatus = React.useMemo(() => {
    const grouped: Record<string, Task[]> = {};

    columns.forEach((column) => {
      grouped[column.id] = tasks.filter((task) => task.status === column.status);
    });

    return grouped;
  }, [tasks, columns]);

  const handleDragStart = useCallback((start: any) => {
    setDraggedTaskId(start.draggableId);
  }, []);

  const handleDragEnd = useCallback(
    (result: DropResult) => {
      setDraggedTaskId(null);

      const { destination, source, draggableId } = result;

      // Dropped outside of any droppable
      if (!destination) {
        return;
      }

      // Dropped in the same position
      if (
        destination.droppableId === source.droppableId &&
        destination.index === source.index
      ) {
        return;
      }

      // Find the destination column and its status
      const destinationColumn = columns.find((col) => col.id === destination.droppableId);
      if (!destinationColumn) {
        return;
      }

      // Move the task
      onTaskMove?.(draggableId, destinationColumn.status);
    },
    [columns, onTaskMove]
  );

  if (loading) {
    return (
      <HStack spacing={6} align="stretch" h="600px" overflowX="auto" p={6}>
        {[...Array(4)].map((_, i) => (
          <Box key={i} minW="300px" flex="1">
            <Skeleton height="100%" borderRadius="lg" />
          </Box>
        ))}
      </HStack>
    );
  }

  return (
    <DragDropContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <Box overflowX="auto" pb={4}>
        <HStack spacing={6} align="stretch" minH="600px" p={6}>
          {columns.map((column) => (
            <KanbanColumnComponent
              key={column.id}
              column={column}
              tasks={tasksByStatus[column.id] || []}
              onTaskMove={onTaskMove}
              onAddTask={onAddTask}
              onTaskEdit={onTaskEdit}
              onTaskDelete={onTaskDelete}
            />
          ))}
        </HStack>
      </Box>
    </DragDropContext>
  );
};