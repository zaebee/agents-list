// Types for the AI-CRM system

export interface Task {
  id: string;
  title: string;
  description: string;
  column_name: 'To Do' | 'In Progress' | 'Done';
  owner?: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  owner?: string;
  no_ai_suggest?: boolean;
}

export interface TaskUpdate {
  owner?: string;
}

export interface TaskMove {
  column: 'To Do' | 'In Progress' | 'Done';
}

export interface TaskComment {
  message: string;
}

export interface TaskDetails extends Task {
  comments: Array<{
    text: string;
  }>;
}

export interface AgentSuggestion {
  agent: string;
  confidence: number;
  matched_keywords: string[];
  reasoning: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

export interface PMAnalysis {
  type: 'direct_assignment' | 'complex_task';
  task?: {
    title: string;
    description: string;
  };
  original_task?: {
    title: string;
    description: string;
  };
  analysis: {
    complexity: string;
    estimated_hours: number;
    required_agents: string[];
    risk_factors: string[];
    success_criteria: string[];
  };
  priority: string;
  assigned_agent?: string;
  subtasks?: Array<{
    title: string;
    description: string;
    agent: string;
    estimated_hours: number;
    depends_on?: string;
  }>;
  recommendation: string;
}

export type ColumnName = 'To Do' | 'In Progress' | 'Done';

// Analytics Types
export interface TaskCompletionAnalytics {
  totalTasks: number;
  completedTasks: number;
  completionRate: number;
}

export interface AgentPerformanceData {
  [agent: string]: {
    totalTasks: number;
    completedTasks: number;
    successRate: number;
  };
}

export interface ExecutiveDashboardData {
  systemOverview: {
    totalAgents: number;
    activeIntegrations: number;
    systemHealth: number;
  };
  performanceKPIs: {
    taskCompletionRate: number;
    topPerformingAgents: Array<{
      agent: string;
      successRate: number;
    }>;
    workflowEfficiency: number;
  };
}

export interface AnalyticsData {
  taskCompletion: TaskCompletionAnalytics;
  agentPerformance: AgentPerformanceData;
  executiveDashboard: ExecutiveDashboardData;
}

// WebSocket and Real-time Types
export interface WebSocketMessage {
  type: 'task_updated' | 'task_created' | 'task_moved' | 'task_assigned' | 'task_completed' | 'connection_status';
  data: any;
  timestamp: string;
}

export interface TaskUpdateEvent {
  taskId: string;
  task: Task;
  previousState?: Partial<Task>;
  updatedBy?: string;
}

export interface TaskMoveEvent {
  taskId: string;
  task: Task;
  fromColumn: ColumnName;
  toColumn: ColumnName;
  movedBy?: string;
}

export interface TaskAssignedEvent {
  taskId: string;
  task: Task;
  assignedTo: string;
  assignedBy?: string;
}

export interface TaskCreatedEvent {
  task: Task;
  createdBy?: string;
}

export interface TaskCompletedEvent {
  taskId: string;
  task: Task;
  completedBy?: string;
  completedAt: string;
}

export interface ConnectionStatusEvent {
  status: 'connected' | 'disconnected' | 'reconnecting' | 'error';
  message?: string;
}

export type WebSocketEventType = 
  | 'task_updated'
  | 'task_created'
  | 'task_moved'
  | 'task_assigned'
  | 'task_completed'
  | 'connection_status';

// Notification Types
export interface NotificationPreferences {
  enabled: boolean;
  taskAssigned: boolean;
  taskCompleted: boolean;
  taskMoved: boolean;
  taskCreated: boolean;
  soundEnabled: boolean;
}

// Real-time UI State
export interface ConnectionState {
  status: 'connected' | 'disconnected' | 'reconnecting' | 'error';
  message?: string;
  lastConnected?: Date;
  reconnectAttempts?: number;
}

export interface TaskAnimationState {
  isMoving: boolean;
  isUpdating: boolean;
  isNew: boolean;
  lastUpdate?: Date;
}