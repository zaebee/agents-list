// Connection status indicator component for WebSocket connection

import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, RefreshCw, AlertCircle, Check } from 'lucide-react';
import websocketService from '../services/websocket';
import { ConnectionState, WebSocketMessage } from '../types';

interface ConnectionStatusProps {
  className?: string;
  showDetails?: boolean;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ 
  className = '', 
  showDetails = false 
}) => {
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    status: 'disconnected',
    reconnectAttempts: 0
  });
  
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    // Subscribe to connection status changes
    const unsubscribe = websocketService.on('connection_status', (message: WebSocketMessage) => {
      const statusData = message.data as any;
      setConnectionState(prev => ({
        ...prev,
        status: statusData.status,
        message: statusData.message,
        lastConnected: statusData.status === 'connected' ? new Date() : prev.lastConnected,
        reconnectAttempts: statusData.status === 'reconnecting' ? (prev.reconnectAttempts || 0) + 1 : 0
      }));
    });

    // Initialize with current status
    setConnectionState(prev => ({
      ...prev,
      status: websocketService.getConnectionStatus()
    }));

    return unsubscribe;
  }, []);

  const getStatusIcon = () => {
    switch (connectionState.status) {
      case 'connected':
        return <Check className="text-green-500" size={16} />;
      case 'disconnected':
        return <WifiOff className="text-red-500" size={16} />;
      case 'reconnecting':
        return <RefreshCw className="text-yellow-500 animate-spin" size={16} />;
      case 'error':
        return <AlertCircle className="text-red-500" size={16} />;
      default:
        return <Wifi className="text-gray-400" size={16} />;
    }
  };

  const getStatusColor = () => {
    switch (connectionState.status) {
      case 'connected':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'disconnected':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'reconnecting':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusText = () => {
    switch (connectionState.status) {
      case 'connected':
        return 'Real-time updates active';
      case 'disconnected':
        return 'Offline mode';
      case 'reconnecting':
        return `Reconnecting... (${connectionState.reconnectAttempts || 1})`;
      case 'error':
        return connectionState.message || 'Connection error';
      default:
        return 'Unknown status';
    }
  };

  const handleReconnect = () => {
    websocketService.reconnect();
  };

  const canReconnect = connectionState.status === 'disconnected' || connectionState.status === 'error';

  if (!showDetails) {
    // Compact version for header
    return (
      <div 
        className={`relative flex items-center space-x-1 ${className}`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {getStatusIcon()}
        {canReconnect && (
          <button
            onClick={handleReconnect}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            title="Reconnect"
          >
            <RefreshCw size={12} />
          </button>
        )}
        
        {/* Tooltip */}
        {showTooltip && (
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded whitespace-nowrap z-50">
            {getStatusText()}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800"></div>
          </div>
        )}
      </div>
    );
  }

  // Detailed version for dashboard
  return (
    <div className={`flex items-center space-x-3 p-3 rounded-lg border ${getStatusColor()} ${className}`}>
      {getStatusIcon()}
      
      <div className="flex-1">
        <div className="font-medium text-sm">
          {getStatusText()}
        </div>
        
        {connectionState.lastConnected && (
          <div className="text-xs opacity-75 mt-1">
            Last connected: {connectionState.lastConnected.toLocaleTimeString()}
          </div>
        )}
      </div>

      {canReconnect && (
        <button
          onClick={handleReconnect}
          className="px-3 py-1 text-xs font-medium bg-white bg-opacity-50 rounded-md hover:bg-opacity-75 transition-colors"
        >
          Reconnect
        </button>
      )}
    </div>
  );
};

// Hook for accessing connection state in other components
export const useConnectionStatus = () => {
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    status: 'disconnected',
    reconnectAttempts: 0
  });

  useEffect(() => {
    const unsubscribe = websocketService.on('connection_status', (message: WebSocketMessage) => {
      const statusData = message.data as any;
      setConnectionState(prev => ({
        ...prev,
        status: statusData.status,
        message: statusData.message,
        lastConnected: statusData.status === 'connected' ? new Date() : prev.lastConnected,
        reconnectAttempts: statusData.status === 'reconnecting' ? (prev.reconnectAttempts || 0) + 1 : 0
      }));
    });

    // Initialize with current status
    setConnectionState(prev => ({
      ...prev,
      status: websocketService.getConnectionStatus()
    }));

    return unsubscribe;
  }, []);

  return {
    connectionState,
    isConnected: connectionState.status === 'connected',
    reconnect: () => websocketService.reconnect()
  };
};

export default ConnectionStatus;