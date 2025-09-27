import React from 'react';
import { Badge, BadgeProps } from '@chakra-ui/react';
import { TaskPriority } from '../../types';
import { getPriorityColor } from '../../theme';

interface PriorityBadgeProps extends Omit<BadgeProps, 'variant'> {
  priority: TaskPriority;
  variant?: 'subtle' | 'solid' | 'outline';
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({
  priority,
  variant = 'subtle',
  ...props
}) => {
  const priorityLabels: Record<TaskPriority, string> = {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
    urgent: 'Urgent',
  };

  return (
    <Badge
      variant={variant}
      colorScheme={getPriorityColor(priority)}
      fontSize="xs"
      fontWeight="600"
      px={2}
      py={1}
      borderRadius="full"
      {...props}
    >
      {priorityLabels[priority]}
    </Badge>
  );
};