import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

// Theme configuration
const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: true,
};

// Custom colors
const colors = {
  brand: {
    50: '#E3F2FD',
    100: '#BBDEFB',
    200: '#90CAF9',
    300: '#64B5F6',
    400: '#42A5F5',
    500: '#2196F3',
    600: '#1E88E5',
    700: '#1976D2',
    800: '#1565C0',
    900: '#0D47A1',
  },
  task: {
    todo: '#4A5568',
    in_progress: '#3182CE',
    review: '#D69E2E',
    done: '#38A169',
  },
  priority: {
    low: '#38A169',
    medium: '#D69E2E',
    high: '#E53E3E',
    urgent: '#9B2C2C',
  },
  status: {
    active: '#38A169',
    inactive: '#718096',
    pending: '#D69E2E',
    error: '#E53E3E',
  },
};

// Custom fonts
const fonts = {
  heading: `'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`,
  body: `'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`,
};

// Custom component styles
const components = {
  Button: {
    baseStyle: {
      fontWeight: '600',
      borderRadius: 'md',
    },
    sizes: {
      sm: {
        fontSize: 'sm',
        px: 3,
        py: 2,
      },
      md: {
        fontSize: 'md',
        px: 4,
        py: 2,
      },
      lg: {
        fontSize: 'lg',
        px: 6,
        py: 3,
      },
    },
    variants: {
      solid: {
        bg: 'brand.500',
        color: 'white',
        _hover: {
          bg: 'brand.600',
          _disabled: {
            bg: 'brand.500',
          },
        },
        _active: {
          bg: 'brand.700',
        },
      },
      ghost: {
        _hover: {
          bg: 'gray.100',
          _dark: {
            bg: 'gray.700',
          },
        },
      },
      outline: {
        borderColor: 'brand.500',
        color: 'brand.500',
        _hover: {
          bg: 'brand.50',
          _dark: {
            bg: 'brand.900',
          },
        },
      },
    },
  },
  Card: {
    baseStyle: {
      container: {
        bg: 'white',
        _dark: {
          bg: 'gray.800',
        },
        borderRadius: 'lg',
        border: '1px solid',
        borderColor: 'gray.200',
        _dark: {
          borderColor: 'gray.600',
        },
        shadow: 'sm',
        _hover: {
          shadow: 'md',
        },
        transition: 'all 0.2s',
      },
    },
    variants: {
      task: {
        container: {
          p: 4,
          cursor: 'pointer',
          _hover: {
            transform: 'translateY(-2px)',
            shadow: 'lg',
          },
        },
      },
      kanban: {
        container: {
          bg: 'gray.50',
          _dark: {
            bg: 'gray.700',
          },
          borderRadius: 'xl',
          p: 4,
          minH: '500px',
        },
      },
    },
  },
  Input: {
    variants: {
      filled: {
        field: {
          bg: 'gray.50',
          _dark: {
            bg: 'gray.700',
          },
          _hover: {
            bg: 'gray.100',
            _dark: {
              bg: 'gray.600',
            },
          },
          _focus: {
            bg: 'white',
            _dark: {
              bg: 'gray.800',
            },
            borderColor: 'brand.500',
          },
        },
      },
    },
  },
  Select: {
    variants: {
      filled: {
        field: {
          bg: 'gray.50',
          _dark: {
            bg: 'gray.700',
          },
          _hover: {
            bg: 'gray.100',
            _dark: {
              bg: 'gray.600',
            },
          },
          _focus: {
            bg: 'white',
            _dark: {
              bg: 'gray.800',
            },
            borderColor: 'brand.500',
          },
        },
      },
    },
  },
  Textarea: {
    variants: {
      filled: {
        bg: 'gray.50',
        _dark: {
          bg: 'gray.700',
        },
        _hover: {
          bg: 'gray.100',
          _dark: {
            bg: 'gray.600',
          },
        },
        _focus: {
          bg: 'white',
          _dark: {
            bg: 'gray.800',
          },
          borderColor: 'brand.500',
        },
      },
    },
  },
  Badge: {
    baseStyle: {
      fontWeight: '600',
      borderRadius: 'full',
      px: 2,
      py: 1,
    },
    variants: {
      priority: {
        low: {
          bg: 'green.100',
          color: 'green.800',
          _dark: {
            bg: 'green.900',
            color: 'green.200',
          },
        },
        medium: {
          bg: 'yellow.100',
          color: 'yellow.800',
          _dark: {
            bg: 'yellow.900',
            color: 'yellow.200',
          },
        },
        high: {
          bg: 'orange.100',
          color: 'orange.800',
          _dark: {
            bg: 'orange.900',
            color: 'orange.200',
          },
        },
        urgent: {
          bg: 'red.100',
          color: 'red.800',
          _dark: {
            bg: 'red.900',
            color: 'red.200',
          },
        },
      },
      status: {
        todo: {
          bg: 'gray.100',
          color: 'gray.800',
          _dark: {
            bg: 'gray.700',
            color: 'gray.200',
          },
        },
        in_progress: {
          bg: 'blue.100',
          color: 'blue.800',
          _dark: {
            bg: 'blue.900',
            color: 'blue.200',
          },
        },
        review: {
          bg: 'yellow.100',
          color: 'yellow.800',
          _dark: {
            bg: 'yellow.900',
            color: 'yellow.200',
          },
        },
        done: {
          bg: 'green.100',
          color: 'green.800',
          _dark: {
            bg: 'green.900',
            color: 'green.200',
          },
        },
      },
    },
  },
  Sidebar: {
    baseStyle: {
      bg: 'white',
      _dark: {
        bg: 'gray.800',
      },
      borderRight: '1px solid',
      borderColor: 'gray.200',
      _dark: {
        borderColor: 'gray.600',
      },
    },
  },
  Header: {
    baseStyle: {
      bg: 'white',
      _dark: {
        bg: 'gray.800',
      },
      borderBottom: '1px solid',
      borderColor: 'gray.200',
      _dark: {
        borderColor: 'gray.600',
      },
      shadow: 'sm',
    },
  },
};

// Global styles
const styles = {
  global: (props: any) => ({
    body: {
      bg: props.colorMode === 'dark' ? 'gray.900' : 'gray.50',
      color: props.colorMode === 'dark' ? 'white' : 'gray.800',
    },
    '*': {
      scrollbarWidth: 'thin',
      scrollbarColor: props.colorMode === 'dark' ? '#4A5568 #1A202C' : '#CBD5E0 #F7FAFC',
    },
    '*::-webkit-scrollbar': {
      width: '8px',
    },
    '*::-webkit-scrollbar-track': {
      bg: props.colorMode === 'dark' ? 'gray.800' : 'gray.100',
    },
    '*::-webkit-scrollbar-thumb': {
      bg: props.colorMode === 'dark' ? 'gray.600' : 'gray.300',
      borderRadius: 'full',
    },
    '*::-webkit-scrollbar-thumb:hover': {
      bg: props.colorMode === 'dark' ? 'gray.500' : 'gray.400',
    },
  }),
};

// Breakpoints
const breakpoints = {
  base: '0em',   // 0px
  sm: '30em',    // 480px
  md: '48em',    // 768px
  lg: '62em',    // 992px
  xl: '80em',    // 1280px
  '2xl': '96em', // 1536px
};

// Spacing
const space = {
  px: '1px',
  0.5: '0.125rem',
  1: '0.25rem',
  1.5: '0.375rem',
  2: '0.5rem',
  2.5: '0.625rem',
  3: '0.75rem',
  3.5: '0.875rem',
  4: '1rem',
  5: '1.25rem',
  6: '1.5rem',
  7: '1.75rem',
  8: '2rem',
  9: '2.25rem',
  10: '2.5rem',
  12: '3rem',
  14: '3.5rem',
  16: '4rem',
  20: '5rem',
  24: '6rem',
  28: '7rem',
  32: '8rem',
  36: '9rem',
  40: '10rem',
  44: '11rem',
  48: '12rem',
  52: '13rem',
  56: '14rem',
  60: '15rem',
  64: '16rem',
  72: '18rem',
  80: '20rem',
  96: '24rem',
};

// Create the theme
const theme = extendTheme({
  config,
  colors,
  fonts,
  components,
  styles,
  breakpoints,
  space,
});

export default theme;

// Theme utility functions
export const getTaskStatusColor = (status: string) => {
  const statusColors = {
    todo: 'gray',
    in_progress: 'blue',
    review: 'yellow',
    done: 'green',
  };
  return statusColors[status as keyof typeof statusColors] || 'gray';
};

export const getPriorityColor = (priority: string) => {
  const priorityColors = {
    low: 'green',
    medium: 'yellow',
    high: 'orange',
    urgent: 'red',
  };
  return priorityColors[priority as keyof typeof priorityColors] || 'gray';
};

export const getProjectStatusColor = (status: string) => {
  const statusColors = {
    active: 'green',
    completed: 'blue',
    archived: 'gray',
    on_hold: 'yellow',
  };
  return statusColors[status as keyof typeof statusColors] || 'gray';
};