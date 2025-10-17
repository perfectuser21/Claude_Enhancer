/**
 * Workflow WebSocket Hook
 * ========================
 *
 * 专门用于Workflow Dashboard的WebSocket连接
 * 连接到Node.js WebSocket服务器（端口8080）
 *
 * 特性：
 * - 自动重连（exponential backoff）
 * - 心跳检测
 * - 实时Phase/Agent/Quality Gate更新
 * - 与workflowStore和metricsStore集成
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useWorkflowStore } from '../stores/workflowStore';
import { useMetricsStore } from '../stores/metricsStore';

// ===== Types =====

interface WebSocketMessage {
  type: string;
  event: string;
  data: any;
}

interface WorkflowWebSocketOptions {
  url?: string;
  sessionId?: string;
  autoConnect?: boolean;
  reconnect?: boolean;
  subscribeToEvents?: string[];
}

interface WorkflowWebSocketReturn {
  isConnected: boolean;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'error';
  error: string | null;
  connect: () => void;
  disconnect: () => void;
  subscribe: (eventType: string) => void;
  unsubscribe: (eventType: string) => void;
  reconnectCount: number;
}

// ===== Hook Implementation =====

export function useWorkflowWebSocket(
  options: WorkflowWebSocketOptions = {}
): WorkflowWebSocketReturn {
  const {
    url = process.env.REACT_APP_WORKFLOW_WS_URL || 'ws://localhost:8080',
    sessionId = 'default',
    autoConnect = true,
    reconnect = true,
    subscribeToEvents = [
      'phase:update',
      'agent:progress',
      'quality:gate',
      'metric:update',
      'hook:execution',
    ],
  } = options;

  // State
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<
    'disconnected' | 'connecting' | 'connected' | 'error'
  >('disconnected');
  const [error, setError] = useState<string | null>(null);
  const [reconnectCount, setReconnectCount] = useState(0);

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const subscriptionsRef = useRef<Set<string>>(new Set(subscribeToEvents));

  // Store actions
  const workflowStore = useWorkflowStore();
  const metricsStore = useMetricsStore();

  // Message handler
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        // Handle different message types
        switch (message.type) {
          case 'connection':
            if (message.event === 'connected') {
              setConnectionState('connected');
              setIsConnected(true);
              setError(null);
              setReconnectCount(0);

              // Subscribe to events
              subscriptionsRef.current.forEach((eventType) => {
                wsRef.current?.send(
                  JSON.stringify({ action: 'subscribe', payload: { eventType } })
                );
              });
            }
            break;

          case 'phase':
            if (message.event === 'status_update') {
              workflowStore.updatePhaseStatus(
                message.data.phase,
                message.data.status,
                message.data.metrics
              );
            }
            break;

          case 'agent':
            if (message.event === 'progress_update') {
              workflowStore.updateAgentProgress(
                message.data.executionId || message.data.agentType,
                message.data.progress || 0,
                message.data.status
              );
            }
            break;

          case 'quality_gate':
            if (message.event === 'result') {
              workflowStore.addQualityGateResult(message.data);
            }
            break;

          case 'performance_metric':
            if (message.event === 'update') {
              metricsStore.updateMetric(
                message.data.metricName,
                message.data.currentValue,
                message.data.status
              );
            }
            break;

          case 'pong':
            // Heartbeat response
            break;

          case 'error':
            setError(message.data.message || 'Unknown server error');
            break;

          default:
            console.warn('[WorkflowWS] Unknown message type:', message.type);
        }
      } catch (err) {
        console.error('[WorkflowWS] Error parsing message:', err);
      }
    },
    [workflowStore, metricsStore]
  );

  // Connect function
  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      setConnectionState('connecting');
      setError(null);

      const wsUrl = `${url}?sessionId=${encodeURIComponent(sessionId)}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        // Connection confirmation will come via 'connection' message
      };

      ws.onmessage = handleMessage;

      ws.onerror = () => {
        setConnectionState('error');
        setError('WebSocket connection error');
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
        setConnectionState('disconnected');
        wsRef.current = null;

        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }

        // Attempt reconnect if enabled
        if (reconnect && reconnectCount < 10) {
          const delay = 1000 * Math.pow(2, reconnectCount); // Exponential backoff

          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectCount((prev) => prev + 1);
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;

      // Start heartbeat
      heartbeatIntervalRef.current = setInterval(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ action: 'ping' }));
        }
      }, 30000);
    } catch (err) {
      setConnectionState('error');
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  }, [url, sessionId, reconnect, reconnectCount, handleMessage]);

  // Disconnect function
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionState('disconnected');
    setReconnectCount(0);
  }, []);

  // Subscribe to event
  const subscribe = useCallback((eventType: string) => {
    subscriptionsRef.current.add(eventType);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'subscribe', payload: { eventType } }));
    }
  }, []);

  // Unsubscribe from event
  const unsubscribe = useCallback((eventType: string) => {
    subscriptionsRef.current.delete(eventType);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'unsubscribe', payload: { eventType } }));
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect]); // Only run on mount/unmount

  return {
    isConnected,
    connectionState,
    error,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    reconnectCount,
  };
}
