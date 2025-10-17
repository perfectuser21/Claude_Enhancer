import React from 'react';
import { ChakraProvider, ColorModeScript } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import theme from './theme';
import { useAuthStore } from './store';
import { AuthPage } from './pages/auth/AuthPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { LoadingSpinner } from './components/atoms';
import SystemLifeDashboard from './pages/workflow/SystemLifeDashboard';
import WorkflowDashboardPage from './pages/workflow/WorkflowDashboardPage';
import PhaseDetailPage from './pages/workflow/PhaseDetailPage';
import LogViewerPage from './pages/workflow/LogViewerPage';
import AgentWorkflowPage from './pages/workflow/AgentWorkflowPage';
import QualityGatesPage from './pages/workflow/QualityGatesPage';
import PerformanceBudgetPage from './pages/workflow/PerformanceBudgetPage';

// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Checking authentication..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  return <>{children}</>;
};

// Public Route Component (redirect if already authenticated)
const PublicRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Checking authentication..." />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <ChakraProvider theme={theme}>
      <ColorModeScript initialColorMode={theme.config.initialColorMode} />
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route
            path="/auth"
            element={
              <PublicRoute>
                <AuthPage />
              </PublicRoute>
            }
          />

          {/* Protected Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          {/* Workflow Dashboard Routes - 暂时移除认证保护以便预览 */}
          <Route path="/workflow" element={<SystemLifeDashboard />} />
          <Route path="/workflow/classic" element={<WorkflowDashboardPage />} />
          <Route path="/workflow/phases/:phaseId" element={<PhaseDetailPage />} />
          <Route path="/workflow/agents/:executionId" element={<AgentWorkflowPage />} />
          <Route path="/workflow/logs" element={<LogViewerPage />} />
          <Route path="/workflow/quality-gates" element={<QualityGatesPage />} />
          <Route path="/workflow/performance" element={<PerformanceBudgetPage />} />

          {/* Root redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Catch all - redirect to dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </ChakraProvider>
  );
}

export default App;
