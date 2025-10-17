/**
 * Performance Metrics State Management Store
 * ===========================================
 *
 * 管理90个性能预算指标和分支保护状态
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

// ===== Types =====

export interface PerformanceMetric {
  metricId: string;
  metricName: string;
  category: 'frontend' | 'backend' | 'database' | 'network' | 'other';
  currentValue: number;
  unit: string;
  budgetThreshold?: number;
  warningThreshold?: number;
  status: 'good' | 'warning' | 'exceeded';
  isWithinBudget: boolean;
  measuredAt: string;
  history?: number[];
}

export interface MetricGroup {
  category: string;
  metrics: PerformanceMetric[];
  withinBudgetCount: number;
  exceededCount: number;
  warningCount: number;
}

export interface BranchProtectionLayer {
  layerNumber: number;
  layerName: string;
  status: 'active' | 'failed' | 'warning';
  lastExecution?: string;
  successRate: number;
  recentBlocks: number;
  hooks: Array<{
    hookType: string;
    status: string;
    triggeredAt: string;
    blockedOperation?: string;
  }>;
}

export interface BranchProtectionStatus {
  overallStatus: 'healthy' | 'degraded' | 'critical';
  protectionScore: number;
  layers: BranchProtectionLayer[];
  recentViolations: Array<{
    hookType: string;
    layer: number;
    triggeredAt: string;
    blockedOperation?: string;
    error?: string;
  }>;
  recommendations: string[];
}

// ===== Store Interface =====

interface MetricsStore {
  // Performance metrics
  metrics: PerformanceMetric[];
  metricGroups: MetricGroup[];
  totalMetrics: number;
  withinBudget: number;
  exceeded: number;
  warning: number;
  budgetComplianceRate: number;

  // Branch protection
  branchProtection: BranchProtectionStatus | null;

  // Loading states
  isLoading: boolean;
  error: string | null;

  // Actions
  setMetrics: (metrics: PerformanceMetric[]) => void;
  setMetricGroups: (groups: MetricGroup[]) => void;
  setBranchProtection: (status: BranchProtectionStatus | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Update actions (for real-time WebSocket updates)
  updateMetric: (metricName: string, currentValue: number, status: string) => void;
  updateBranchProtectionLayer: (layerNumber: number, status: string) => void;

  // Reset
  reset: () => void;
}

// ===== Initial State =====

const initialState = {
  metrics: [],
  metricGroups: [],
  totalMetrics: 0,
  withinBudget: 0,
  exceeded: 0,
  warning: 0,
  budgetComplianceRate: 100,
  branchProtection: null,
  isLoading: false,
  error: null,
};

// ===== Store Implementation =====

export const useMetricsStore = create<MetricsStore>()(
  devtools(
    (set, get) => ({
      ...initialState,

      setMetrics: (metrics) => {
        const within = metrics.filter((m) => m.isWithinBudget).length;
        const exceeded = metrics.filter((m) => m.status === 'exceeded').length;
        const warning = metrics.filter((m) => m.status === 'warning').length;
        const complianceRate = metrics.length > 0 ? (within / metrics.length) * 100 : 100;

        set({
          metrics,
          totalMetrics: metrics.length,
          withinBudget: within,
          exceeded,
          warning,
          budgetComplianceRate: complianceRate,
        });
      },

      setMetricGroups: (groups) => set({ metricGroups: groups }),

      setBranchProtection: (status) => set({ branchProtection: status }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      updateMetric: (metricName, currentValue, status) =>
        set((state) => {
          const updatedMetrics = state.metrics.map((metric) =>
            metric.metricName === metricName
              ? {
                  ...metric,
                  currentValue,
                  status: status as any,
                  isWithinBudget: status === 'good',
                  measuredAt: new Date().toISOString(),
                }
              : metric
          );

          const within = updatedMetrics.filter((m) => m.isWithinBudget).length;
          const exceeded = updatedMetrics.filter((m) => m.status === 'exceeded').length;
          const warning = updatedMetrics.filter((m) => m.status === 'warning').length;
          const complianceRate = updatedMetrics.length > 0 ? (within / updatedMetrics.length) * 100 : 100;

          return {
            metrics: updatedMetrics,
            withinBudget: within,
            exceeded,
            warning,
            budgetComplianceRate: complianceRate,
          };
        }),

      updateBranchProtectionLayer: (layerNumber, status) =>
        set((state) => {
          if (!state.branchProtection) return state;

          const updatedLayers = state.branchProtection.layers.map((layer) =>
            layer.layerNumber === layerNumber
              ? { ...layer, status: status as any }
              : layer
          );

          return {
            branchProtection: {
              ...state.branchProtection,
              layers: updatedLayers,
            },
          };
        }),

      reset: () => set(initialState),
    }),
    {
      name: 'metrics-store',
    }
  )
);

// ===== Selectors =====

export const selectMetricsByCategory = (category: string) => (state: MetricsStore) =>
  state.metrics.filter((m) => m.category === category);

export const selectExceededMetrics = (state: MetricsStore) =>
  state.metrics.filter((m) => m.status === 'exceeded');

export const selectBranchProtectionScore = (state: MetricsStore) =>
  state.branchProtection?.protectionScore || 0;

export const selectIsHealthy = (state: MetricsStore) =>
  state.branchProtection?.overallStatus === 'healthy' && state.budgetComplianceRate >= 90;
