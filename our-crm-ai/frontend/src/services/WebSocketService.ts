/**
 * WebSocket Service for Real-time Updates
 * Handles real-time communication with the backend
 */

import { io, Socket } from 'socket.io-client';

export interface SocketEvents {
  // Agent events
  agent_status_update: (data: { agent_id: string; status: string }) => void;
  agent_connected: (data: { agent_id: string; name: string }) => void;
  agent_disconnected: (data: { agent_id: string; name: string }) => void;
  
  // Task events  
  task_created: (data: { task_id: string; description: string; status: string }) => void;
  task_updated: (data: { task_id: string; status: string; progress?: number }) => void;
  task_completed: (data: { task_id: string; result: any }) => void;
  task_failed: (data: { task_id: string; error: string }) => void;
  
  // System events
  system_status_update: (data: { status: string; active_agents: number; total_agents: number }) => void;
  notification: (data: { type: 'info' | 'warning' | 'error' | 'success'; message: string; timestamp: string }) => void;
  
  // Dashboard events
  dashboard_data_update: (data: any) => void;
  metrics_update: (data: { total_projects: number; revenue: number; active_agents: number }) => void;
}

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<Function>> = new Map();

  /**
   * Connect to WebSocket server
   */
  connect(serverURL?: string): void {
    if (this.socket?.connected) {
      console.log('WebSocket already connected');
      return;
    }

    const url = serverURL || 
      (process.env.NODE_ENV === 'development' 
        ? 'http://zae.life:5001' 
        : window.location.origin);

    console.log('Connecting to WebSocket server:', url);

    this.socket = io(url, {
      transports: ['websocket', 'polling'],
      timeout: 10000,
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    });

    this.setupEventListeners();
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      console.log('Disconnecting from WebSocket server');
      this.socket.disconnect();
      this.socket = null;
      this.reconnectAttempts = 0;
    }
  }

  /**
   * Setup basic WebSocket event listeners
   */
  private setupEventListeners(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected successfully');
      this.reconnectAttempts = 0;
      this.emit('connection_status', { connected: true });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.emit('connection_status', { connected: false, reason });
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.reconnectAttempts++;
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
        this.emit('connection_failed', { error: 'Max reconnection attempts reached' });
      }
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('WebSocket reconnected after', attemptNumber, 'attempts');
      this.reconnectAttempts = 0;
      this.emit('connection_status', { connected: true, reconnected: true });
    });

    this.socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed');
      this.emit('connection_failed', { error: 'Reconnection failed' });
    });
  }

  /**
   * Subscribe to a specific event
   */
  on<K extends keyof SocketEvents>(event: K, callback: SocketEvents[K]): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    
    this.listeners.get(event)!.add(callback);

    // Also listen on the socket if connected
    if (this.socket) {
      this.socket.on(event, callback as any);
    }
  }

  /**
   * Subscribe to internal events (connection status, etc.)
   */
  onInternal(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  /**
   * Unsubscribe from a specific event
   */
  off<K extends keyof SocketEvents>(event: K, callback?: SocketEvents[K]): void {
    const eventListeners = this.listeners.get(event);
    
    if (eventListeners) {
      if (callback) {
        eventListeners.delete(callback);
        // Also remove from socket
        if (this.socket) {
          this.socket.off(event, callback as any);
        }
      } else {
        // Remove all listeners for this event
        eventListeners.clear();
        if (this.socket) {
          this.socket.off(event);
        }
      }
    }
  }

  /**
   * Emit an event to all listeners
   */
  private emit(event: string, data: any): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in WebSocket event callback:', error);
        }
      });
    }
  }

  /**
   * Send data to server
   */
  emit_to_server(event: string, data?: any): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('WebSocket not connected, cannot emit event:', event);
    }
  }

  /**
   * Send data to server with acknowledgment
   */
  emitWithAck(event: string, data?: any): Promise<any> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        this.socket.emit(event, data, (response: any) => {
          resolve(response);
        });
      } else {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  /**
   * Join a room for targeted updates
   */
  joinRoom(room: string): void {
    this.emit_to_server('join_room', { room });
  }

  /**
   * Leave a room
   */
  leaveRoom(room: string): void {
    this.emit_to_server('leave_room', { room });
  }

  /**
   * Get connection status
   */
  get isConnected(): boolean {
    return this.socket?.connected || false;
  }

  /**
   * Get socket ID
   */
  get socketId(): string | undefined {
    return this.socket?.id;
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService();

// Export a React hook for easier integration
export function useWebSocket() {
  return {
    connect: (url?: string) => webSocketService.connect(url),
    disconnect: () => webSocketService.disconnect(),
    on: <K extends keyof SocketEvents>(event: K, callback: SocketEvents[K]) => 
      webSocketService.on(event, callback),
    off: <K extends keyof SocketEvents>(event: K, callback?: SocketEvents[K]) => 
      webSocketService.off(event, callback),
    onInternal: (event: string, callback: Function) => 
      webSocketService.onInternal(event, callback),
    emit: (event: string, data?: any) => 
      webSocketService.emit_to_server(event, data),
    emitWithAck: (event: string, data?: any) => 
      webSocketService.emitWithAck(event, data),
    joinRoom: (room: string) => webSocketService.joinRoom(room),
    leaveRoom: (room: string) => webSocketService.leaveRoom(room),
    isConnected: webSocketService.isConnected,
    socketId: webSocketService.socketId,
  };
}
