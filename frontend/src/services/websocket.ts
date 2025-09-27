/**
 * WebSocket实时通信服务
 * 提供自动重连、心跳保活、消息队列等功能
 */

interface WebSocketConfig {
  url: string;
  protocols?: string[];
  heartbeatInterval?: number;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  debug?: boolean;
}

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  message_id: string;
  user_id?: string;
  room_id?: string;
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  requires_ack?: boolean;
}

interface ConnectionState {
  isConnected: boolean;
  isConnecting: boolean;
  reconnectAttempts: number;
  lastConnected?: Date;
  lastDisconnected?: Date;
}

interface EventListener {
  event: string;
  callback: (data: any) => void;
  once?: boolean;
}

type EventCallback = (data: any) => void;
type ConnectionCallback = (state: ConnectionState) => void;
type ErrorCallback = (error: Error) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private state: ConnectionState;
  private eventListeners: Map<string, EventListener[]> = new Map();
  private messageQueue: WebSocketMessage[] = [];
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private connectionCallbacks: ConnectionCallback[] = [];
  private errorCallbacks: ErrorCallback[] = [];
  private userInfo: { userId: string; username: string } | null = null;

  constructor(config: WebSocketConfig) {
    this.config = {
      url: config.url,
      protocols: config.protocols || [],
      heartbeatInterval: config.heartbeatInterval || 30000, // 30秒
      reconnectInterval: config.reconnectInterval || 5000,   // 5秒
      maxReconnectAttempts: config.maxReconnectAttempts || 10,
      debug: config.debug || false
    };

    this.state = {
      isConnected: false,
      isConnecting: false,
      reconnectAttempts: 0
    };

    // 页面可见性变化处理
    this.setupVisibilityHandler();

    // 页面卸载处理
    this.setupUnloadHandler();
  }

  /**
   * 连接到WebSocket服务器
   */
  async connect(userInfo: { userId: string; username: string }): Promise<void> {
    if (this.state.isConnected || this.state.isConnecting) {
      this.log('已经连接或正在连接中');
      return;
    }

    this.userInfo = userInfo;
    this.state.isConnecting = true;
    this.notifyConnectionChange();

    try {
      await this.createConnection();
    } catch (error) {
      this.state.isConnecting = false;
      this.notifyConnectionChange();
      throw error;
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.log('手动断开连接');
    this.cleanup();

    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
    }

    this.state.isConnected = false;
    this.state.isConnecting = false;
    this.state.reconnectAttempts = 0;
    this.state.lastDisconnected = new Date();
    this.notifyConnectionChange();
  }

  /**
   * 发送消息
   */
  send(type: string, data: any, options: {
    roomId?: string;
    priority?: 'low' | 'normal' | 'high' | 'urgent';
    requiresAck?: boolean;
  } = {}): void {
    const message: WebSocketMessage = {
      type,
      data,
      timestamp: new Date().toISOString(),
      message_id: this.generateMessageId(),
      user_id: this.userInfo?.userId,
      room_id: options.roomId,
      priority: options.priority || 'normal',
      requires_ack: options.requiresAck || false
    };

    if (this.state.isConnected && this.ws) {
      this.ws.send(JSON.stringify(message));
      this.log('发送消息:', message);
    } else {
      // 将消息加入队列，连接后发送
      this.messageQueue.push(message);
      this.log('消息已加入队列:', message);
    }
  }

  /**
   * 监听事件
   */
  on(event: string, callback: EventCallback): () => void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }

    const listener: EventListener = { event, callback };
    this.eventListeners.get(event)!.push(listener);

    // 返回移除监听器的函数
    return () => this.off(event, callback);
  }

  /**
   * 监听事件（一次性）
   */
  once(event: string, callback: EventCallback): () => void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }

    const listener: EventListener = { event, callback, once: true };
    this.eventListeners.get(event)!.push(listener);

    return () => this.off(event, callback);
  }

  /**
   * 移除事件监听器
   */
  off(event: string, callback?: EventCallback): void {
    if (!callback) {
      // 移除所有监听器
      this.eventListeners.delete(event);
      return;
    }

    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.findIndex(l => l.callback === callback);
      if (index !== -1) {
        listeners.splice(index, 1);
        if (listeners.length === 0) {
          this.eventListeners.delete(event);
        }
      }
    }
  }

  /**
   * 监听连接状态变化
   */
  onConnectionChange(callback: ConnectionCallback): () => void {
    this.connectionCallbacks.push(callback);
    return () => {
      const index = this.connectionCallbacks.indexOf(callback);
      if (index !== -1) {
        this.connectionCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * 监听错误
   */
  onError(callback: ErrorCallback): () => void {
    this.errorCallbacks.push(callback);
    return () => {
      const index = this.errorCallbacks.indexOf(callback);
      if (index !== -1) {
        this.errorCallbacks.splice(index, 1);
      }
    };
  }

  /**
   * 加入房间
   */
  joinRoom(roomId: string, roomName?: string): void {
    this.send('user_join_project', {
      room_id: roomId,
      room_name: roomName,
      user_id: this.userInfo?.userId,
      username: this.userInfo?.username
    });
  }

  /**
   * 离开房间
   */
  leaveRoom(roomId: string): void {
    this.send('user_leave_project', {
      room_id: roomId,
      user_id: this.userInfo?.userId
    });
  }

  /**
   * 发送心跳
   */
  private sendHeartbeat(): void {
    if (this.state.isConnected) {
      this.send('heartbeat', {
        timestamp: new Date().toISOString(),
        user_id: this.userInfo?.userId
      });
    }
  }

  /**
   * 开始心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat();
    }, this.config.heartbeatInterval);
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * 创建WebSocket连接
   */
  private async createConnection(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.buildConnectionUrl();
        this.log('正在连接:', wsUrl);

        this.ws = new WebSocket(wsUrl, this.config.protocols);

        this.ws.onopen = () => {
          this.log('WebSocket连接已建立');
          this.state.isConnected = true;
          this.state.isConnecting = false;
          this.state.reconnectAttempts = 0;
          this.state.lastConnected = new Date();

          this.startHeartbeat();
          this.processMessageQueue();
          this.notifyConnectionChange();

          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            this.log('解析消息失败:', error);
            this.notifyError(new Error('消息解析失败'));
          }
        };

        this.ws.onclose = (event) => {
          this.log('WebSocket连接已关闭:', event.code, event.reason);
          this.handleDisconnection(event.code !== 1000); // 非正常关闭才重连
        };

        this.ws.onerror = (error) => {
          this.log('WebSocket错误:', error);
          this.notifyError(new Error('WebSocket连接错误'));
          reject(error);
        };

      } catch (error) {
        this.log('创建连接失败:', error);
        reject(error);
      }
    });
  }

  /**
   * 处理断开连接
   */
  private handleDisconnection(shouldReconnect: boolean = true): void {
    this.state.isConnected = false;
    this.state.isConnecting = false;
    this.state.lastDisconnected = new Date();
    this.stopHeartbeat();
    this.notifyConnectionChange();

    if (shouldReconnect && this.state.reconnectAttempts < this.config.maxReconnectAttempts) {
      this.scheduleReconnect();
    } else if (this.state.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.log('达到最大重连次数，停止重连');
      this.notifyError(new Error('连接失败：达到最大重连次数'));
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return;
    }

    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.state.reconnectAttempts),
      30000 // 最大30秒
    );

    this.log(`${delay}ms后尝试重连 (第${this.state.reconnectAttempts + 1}次)`);

    this.reconnectTimer = setTimeout(async () => {
      this.reconnectTimer = null;
      this.state.reconnectAttempts++;

      if (this.userInfo) {
        try {
          await this.connect(this.userInfo);
        } catch (error) {
          this.log('重连失败:', error);
        }
      }
    }, delay);
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage): void {
    this.log('收到消息:', message);

    // 触发对应的事件监听器
    const listeners = this.eventListeners.get(message.type) || [];

    for (let i = listeners.length - 1; i >= 0; i--) {
      const listener = listeners[i];
      try {
        listener.callback(message.data);

        // 如果是一次性监听器，移除它
        if (listener.once) {
          listeners.splice(i, 1);
        }
      } catch (error) {
        this.log('事件处理器执行失败:', error);
      }
    }

    // 如果没有监听器，触发通用事件
    if (listeners.length === 0) {
      const allListeners = this.eventListeners.get('*') || [];
      allListeners.forEach(listener => {
        try {
          listener.callback({ type: message.type, data: message.data });
        } catch (error) {
          this.log('通用事件处理器执行失败:', error);
        }
      });
    }
  }

  /**
   * 处理消息队列
   */
  private processMessageQueue(): void {
    if (this.messageQueue.length > 0) {
      this.log(`处理消息队列，共${this.messageQueue.length}条消息`);

      const messages = [...this.messageQueue];
      this.messageQueue = [];

      messages.forEach(message => {
        if (this.ws && this.state.isConnected) {
          this.ws.send(JSON.stringify(message));
        }
      });
    }
  }

  /**
   * 构建连接URL
   */
  private buildConnectionUrl(): string {
    const url = new URL(this.config.url);

    if (this.userInfo) {
      url.searchParams.set('user_id', this.userInfo.userId);
      url.searchParams.set('username', this.userInfo.username);
    }

    return url.toString();
  }

  /**
   * 生成消息ID
   */
  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 清理资源
   */
  private cleanup(): void {
    this.stopHeartbeat();

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * 设置页面可见性处理
   */
  private setupVisibilityHandler(): void {
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', () => {
        if (!document.hidden && !this.state.isConnected && this.userInfo) {
          // 页面变为可见且未连接时，尝试重连
          this.log('页面变为可见，尝试重连');
          this.connect(this.userInfo).catch(error => {
            this.log('页面可见时重连失败:', error);
          });
        }
      });
    }
  }

  /**
   * 设置页面卸载处理
   */
  private setupUnloadHandler(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.disconnect();
      });
    }
  }

  /**
   * 通知连接状态变化
   */
  private notifyConnectionChange(): void {
    this.connectionCallbacks.forEach(callback => {
      try {
        callback({ ...this.state });
      } catch (error) {
        this.log('连接状态回调执行失败:', error);
      }
    });
  }

  /**
   * 通知错误
   */
  private notifyError(error: Error): void {
    this.errorCallbacks.forEach(callback => {
      try {
        callback(error);
      } catch (err) {
        this.log('错误回调执行失败:', err);
      }
    });
  }

  /**
   * 日志输出
   */
  private log(...args: any[]): void {
    if (this.config.debug) {
      console.log('[WebSocket]', ...args);
    }
  }

  /**
   * 获取连接状态
   */
  getState(): ConnectionState {
    return { ...this.state };
  }

  /**
   * 获取在线用户列表
   */
  getOnlineUsers(roomId?: string): void {
    this.send('get_online_users', { room_id: roomId });
  }

  /**
   * 获取房间信息
   */
  getRoomInfo(roomId: string): void {
    this.send('get_room_info', { room_id: roomId });
  }
}

// 创建单例实例
let wsInstance: WebSocketService | null = null;

/**
 * 创建或获取WebSocket服务实例
 */
export function createWebSocketService(config: WebSocketConfig): WebSocketService {
  if (!wsInstance) {
    wsInstance = new WebSocketService(config);
  }
  return wsInstance;
}

/**
 * 获取WebSocket服务实例
 */
export function getWebSocketService(): WebSocketService | null {
  return wsInstance;
}

// 导出类型
export type {
  WebSocketConfig,
  WebSocketMessage,
  ConnectionState,
  EventCallback,
  ConnectionCallback,
  ErrorCallback
};

export default WebSocketService;