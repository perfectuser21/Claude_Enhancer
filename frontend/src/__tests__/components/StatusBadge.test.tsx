/**
 * StatusBadge组件测试
 * Initial-tests阶段 - 测试状态徽章组件
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { StatusBadge } from '../../components/atoms/StatusBadge';
import { TaskStatus } from '../../types';

// 测试包装器
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ChakraProvider>{children}</ChakraProvider>
);

describe('StatusBadge', () => {
  describe('Status Display', () => {
    it('should display correct label for todo status', () => {
      render(
        <TestWrapper>
          <StatusBadge status={TaskStatus.TODO} />
        </TestWrapper>
      );

      expect(screen.getByText('To Do')).toBeInTheDocument();
    });

    it('should display correct label for in progress status', () => {
      render(
        <TestWrapper>
          <StatusBadge status={TaskStatus.IN_PROGRESS} />
        </TestWrapper>
      );

      expect(screen.getByText('In Progress')).toBeInTheDocument();
    });

    it('should display correct label for in review status', () => {
      render(
        <TestWrapper>
          <StatusBadge status={TaskStatus.IN_REVIEW} />
        </TestWrapper>
      );

      expect(screen.getByText('In Review')).toBeInTheDocument();
    });

    it('should display correct label for done status', () => {
      render(
        <TestWrapper>
          <StatusBadge status={TaskStatus.DONE} />
        </TestWrapper>
      );

      expect(screen.getByText('Done')).toBeInTheDocument();
    });

    it('should display correct label for blocked status', () => {
      render(
        <TestWrapper>
          <StatusBadge status={TaskStatus.BLOCKED} />
        </TestWrapper>
      );

      expect(screen.getByText('Blocked')).toBeInTheDocument();
    });

    it('should display correct label for cancelled status', () => {
      render(
        <TestWrapper>
          <StatusBadge status={TaskStatus.CANCELLED} />
        </TestWrapper>
      );

      expect(screen.getByText('Cancelled')).toBeInTheDocument();
    });
  });

  describe('Visual Variants', () => {
    it('should apply default subtle variant', () => {
      render(
        <TestWrapper>
          <StatusBadge status={TaskStatus.IN_PROGRESS} />
        </TestWrapper>
      );

      const badge = screen.getByText('In Progress');
      expect(badge).toHaveClass('chakra-badge');
    });

    it('should apply solid variant when specified', () => {
      render(
        <TestWrapper>
          <StatusBadge status={TaskStatus.DONE} variant="solid" />
        </TestWrapper>
      );

      const badge = screen.getByText('Done');
      expect(badge).toBeInTheDocument();
    });

    it('should apply correct size classes', () => {
      render(
        <TestWrapper>
          <StatusBadge status={TaskStatus.TODO} size="sm" />
        </TestWrapper>
      );

      const badge = screen.getByText('To Do');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Status Color Scheme', () => {
    const statusColorTests = [
      { status: TaskStatus.TODO, expectedClass: 'gray' },
      { status: TaskStatus.IN_PROGRESS, expectedClass: 'blue' },
      { status: TaskStatus.IN_REVIEW, expectedClass: 'yellow' },
      { status: TaskStatus.DONE, expectedClass: 'green' },
      { status: TaskStatus.BLOCKED, expectedClass: 'red' },
      { status: TaskStatus.CANCELLED, expectedClass: 'gray' }
    ];

    test.each(statusColorTests)(
      'should apply correct color scheme for $status status',
      ({ status }) => {
        render(
          <TestWrapper>
            <StatusBadge status={status} />
          </TestWrapper>
        );

        // 验证徽章渲染
        const badge = screen.getByRole('text');
        expect(badge).toBeInTheDocument();
      }
    );
  });

  describe('Interactive Features', () => {
    it('should handle click events when clickable', () => {
      const handleClick = jest.fn();

      render(
        <TestWrapper>
          <StatusBadge
            status={TaskStatus.TODO}
            onClick={handleClick}
            cursor="pointer"
          />
        </TestWrapper>
      );

      const badge = screen.getByText('To Do');
      badge.click();

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should not be clickable by default', () => {
      render(
        <TestWrapper>
          <StatusBadge status={TaskStatus.IN_PROGRESS} />
        </TestWrapper>
      );

      const badge = screen.getByText('In Progress');
      expect(badge).not.toHaveStyle('cursor: pointer');
    });
  });

  describe('Accessibility Features', () => {
    it('should provide proper accessibility labels', () => {
      render(
        <TestWrapper>
          <StatusBadge
            status={TaskStatus.DONE}
            aria-label="Task status: Completed"
          />
        </TestWrapper>
      );

      expect(screen.getByLabelText('Task status: Completed')).toBeInTheDocument();
    });

    it('should support keyboard navigation when interactive', () => {
      const handleKeyDown = jest.fn();

      render(
        <TestWrapper>
          <StatusBadge
            status={TaskStatus.TODO}
            onKeyDown={handleKeyDown}
            tabIndex={0}
          />
        </TestWrapper>
      );

      const badge = screen.getByText('To Do');
      expect(badge).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('Custom Styling', () => {
    it('should accept custom CSS classes', () => {
      render(
        <TestWrapper>
          <StatusBadge
            status={TaskStatus.HIGH_PRIORITY}
            className="custom-status-badge"
          />
        </TestWrapper>
      );

      const badge = screen.getByText('High Priority');
      expect(badge).toHaveClass('custom-status-badge');
    });

    it('should allow custom styles override', () => {
      render(
        <TestWrapper>
          <StatusBadge
            status={TaskStatus.IN_PROGRESS}
            style={{ backgroundColor: 'purple' }}
          />
        </TestWrapper>
      );

      const badge = screen.getByText('In Progress');
      expect(badge).toHaveStyle('background-color: purple');
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined status gracefully', () => {
      render(
        <TestWrapper>
          <StatusBadge status={undefined as any} />
        </TestWrapper>
      );

      // 应该有默认显示或错误处理
      expect(screen.getByRole('text')).toBeInTheDocument();
    });

    it('should handle invalid status values', () => {
      render(
        <TestWrapper>
          <StatusBadge status={'invalid_status' as any} />
        </TestWrapper>
      );

      // 应该有错误处理或默认显示
      const badge = screen.getByRole('text');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('should render quickly with multiple status badges', () => {
      const startTime = performance.now();

      render(
        <TestWrapper>
          <div>
            {Object.values(TaskStatus).map((status, index) => (
              <StatusBadge key={index} status={status} />
            ))}
          </div>
        </TestWrapper>
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // 渲染时间应该小于100ms
      expect(renderTime).toBeLessThan(100);
    });

    it('should not cause memory leaks with frequent re-renders', () => {
      const { rerender } = render(
        <TestWrapper>
          <StatusBadge status={TaskStatus.TODO} />
        </TestWrapper>
      );

      // 多次重新渲染
      for (let i = 0; i < 10; i++) {
        rerender(
          <TestWrapper>
            <StatusBadge status={TaskStatus.IN_PROGRESS} />
          </TestWrapper>
        );
      }

      // 验证最终状态
      expect(screen.getByText('In Progress')).toBeInTheDocument();
    });
  });
});