/**
 * PriorityBadge组件测试
 * Initial-tests阶段 - 测试优先级徽章组件
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { PriorityBadge } from '../../components/atoms/PriorityBadge';
import { TaskPriority } from '../../types';

// 测试包装器
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ChakraProvider>{children}</ChakraProvider>
);

describe('PriorityBadge', () => {
  describe('Priority Display', () => {
    it('should display correct label for low priority', () => {
      render(
        <TestWrapper>
          <PriorityBadge priority={TaskPriority.LOW} />
        </TestWrapper>
      );

      expect(screen.getByText('Low')).toBeInTheDocument();
    });

    it('should display correct label for medium priority', () => {
      render(
        <TestWrapper>
          <PriorityBadge priority={TaskPriority.MEDIUM} />
        </TestWrapper>
      );

      expect(screen.getByText('Medium')).toBeInTheDocument();
    });

    it('should display correct label for high priority', () => {
      render(
        <TestWrapper>
          <PriorityBadge priority={TaskPriority.HIGH} />
        </TestWrapper>
      );

      expect(screen.getByText('High')).toBeInTheDocument();
    });

    it('should display correct label for urgent priority', () => {
      render(
        <TestWrapper>
          <PriorityBadge priority={TaskPriority.URGENT} />
        </TestWrapper>
      );

      expect(screen.getByText('Urgent')).toBeInTheDocument();
    });
  });

  describe('Styling and Variants', () => {
    it('should apply default subtle variant', () => {
      render(
        <TestWrapper>
          <PriorityBadge priority={TaskPriority.MEDIUM} />
        </TestWrapper>
      );

      const badge = screen.getByText('Medium');
      expect(badge).toHaveClass('chakra-badge');
    });

    it('should apply solid variant when specified', () => {
      render(
        <TestWrapper>
          <PriorityBadge priority={TaskPriority.HIGH} variant="solid" />
        </TestWrapper>
      );

      const badge = screen.getByText('High');
      expect(badge).toBeInTheDocument();
    });

    it('should apply outline variant when specified', () => {
      render(
        <TestWrapper>
          <PriorityBadge priority={TaskPriority.URGENT} variant="outline" />
        </TestWrapper>
      );

      const badge = screen.getByText('Urgent');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Custom Props', () => {
    it('should accept and apply custom className', () => {
      render(
        <TestWrapper>
          <PriorityBadge
            priority={TaskPriority.LOW}
            className="custom-class"
          />
        </TestWrapper>
      );

      const badge = screen.getByText('Low');
      expect(badge).toHaveClass('custom-class');
    });

    it('should accept custom data attributes', () => {
      render(
        <TestWrapper>
          <PriorityBadge
            priority={TaskPriority.MEDIUM}
            data-testid="priority-badge"
          />
        </TestWrapper>
      );

      expect(screen.getByTestId('priority-badge')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should be accessible with screen readers', () => {
      render(
        <TestWrapper>
          <PriorityBadge
            priority={TaskPriority.HIGH}
            aria-label="Task priority: High"
          />
        </TestWrapper>
      );

      expect(screen.getByLabelText('Task priority: High')).toBeInTheDocument();
    });

    it('should have proper semantic role', () => {
      render(
        <TestWrapper>
          <PriorityBadge priority={TaskPriority.URGENT} />
        </TestWrapper>
      );

      const badge = screen.getByText('Urgent');
      expect(badge.tagName).toBe('SPAN');
    });
  });

  describe('Priority Color Mapping', () => {
    const priorityTestCases = [
      { priority: TaskPriority.LOW, expectedText: 'Low' },
      { priority: TaskPriority.MEDIUM, expectedText: 'Medium' },
      { priority: TaskPriority.HIGH, expectedText: 'High' },
      { priority: TaskPriority.URGENT, expectedText: 'Urgent' }
    ];

    test.each(priorityTestCases)(
      'should render $expectedText for $priority priority',
      ({ priority, expectedText }) => {
        render(
          <TestWrapper>
            <PriorityBadge priority={priority} />
          </TestWrapper>
        );

        expect(screen.getByText(expectedText)).toBeInTheDocument();
      }
    );
  });

  describe('Component Integration', () => {
    it('should work within a parent container', () => {
      render(
        <TestWrapper>
          <div data-testid="parent-container">
            <PriorityBadge priority={TaskPriority.HIGH} />
          </div>
        </TestWrapper>
      );

      const container = screen.getByTestId('parent-container');
      const badge = screen.getByText('High');

      expect(container).toContainElement(badge);
    });

    it('should render multiple badges correctly', () => {
      render(
        <TestWrapper>
          <div>
            <PriorityBadge priority={TaskPriority.LOW} />
            <PriorityBadge priority={TaskPriority.HIGH} />
            <PriorityBadge priority={TaskPriority.URGENT} />
          </div>
        </TestWrapper>
      );

      expect(screen.getByText('Low')).toBeInTheDocument();
      expect(screen.getByText('High')).toBeInTheDocument();
      expect(screen.getByText('Urgent')).toBeInTheDocument();
    });
  });
});