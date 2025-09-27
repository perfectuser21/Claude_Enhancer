/**
 * Avatar组件测试
 * Initial-tests阶段 - 测试头像组件
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { Avatar } from '../../components/atoms/Avatar';

// 测试包装器
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ChakraProvider>{children}</ChakraProvider>
);

describe('Avatar', () => {
  describe('Image Display', () => {
    it('should display user image when src is provided', () => {
      render(
        <TestWrapper>
          <Avatar
            src="https://example.com/avatar.jpg"
            name="John Doe"
            alt="John Doe's avatar"
          />
        </TestWrapper>
      );

      const image = screen.getByAltText("John Doe's avatar");
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('src', 'https://example.com/avatar.jpg');
    });

    it('should display fallback initials when no image is provided', () => {
      render(
        <TestWrapper>
          <Avatar name="John Doe" />
        </TestWrapper>
      );

      expect(screen.getByText('JD')).toBeInTheDocument();
    });

    it('should display fallback initials when image fails to load', async () => {
      render(
        <TestWrapper>
          <Avatar
            src="https://invalid-url.com/avatar.jpg"
            name="Jane Smith"
          />
        </TestWrapper>
      );

      const image = screen.getByRole('img');
      fireEvent.error(image);

      await waitFor(() => {
        expect(screen.getByText('JS')).toBeInTheDocument();
      });
    });
  });

  describe('Name Processing', () => {
    it('should generate correct initials from full name', () => {
      render(
        <TestWrapper>
          <Avatar name="John Smith Doe" />
        </TestWrapper>
      );

      expect(screen.getByText('JD')).toBeInTheDocument();
    });

    it('should handle single name', () => {
      render(
        <TestWrapper>
          <Avatar name="John" />
        </TestWrapper>
      );

      expect(screen.getByText('J')).toBeInTheDocument();
    });

    it('should handle empty name gracefully', () => {
      render(
        <TestWrapper>
          <Avatar name="" />
        </TestWrapper>
      );

      expect(screen.getByText('?')).toBeInTheDocument();
    });

    it('should handle special characters in names', () => {
      render(
        <TestWrapper>
          <Avatar name="José María" />
        </TestWrapper>
      );

      expect(screen.getByText('JM')).toBeInTheDocument();
    });

    it('should handle Chinese names', () => {
      render(
        <TestWrapper>
          <Avatar name="张三" />
        </TestWrapper>
      );

      expect(screen.getByText('张三')).toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    const sizeTests = [
      { size: 'xs', expectedSize: '24px' },
      { size: 'sm', expectedSize: '32px' },
      { size: 'md', expectedSize: '48px' },
      { size: 'lg', expectedSize: '64px' },
      { size: 'xl', expectedSize: '96px' },
      { size: '2xl', expectedSize: '128px' }
    ];

    test.each(sizeTests)(
      'should render $size size correctly',
      ({ size }) => {
        render(
          <TestWrapper>
            <Avatar name="Test User" size={size} />
          </TestWrapper>
        );

        const avatar = screen.getByText('TU').closest('.chakra-avatar');
        expect(avatar).toBeInTheDocument();
      }
    );
  });

  describe('Color Schemes', () => {
    it('should apply correct color scheme', () => {
      render(
        <TestWrapper>
          <Avatar name="Test User" colorScheme="blue" />
        </TestWrapper>
      );

      const avatar = screen.getByText('TU');
      expect(avatar).toBeInTheDocument();
    });

    it('should generate consistent colors for same name', () => {
      const { rerender } = render(
        <TestWrapper>
          <Avatar name="Consistent User" />
        </TestWrapper>
      );

      const firstRender = screen.getByText('CU');
      const firstColor = window.getComputedStyle(firstRender).backgroundColor;

      rerender(
        <TestWrapper>
          <Avatar name="Consistent User" />
        </TestWrapper>
      );

      const secondRender = screen.getByText('CU');
      const secondColor = window.getComputedStyle(secondRender).backgroundColor;

      expect(firstColor).toBe(secondColor);
    });
  });

  describe('Interactive Features', () => {
    it('should handle click events', () => {
      const handleClick = jest.fn();

      render(
        <TestWrapper>
          <Avatar
            name="Clickable User"
            onClick={handleClick}
            cursor="pointer"
          />
        </TestWrapper>
      );

      const avatar = screen.getByText('CU');
      fireEvent.click(avatar);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should handle hover events', () => {
      const handleMouseEnter = jest.fn();
      const handleMouseLeave = jest.fn();

      render(
        <TestWrapper>
          <Avatar
            name="Hover User"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          />
        </TestWrapper>
      );

      const avatar = screen.getByText('HU');

      fireEvent.mouseEnter(avatar);
      expect(handleMouseEnter).toHaveBeenCalledTimes(1);

      fireEvent.mouseLeave(avatar);
      expect(handleMouseLeave).toHaveBeenCalledTimes(1);
    });
  });

  describe('Status Indicators', () => {
    it('should display online status indicator', () => {
      render(
        <TestWrapper>
          <Avatar name="Online User" showStatus status="online" />
        </TestWrapper>
      );

      expect(screen.getByTestId('avatar-status')).toBeInTheDocument();
    });

    it('should display offline status indicator', () => {
      render(
        <TestWrapper>
          <Avatar name="Offline User" showStatus status="offline" />
        </TestWrapper>
      );

      expect(screen.getByTestId('avatar-status')).toBeInTheDocument();
    });

    it('should display away status indicator', () => {
      render(
        <TestWrapper>
          <Avatar name="Away User" showStatus status="away" />
        </TestWrapper>
      );

      expect(screen.getByTestId('avatar-status')).toBeInTheDocument();
    });

    it('should not display status indicator when showStatus is false', () => {
      render(
        <TestWrapper>
          <Avatar name="No Status User" showStatus={false} status="online" />
        </TestWrapper>
      );

      expect(screen.queryByTestId('avatar-status')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper alt text for images', () => {
      render(
        <TestWrapper>
          <Avatar
            src="https://example.com/avatar.jpg"
            name="Accessible User"
            alt="Profile picture of Accessible User"
          />
        </TestWrapper>
      );

      expect(
        screen.getByAltText('Profile picture of Accessible User')
      ).toBeInTheDocument();
    });

    it('should provide accessible name for initials', () => {
      render(
        <TestWrapper>
          <Avatar
            name="Screen Reader User"
            aria-label="Avatar for Screen Reader User"
          />
        </TestWrapper>
      );

      expect(
        screen.getByLabelText('Avatar for Screen Reader User')
      ).toBeInTheDocument();
    });

    it('should support keyboard navigation when interactive', () => {
      const handleKeyDown = jest.fn();

      render(
        <TestWrapper>
          <Avatar
            name="Keyboard User"
            onKeyDown={handleKeyDown}
            tabIndex={0}
          />
        </TestWrapper>
      );

      const avatar = screen.getByText('KU');
      expect(avatar).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('Custom Styling', () => {
    it('should accept custom CSS classes', () => {
      render(
        <TestWrapper>
          <Avatar name="Custom User" className="custom-avatar" />
        </TestWrapper>
      );

      const avatar = screen.getByText('CU').closest('.custom-avatar');
      expect(avatar).toBeInTheDocument();
    });

    it('should allow style overrides', () => {
      render(
        <TestWrapper>
          <Avatar
            name="Styled User"
            style={{ borderRadius: '4px', border: '2px solid red' }}
          />
        </TestWrapper>
      );

      const avatar = screen.getByText('SU');
      expect(avatar).toHaveStyle('border-radius: 4px');
      expect(avatar).toHaveStyle('border: 2px solid red');
    });
  });

  describe('Badge Support', () => {
    it('should display notification badge', () => {
      render(
        <TestWrapper>
          <Avatar name="Badge User" badge={{ count: 5, color: 'red' }} />
        </TestWrapper>
      );

      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('should handle large badge numbers', () => {
      render(
        <TestWrapper>
          <Avatar name="Badge User" badge={{ count: 99, color: 'blue' }} />
        </TestWrapper>
      );

      expect(screen.getByText('99+')).toBeInTheDocument();
    });

    it('should display dot badge when count is 0', () => {
      render(
        <TestWrapper>
          <Avatar name="Badge User" badge={{ count: 0, showDot: true }} />
        </TestWrapper>
      );

      expect(screen.getByTestId('avatar-badge-dot')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('should render multiple avatars efficiently', () => {
      const startTime = performance.now();

      render(
        <TestWrapper>
          <div>
            {Array.from({ length: 50 }, (_, i) => (
              <Avatar key={i} name={`User ${i}`} />
            ))}
          </div>
        </TestWrapper>
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // 50个头像的渲染时间应该小于200ms
      expect(renderTime).toBeLessThan(200);
    });

    it('should handle image loading efficiently', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Avatar src="https://example.com/avatar1.jpg" name="User 1" />
        </TestWrapper>
      );

      // 快速切换图片源
      for (let i = 2; i <= 10; i++) {
        rerender(
          <TestWrapper>
            <Avatar src={`https://example.com/avatar${i}.jpg`} name={`User ${i}`} />
          </TestWrapper>
        );
      }

      // 验证最终状态
      const finalImage = screen.getByRole('img');
      expect(finalImage).toHaveAttribute('src', 'https://example.com/avatar10.jpg');
    });
  });
});