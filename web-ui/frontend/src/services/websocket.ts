// WebSocket service for real-time communication with backend

import { Task, ColumnName } from '../types';

export interface WebSocketMessage {
  type: 'task_updated' | 'task_created' | 'task_moved' | 'task_assigned' | 'task_completed' | 'connection_status';
  data: any;
  timestamp: string;
}

export interface TaskUpdateEvent {
  taskId: string;
  task: Task;
  previousState?: Partial<Task>;
}

export interface TaskMoveEvent {
  taskId: string;
  task: Task;
  fromColumn: ColumnName;
  toColumn: ColumnName;
}

export interface TaskAssignedEvent {
  taskId: string;
  task: Task;
  assignedTo: string;
  assignedBy?: string;
}

export interface ConnectionStatusEvent {
  status: 'connected' | 'disconnected' | 'reconnecting' | 'error';
  message?: string;
}

export type WebSocketEventHandler = (message: WebSocketMessage) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private eventHandlers: Map<string, WebSocketEventHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private connectionStatus: 'connected' | 'disconnected' | 'reconnecting' | 'error' = 'disconnected';

  constructor() {
    this.connect();
  }

  // Get WebSocket URL from environment or default
  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.REACT_APP_WS_URL || 
                 (process.env.REACT_APP_API_URL?.replace(/^https?/, protocol.slice(0, -1))) ||
                 `${protocol}//${window.location.host}`;
    
    // Remove trailing slash and add /ws path
    return `${host.replace(/\/$/, '')}/ws`;
  }

  // Connect to WebSocket server
  connect(): void {
    if (this.isConnecting || this.ws?.readyState === WebSocket.CONNECTING) {
      return;
    }

    this.isConnecting = true;
    const wsUrl = this.getWebSocketUrl();

    try {
      this.ws = new WebSocket(wsUrl);
      this.setupEventListeners();
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.handleConnectionError();
    }
  }

  // Setup WebSocket event listeners
  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.connectionStatus = 'connected';
      this.emit('connection_status', { status: 'connected' });
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.isConnecting = false;
      
      if (event.code !== 1000) { // Not a normal closure
        this.handleConnectionError();
      } else {
        this.connectionStatus = 'disconnected';
        this.emit('connection_status', { status: 'disconnected' });
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.handleConnectionError();
    };
  }

  // Handle connection errors and implement reconnection logic
  private handleConnectionError(): void {
    this.isConnecting = false;
    this.connectionStatus = 'error';
    this.emit('connection_status', { 
      status: 'error',
      message: 'Connection failed'
    });

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      this.connectionStatus = 'reconnecting';
      this.emit('connection_status', { 
        status: 'reconnecting',
        message: `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`
      });

      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  // Handle incoming WebSocket messages
  private handleMessage(message: WebSocketMessage): void {
    console.log('WebSocket message received:', message);
    
    const handlers = this.eventHandlers.get(message.type) || [];
    handlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in WebSocket event handler:', error);
      }
    });

    // Emit to 'all' listeners
    const allHandlers = this.eventHandlers.get('*') || [];
    allHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in WebSocket universal event handler:', error);
      }
    });
  }

  // Send message to server
  send(message: any): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        return false;
      }
    }
    return false;
  }

  // Subscribe to WebSocket events
  on(eventType: string | '*', handler: WebSocketEventHandler): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    
    this.eventHandlers.get(eventType)!.push(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(eventType);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }

  // Emit event to handlers
  private emit(eventType: string, data: any): void {
    const message: WebSocketMessage = {
      type: eventType as any,
      data,
      timestamp: new Date().toISOString()
    };
    this.handleMessage(message);
  }

  // Disconnect WebSocket
  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.connectionStatus = 'disconnected';
  }

  // Get current connection status
  getConnectionStatus(): 'connected' | 'disconnected' | 'reconnecting' | 'error' {
    return this.connectionStatus;
  }

  // Check if connected
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // Manually trigger reconnection
  reconnect(): void {
    this.disconnect();
    this.reconnectAttempts = 0;
    setTimeout(() => this.connect(), 100);
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();

export default websocketService;