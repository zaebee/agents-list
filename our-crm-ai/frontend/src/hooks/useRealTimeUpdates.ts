/**
 * React Hook for Real-time Updates via WebSocket
 * Provides a convenient way to handle real-time data in React components
 */

import { useEffect, useCallback, useRef } from 'react';
import { webSocketService, SocketEvents } from '../services/WebSocketService';

interface UseRealTimeUpdatesOptions {
  autoConnect?: boolean;
  room?: string; // Join specific room for targeted updates
  onConnectionChange?: (connected: boolean) => void;
  onError?: (error: any) => void;
}

export function useRealTimeUpdates(options: UseRealTimeUpdatesOptions = {}) {
  const {
    autoConnect = true,
    room,
    onConnectionChange,
    onError
  } = options;

  const listenersRef = useRef<Map<string, Function>>(new Map());

  useEffect(() => {
    if (autoConnect) {
      webSocketService.connect();
    }

    // Setup connection status listener
    const handleConnectionStatus = (data: { connected: boolean; reason?: string }) => {
      onConnectionChange?.(data.connected);
      if (!data.connected && data.reason) {
        console.warn('WebSocket disconnected:', data.reason);
      }
    };

    const handleConnectionFailed = (data: { error: string }) => {
      onError?.(new Error(data.error));
    };

    webSocketService.onInternal('connection_status', handleConnectionStatus);
    webSocketService.onInternal('connection_failed', handleConnectionFailed);

    // Join room if specified
    if (room) {
      const joinRoomWithDelay = () => {
        if (webSocketService.isConnected) {
          webSocketService.joinRoom(room);
        } else {
          // Wait for connection and try again
          setTimeout(joinRoomWithDelay, 1000);
        }
      };
      joinRoomWithDelay();
    }

    return () => {
      // Cleanup listeners
      listenersRef.current.forEach((callback, event) => {
        webSocketService.off(event as any, callback as any);
      });
      listenersRef.current.clear();

      // Leave room if specified
      if (room) {
        webSocketService.leaveRoom(room);
      }
    };
  }, [autoConnect, room, onConnectionChange, onError]);

  // Function to subscribe to events with automatic cleanup
  const subscribe = useCallback(<K extends keyof SocketEvents>(
    event: K,
    callback: SocketEvents[K]
  ) => {
    webSocketService.on(event, callback);
    listenersRef.current.set(event, callback as any);

    // Return unsubscribe function
    return () => {
      webSocketService.off(event, callback);
      listenersRef.current.delete(event);
    };
  }, []);

  // Function to emit events to server
  const emit = useCallback((event: string, data?: any) => {
    webSocketService.emit_to_server(event, data);
  }, []);

  // Function to emit with acknowledgment
  const emitWithAck = useCallback((event: string, data?: any) => {
    return webSocketService.emitWithAck(event, data);
  }, []);

  return {
    subscribe,
    emit,
    emitWithAck,
    isConnected: webSocketService.isConnected,
    socketId: webSocketService.socketId,
    connect: () => webSocketService.connect(),
    disconnect: () => webSocketService.disconnect(),
  };
}

// Specialized hooks for different use cases

/**
 * Hook for agent status updates
 */
export function useAgentUpdates(onAgentUpdate?: (data: any) => void) {
  const { subscribe } = useRealTimeUpdates({ room: 'agents' });

  useEffect(() => {
    if (!onAgentUpdate) return;

    const unsubscribers = [
      subscribe('agent_status_update', onAgentUpdate),
      subscribe('agent_connected', onAgentUpdate),
      subscribe('agent_disconnected', onAgentUpdate),
    ];

    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [subscribe, onAgentUpdate]);
}

/**
 * Hook for task updates
 */
export function useTaskUpdates(onTaskUpdate?: (data: any) => void) {
  const { subscribe } = useRealTimeUpdates({ room: 'tasks' });

  useEffect(() => {
    if (!onTaskUpdate) return;

    const unsubscribers = [
      subscribe('task_created', onTaskUpdate),
      subscribe('task_updated', onTaskUpdate),
      subscribe('task_completed', onTaskUpdate),
      subscribe('task_failed', onTaskUpdate),
    ];

    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [subscribe, onTaskUpdate]);
}

/**
 * Hook for system status updates
 */
export function useSystemUpdates(onSystemUpdate?: (data: any) => void) {
  const { subscribe } = useRealTimeUpdates({ room: 'system' });

  useEffect(() => {
    if (!onSystemUpdate) return;

    const unsubscribers = [
      subscribe('system_status_update', onSystemUpdate),
      subscribe('notification', (data) => {
        // Show notification (could integrate with toast library)
        console.log('Notification:', data);
        onSystemUpdate?.(data);
      }),
    ];

    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [subscribe, onSystemUpdate]);
}

/**
 * Hook for dashboard data updates
 */
export function useDashboardUpdates(onDashboardUpdate?: (data: any) => void) {
  const { subscribe } = useRealTimeUpdates({ room: 'dashboard' });

  useEffect(() => {
    if (!onDashboardUpdate) return;

    const unsubscribers = [
      subscribe('dashboard_data_update', onDashboardUpdate),
      subscribe('metrics_update', onDashboardUpdate),
    ];

    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [subscribe, onDashboardUpdate]);
}