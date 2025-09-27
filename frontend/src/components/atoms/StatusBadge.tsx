import React from 'react';
import { Badge, BadgeProps } from '@chakra-ui/react';
import { TaskStatus } from '../../types';
import { getTaskStatusColor } from '../../theme';

interface StatusBadgeProps extends Omit<BadgeProps, 'variant'> {
  status: TaskStatus;
  variant?: 'subtle' | 'solid' | 'outline';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant = 'subtle',
  ...props
}) => {
  const statusLabels: Record<TaskStatus, string> = {
    todo: 'To Do',
    in_progress: 'In Progress',
    review: 'Review',
    done: 'Done',
  };

  return (
    <Badge
      variant={variant}
      colorScheme={getTaskStatusColor(status)}
      fontSize="xs"
      fontWeight="600"
      px={2}
      py={1}
      borderRadius="full"
      {...props}
    >
      {statusLabels[status]}
    </Badge>
  );
};