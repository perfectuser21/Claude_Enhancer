/**
 * Workflow State Management Store
 * ================================
 *
 * 使用Zustand管理工作流状态：
 * - Workflow Sessions
 * - Phase执行详情
 * - Agent工作流
 * - Quality Gates
 * - BDD Scenarios
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

// ===== Types =====

export interface PhaseDetail {
  phaseId: string;
  phaseName: string;
  phaseNumber: number;
  status: 'not_started' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  startedAt?: string;
  completedAt?: string;
  durationSeconds?: number;
  deliverables?: Array<{ file: string; type: string }>;
  tasksCompleted?: string[];
  errors?: Array<{ message: string; severity: string }>;
  warnings?: Array<{ message: string }>;
  metrics?: Record<string, any>;
}

export interface AgentWorkflow {
  executionId: string;
  agentType: string;
  agentName?: string;
  taskDescription?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'timeout';
  startedAt?: string;
  completedAt?: string;
  durationSeconds?: number;
  outputFiles?: string[];
  outputSummary?: string;
  toolCalls?: Array<{ tool: string; args: any; result: any }>;
  tokensUsed?: number;
  errorMessage?: string;
}

export interface QualityGateResult {
  gateId: string;
  gateType: string;
  phase: string;
  gateName: string;
  executedAt?: string;
  status: 'pending' | 'passed' | 'failed' | 'skipped';
  passedChecks: number;
  failedChecks: number;
  warningChecks: number;
  checkResults?: Array<{ check: string; status: string; message?: string }>;
  issuesFound?: Array<{ type: string; severity: string; message: string; file?: string }>;
  recommendations?: string[];
  blocksMerge: boolean;
  blockingReasons?: string[];
}

export interface BDDScenario {
  executionId: string;
  featureFile: string;
  scenarioName: string;
  status: 'passed' | 'failed' | 'skipped' | 'pending';
  stepsTotal: number;
  stepsPassed: number;
  stepsFailed: number;
  stepsSkipped: number;
  durationMs: number;
  executedAt: string;
  failedStep?: string;
  errorMessage?: string;
  environment?: string;
}

export interface WorkflowSession {
  sessionId: string;
  branchName: string;
  featureName: string;
  impactRadiusScore?: number;
  riskLevel?: string;
  currentPhase?: string;
  status: 'in_progress' | 'completed' | 'failed';
  qualityScore?: number;
  totalAgentsUsed?: number;
  startedAt?: string;
  completedAt?: string;
}

// ===== Store Interface =====

interface WorkflowStore {
  // Current session
  currentSession: WorkflowSession | null;
  sessions: WorkflowSession[];

  // Phase details
  currentPhase: PhaseDetail | null;
  phaseHistory: PhaseDetail[];

  // Agent workflows
  activeAgents: AgentWorkflow[];
  agentHistory: AgentWorkflow[];

  // Quality gates
  qualityGates: QualityGateResult[];

  // BDD scenarios
  bddScenarios: BDDScenario[];

  // Loading states
  isLoading: boolean;
  error: string | null;

  // Actions
  setCurrentSession: (session: WorkflowSession | null) => void;
  setSessions: (sessions: WorkflowSession[]) => void;
  setCurrentPhase: (phase: PhaseDetail | null) => void;
  setPhaseHistory: (phases: PhaseDetail[]) => void;
  setActiveAgents: (agents: AgentWorkflow[]) => void;
  setAgentHistory: (agents: AgentWorkflow[]) => void;
  setQualityGates: (gates: QualityGateResult[]) => void;
  setBDDScenarios: (scenarios: BDDScenario[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Update actions (for WebSocket real-time updates)
  updatePhaseStatus: (phaseId: string, status: string, metrics?: any) => void;
  updateAgentProgress: (executionId: string, progress: number, status: string) => void;
  addQualityGateResult: (gate: QualityGateResult) => void;
  updateBDDScenarioResult: (scenario: BDDScenario) => void;

  // Reset
  reset: () => void;
}

// ===== Initial State =====

const initialState = {
  currentSession: null,
  sessions: [],
  currentPhase: null,
  phaseHistory: [],
  activeAgents: [],
  agentHistory: [],
  qualityGates: [],
  bddScenarios: [],
  isLoading: false,
  error: null,
};

// ===== Store Implementation =====

export const useWorkflowStore = create<WorkflowStore>()(
  devtools(
    (set, get) => ({
      ...initialState,

      // Basic setters
      setCurrentSession: (session) => set({ currentSession: session }),
      setSessions: (sessions) => set({ sessions }),
      setCurrentPhase: (phase) => set({ currentPhase: phase }),
      setPhaseHistory: (phases) => set({ phaseHistory: phases }),
      setActiveAgents: (agents) => set({ activeAgents: agents }),
      setAgentHistory: (agents) => set({ agentHistory: agents }),
      setQualityGates: (gates) => set({ qualityGates: gates }),
      setBDDScenarios: (scenarios) => set({ bddScenarios: scenarios }),
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),

      // Real-time update actions
      updatePhaseStatus: (phaseId, status, metrics) =>
        set((state) => {
          // Update current phase if it's the same
          const updatedCurrentPhase =
            state.currentPhase?.phaseId === phaseId
              ? {
                  ...state.currentPhase,
                  status: status as any,
                  metrics: metrics || state.currentPhase.metrics,
                }
              : state.currentPhase;

          // Update phase history
          const updatedHistory = state.phaseHistory.map((phase) =>
            phase.phaseId === phaseId
              ? { ...phase, status: status as any, metrics: metrics || phase.metrics }
              : phase
          );

          return {
            currentPhase: updatedCurrentPhase,
            phaseHistory: updatedHistory,
          };
        }),

      updateAgentProgress: (executionId, progress, status) =>
        set((state) => {
          const updateAgent = (agent: AgentWorkflow) =>
            agent.executionId === executionId
              ? { ...agent, status: status as any, metadata: { ...agent, progress } }
              : agent;

          return {
            activeAgents: state.activeAgents.map(updateAgent),
            agentHistory: state.agentHistory.map(updateAgent),
          };
        }),

      addQualityGateResult: (gate) =>
        set((state) => ({
          qualityGates: [...state.qualityGates, gate],
        })),

      updateBDDScenarioResult: (scenario) =>
        set((state) => {
          const existingIndex = state.bddScenarios.findIndex(
            (s) => s.executionId === scenario.executionId
          );

          if (existingIndex >= 0) {
            const updated = [...state.bddScenarios];
            updated[existingIndex] = scenario;
            return { bddScenarios: updated };
          } else {
            return { bddScenarios: [...state.bddScenarios, scenario] };
          }
        }),

      // Reset
      reset: () => set(initialState),
    }),
    {
      name: 'workflow-store',
    }
  )
);

// ===== Selectors =====

export const selectCurrentSessionId = (state: WorkflowStore) => state.currentSession?.sessionId;
export const selectIsLoading = (state: WorkflowStore) => state.isLoading;
export const selectError = (state: WorkflowStore) => state.error;
export const selectActivePhase = (state: WorkflowStore) => state.currentPhase;
export const selectActiveAgents = (state: WorkflowStore) => state.activeAgents;
export const selectFailedQualityGates = (state: WorkflowStore) =>
  state.qualityGates.filter((gate) => gate.status === 'failed');
export const selectBDDFailedScenarios = (state: WorkflowStore) =>
  state.bddScenarios.filter((scenario) => scenario.status === 'failed');
