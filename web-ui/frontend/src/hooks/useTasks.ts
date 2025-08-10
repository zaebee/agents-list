// Custom React hook for task management with real-time updates

import { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'react-toastify';
import { apiService } from '../services/api';
import websocketService from '../services/websocket';
import { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'react-toastify';
import { apiService } from '../services/api';
import websocketService from '../services/websocket';
import notificationService from '../services/notifications';
import {
  Task,
  TaskCreate,
  TaskUpdate,
  ColumnName,
  WebSocketMessage,
  TaskUpdateEvent,
  TaskMoveEvent,
  TaskAssignedEvent,
  TaskCreatedEvent,
  TaskCompletedEvent,
  TaskAnimationState
} from '../types';

export const useTasks = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [archivedTasks, setArchivedTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [taskAnimations, setTaskAnimations] = useState<Map<string, TaskAnimationState>>(new Map());
  
  // Track optimistic updates for rollback functionality
  const optimisticUpdates = useRef<Map<string, { original: Task; timeout: NodeJS.Timeout }>>(new Map());
  
  // Track if component is mounted to prevent state updates after unmount
  const mountedRef = useRef(true);

  // Animation helper functions
  const setTaskAnimation = useCallback((taskId: string, animation: Partial<TaskAnimationState>) => {
    setTaskAnimations(prev => {
      const newMap = new Map(prev);
      const current = newMap.get(taskId) || { isMoving: false, isUpdating: false, isNew: false };
      newMap.set(taskId, { ...current, ...animation, lastUpdate: new Date() });
      return newMap;
    });
  }, []);

  const clearTaskAnimation = useCallback((taskId: string, delay = 2000) => {
    setTimeout(() => {
      if (mountedRef.current) {
        setTaskAnimations(prev => {
          const newMap = new Map(prev);
          newMap.delete(taskId);
          return newMap;
        });
      }
    }, delay);
  }, []);

  // Optimistic update helpers
  const addOptimisticUpdate = useCallback((taskId: string, originalTask: Task) => {
    const timeout = setTimeout(() => {
      optimisticUpdates.current.delete(taskId);
    }, 10000); // Clear after 10 seconds
    
    optimisticUpdates.current.set(taskId, { original: originalTask, timeout });
  }, []);

  const rollbackOptimisticUpdate = useCallback((taskId: string) => {
    const update = optimisticUpdates.current.get(taskId);
    if (update && mountedRef.current) {
      clearTimeout(update.timeout);
      optimisticUpdates.current.delete(taskId);
      
      // Restore original task
      setTasks(prevTasks => 
        prevTasks.map(task => task.id === taskId ? update.original : task)
      );
      
      setTaskAnimation(taskId, { isUpdating: false, isMoving: false });
    }
  }, [setTaskAnimation]);

  // WebSocket event handlers
  const handleTaskCreated = useCallback((event: TaskCreatedEvent) => {
    if (!mountedRef.current) return;
    
    const newTask = event.task;
    
    setTasks(prevTasks => {
      // Check if task already exists (avoid duplicates)
      const exists = prevTasks.some(task => task.id === newTask.id);
      if (exists) return prevTasks;
      
      return [...prevTasks, newTask];
    });
    
    setTaskAnimation(newTask.id, { isNew: true });
    clearTaskAnimation(newTask.id);
    
    // Show notification
    notificationService.notifyTaskCreated(newTask);
  }, [setTaskAnimation, clearTaskAnimation]);

  const handleTaskUpdated = useCallback((event: TaskUpdateEvent) => {
    if (!mountedRef.current) return;
    
    const { taskId, task } = event;
    
    setTasks(prevTasks => 
      prevTasks.map(prevTask => 
        prevTask.id === taskId ? { ...prevTask, ...task } : prevTask
      )
    );
    
    setTaskAnimation(taskId, { isUpdating: true });
    clearTaskAnimation(taskId);
  }, [setTaskAnimation, clearTaskAnimation]);

  const handleTaskMoved = useCallback((event: TaskMoveEvent) => {
    if (!mountedRef.current) return;
    
    const { taskId, task, fromColumn, toColumn } = event;
    
    setTasks(prevTasks => 
      prevTasks.map(prevTask => 
        prevTask.id === taskId ? { ...prevTask, column_name: toColumn } : prevTask
      )
    );
    
    setTaskAnimation(taskId, { isMoving: true });
    clearTaskAnimation(taskId);
    
    // Show notification for completed tasks
    if (toColumn === 'Done') {
      notificationService.notifyTaskCompleted(task);
    } else {
      notificationService.notifyTaskMoved(task, fromColumn, toColumn);
    }
  }, [setTaskAnimation, clearTaskAnimation]);

  const handleTaskAssigned = useCallback((event: TaskAssignedEvent) => {
    if (!mountedRef.current) return;
    
    const { taskId, task, assignedTo } = event;
    
    setTasks(prevTasks => 
      prevTasks.map(prevTask => 
        prevTask.id === taskId ? { ...prevTask, owner: assignedTo } : prevTask
      )
    );
    
    setTaskAnimation(taskId, { isUpdating: true });
    clearTaskAnimation(taskId);
    
    // Show notification
    notificationService.notifyTaskAssigned(task, assignedTo);
  }, [setTaskAnimation, clearTaskAnimation]);

  const handleTaskCompleted = useCallback((event: TaskCompletedEvent) => {
    if (!mountedRef.current) return;
    
    const { taskId, task } = event;
    
    setTasks(prevTasks => 
      prevTasks.map(prevTask => 
        prevTask.id === taskId ? { ...prevTask, column_name: 'Done' } : prevTask
      )
    );
    
    setTaskAnimation(taskId, { isMoving: true });
    clearTaskAnimation(taskId);
    
    // Show notification
    notificationService.notifyTaskCompleted(task);
  }, [setTaskAnimation, clearTaskAnimation]);

  // Fetch all tasks
  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [tasksData, archivedTasksData] = await Promise.all([
        apiService.listTasks(),
        apiService.listArchivedTasks(),
      ]);
      setTasks(tasksData);
      setArchivedTasks(archivedTasksData);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to fetch tasks';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Create a new task
  const createTask = useCallback(async (taskData: TaskCreate) => {
    try {
      const response = await apiService.createTask(taskData);
      if (response.success) {
        toast.success(response.message);
        await fetchTasks(); // Refresh the task list
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to create task';
      toast.error(errorMessage);
      throw err;
    }
  }, [fetchTasks]);

  // Update task owner
  const updateTaskOwner = useCallback(async (taskId: string, owner: string) => {
    try {
      const update: TaskUpdate = { owner };
      const response = await apiService.updateTask(taskId, update);
      if (response.success) {
        toast.success(response.message);
        await fetchTasks(); // Refresh the task list
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to update task';
      toast.error(errorMessage);
      throw err;
    }
  }, [fetchTasks]);

  // Archive or unarchive a task
  const archiveTask = useCallback(async (taskId: string, archived: boolean) => {
    try {
      const response = await apiService.updateTask(taskId, { archived });
      if (response.success) {
        toast.success(response.message);
        await fetchTasks(); // Refresh the task list
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || (archived ? 'Failed to archive task' : 'Failed to unarchive task');
      toast.error(errorMessage);
      throw err;
    }
  }, [fetchTasks]);

  // Move task to different column with optimistic updates
  const moveTask = useCallback(async (taskId: string, column: ColumnName) => {
    const originalTask = tasks.find(task => task.id === taskId);
    if (!originalTask) return;

    try {
      // Store original task for potential rollback
      addOptimisticUpdate(taskId, originalTask);
      
      // Optimistically update the UI immediately
      setTasks(prevTasks => 
        prevTasks.map(task => 
          task.id === taskId ? { ...task, column_name: column } : task
        )
      );
      
      setTaskAnimation(taskId, { isMoving: true });
      
      // Make API call
      const response = await apiService.moveTask(taskId, { column });
      if (response.success) {
        // Success - clear optimistic update
        const update = optimisticUpdates.current.get(taskId);
        if (update) {
          clearTimeout(update.timeout);
          optimisticUpdates.current.delete(taskId);
        }
        
        clearTaskAnimation(taskId);
        toast.success(response.message);
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to move task';
      toast.error(errorMessage);
      
      // Rollback optimistic update
      rollbackOptimisticUpdate(taskId);
      throw err;
    }
  }, [tasks, addOptimisticUpdate, rollbackOptimisticUpdate, setTaskAnimation, clearTaskAnimation]);

  // Group tasks by column
  const tasksByColumn = {
    'To Do': tasks.filter(task => task.column_name === 'To Do'),
    'In Progress': tasks.filter(task => task.column_name === 'In Progress'),
    'Done': tasks.filter(task => task.column_name === 'Done'),
  };

  // Setup WebSocket listeners and load tasks on mount
  useEffect(() => {
    // Load initial tasks
    fetchTasks();
    
    // Setup WebSocket event listeners
    const unsubscribeCreated = websocketService.on('task_created', (message: WebSocketMessage) => {
      handleTaskCreated(message.data as TaskCreatedEvent);
    });
    
    const unsubscribeUpdated = websocketService.on('task_updated', (message: WebSocketMessage) => {
      handleTaskUpdated(message.data as TaskUpdateEvent);
    });
    
    const unsubscribeMoved = websocketService.on('task_moved', (message: WebSocketMessage) => {
      handleTaskMoved(message.data as TaskMoveEvent);
    });
    
    const unsubscribeAssigned = websocketService.on('task_assigned', (message: WebSocketMessage) => {
      handleTaskAssigned(message.data as TaskAssignedEvent);
    });
    
    const unsubscribeCompleted = websocketService.on('task_completed', (message: WebSocketMessage) => {
      handleTaskCompleted(message.data as TaskCompletedEvent);
    });

    // Cleanup on unmount
    return () => {
      mountedRef.current = false;
      unsubscribeCreated();
      unsubscribeUpdated();
      unsubscribeMoved();
      unsubscribeAssigned();
      unsubscribeCompleted();
      
      // Clear any pending timeouts
      optimisticUpdates.current.forEach(({ timeout }) => clearTimeout(timeout));
      optimisticUpdates.current.clear();
    };
  }, [
    fetchTasks,
    handleTaskCreated,
    handleTaskUpdated,
    handleTaskMoved,
    handleTaskAssigned,
    handleTaskCompleted
  ]);

  return {
    tasks,
    archivedTasks,
    tasksByColumn,
    loading,
    error,
    taskAnimations,
    fetchTasks,
    createTask,
    updateTaskOwner,
    archiveTask,
    moveTask,
    // Animation helpers
    getTaskAnimation: (taskId: string) => taskAnimations.get(taskId),
    // Real-time helpers
    rollbackOptimisticUpdate,
    // Utility functions
    isTaskAnimating: (taskId: string) => {
      const animation = taskAnimations.get(taskId);
      return animation ? (animation.isMoving || animation.isUpdating || animation.isNew) : false;
    }
  };
};
import {
  Task,
  TaskCreate,
  TaskUpdate,
  ColumnName,
  WebSocketMessage,
  TaskUpdateEvent,
  TaskMoveEvent,
  TaskAssignedEvent,
  TaskCreatedEvent,
  TaskCompletedEvent,
  TaskAnimationState
} from '../types';

export const useTasks = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [taskAnimations, setTaskAnimations] = useState<Map<string, TaskAnimationState>>(new Map());
  
  // Track optimistic updates for rollback functionality
  const optimisticUpdates = useRef<Map<string, { original: Task; timeout: NodeJS.Timeout }>>(new Map());
  
  // Track if component is mounted to prevent state updates after unmount
  const mountedRef = useRef(true);

  // Animation helper functions
  const setTaskAnimation = useCallback((taskId: string, animation: Partial<TaskAnimationState>) => {
    setTaskAnimations(prev => {
      const newMap = new Map(prev);
      const current = newMap.get(taskId) || { isMoving: false, isUpdating: false, isNew: false };
      newMap.set(taskId, { ...current, ...animation, lastUpdate: new Date() });
      return newMap;
    });
  }, []);

  const clearTaskAnimation = useCallback((taskId: string, delay = 2000) => {
    setTimeout(() => {
      if (mountedRef.current) {
        setTaskAnimations(prev => {
          const newMap = new Map(prev);
          newMap.delete(taskId);
          return newMap;
        });
      }
    }, delay);
  }, []);

  // Optimistic update helpers
  const addOptimisticUpdate = useCallback((taskId: string, originalTask: Task) => {
    const timeout = setTimeout(() => {
      optimisticUpdates.current.delete(taskId);
    }, 10000); // Clear after 10 seconds
    
    optimisticUpdates.current.set(taskId, { original: originalTask, timeout });
  }, []);

  const rollbackOptimisticUpdate = useCallback((taskId: string) => {
    const update = optimisticUpdates.current.get(taskId);
    if (update && mountedRef.current) {
      clearTimeout(update.timeout);
      optimisticUpdates.current.delete(taskId);
      
      // Restore original task
      setTasks(prevTasks => 
        prevTasks.map(task => task.id === taskId ? update.original : task)
      );
      
      setTaskAnimation(taskId, { isUpdating: false, isMoving: false });
    }
  }, [setTaskAnimation]);

  // WebSocket event handlers
  const handleTaskCreated = useCallback((event: TaskCreatedEvent) => {
    if (!mountedRef.current) return;
    
    const newTask = event.task;
    
    setTasks(prevTasks => {
      // Check if task already exists (avoid duplicates)
      const exists = prevTasks.some(task => task.id === newTask.id);
      if (exists) return prevTasks;
      
      return [...prevTasks, newTask];
    });
    
    setTaskAnimation(newTask.id, { isNew: true });
    clearTaskAnimation(newTask.id);
    
    // Show notification
    notificationService.notifyTaskCreated(newTask);
  }, [setTaskAnimation, clearTaskAnimation]);

  const handleTaskUpdated = useCallback((event: TaskUpdateEvent) => {
    if (!mountedRef.current) return;
    
    const { taskId, task } = event;
    
    setTasks(prevTasks => 
      prevTasks.map(prevTask => 
        prevTask.id === taskId ? { ...prevTask, ...task } : prevTask
      )
    );
    
    setTaskAnimation(taskId, { isUpdating: true });
    clearTaskAnimation(taskId);
  }, [setTaskAnimation, clearTaskAnimation]);

  const handleTaskMoved = useCallback((event: TaskMoveEvent) => {
    if (!mountedRef.current) return;
    
    const { taskId, task, fromColumn, toColumn } = event;
    
    setTasks(prevTasks => 
      prevTasks.map(prevTask => 
        prevTask.id === taskId ? { ...prevTask, column_name: toColumn } : prevTask
      )
    );
    
    setTaskAnimation(taskId, { isMoving: true });
    clearTaskAnimation(taskId);
    
    // Show notification for completed tasks
    if (toColumn === 'Done') {
      notificationService.notifyTaskCompleted(task);
    } else {
      notificationService.notifyTaskMoved(task, fromColumn, toColumn);
    }
  }, [setTaskAnimation, clearTaskAnimation]);

  const handleTaskAssigned = useCallback((event: TaskAssignedEvent) => {
    if (!mountedRef.current) return;
    
    const { taskId, task, assignedTo } = event;
    
    setTasks(prevTasks => 
      prevTasks.map(prevTask => 
        prevTask.id === taskId ? { ...prevTask, owner: assignedTo } : prevTask
      )
    );
    
    setTaskAnimation(taskId, { isUpdating: true });
    clearTaskAnimation(taskId);
    
    // Show notification
    notificationService.notifyTaskAssigned(task, assignedTo);
  }, [setTaskAnimation, clearTaskAnimation]);

  const handleTaskCompleted = useCallback((event: TaskCompletedEvent) => {
    if (!mountedRef.current) return;
    
    const { taskId, task } = event;
    
    setTasks(prevTasks => 
      prevTasks.map(prevTask => 
        prevTask.id === taskId ? { ...prevTask, column_name: 'Done' } : prevTask
      )
    );
    
    setTaskAnimation(taskId, { isMoving: true });
    clearTaskAnimation(taskId);
    
    // Show notification
    notificationService.notifyTaskCompleted(task);
  }, [setTaskAnimation, clearTaskAnimation]);

  // Fetch all tasks
  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const tasksData = await apiService.listTasks();
      setTasks(tasksData);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to fetch tasks';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  // Create a new task
  const createTask = useCallback(async (taskData: TaskCreate) => {
    try {
      const response = await apiService.createTask(taskData);
      if (response.success) {
        toast.success(response.message);
        await fetchTasks(); // Refresh the task list
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to create task';
      toast.error(errorMessage);
      throw err;
    }
  }, [fetchTasks]);

  // Update task owner
  const updateTaskOwner = useCallback(async (taskId: string, owner: string) => {
    try {
      const update: TaskUpdate = { owner };
      const response = await apiService.updateTask(taskId, update);
      if (response.success) {
        toast.success(response.message);
        await fetchTasks(); // Refresh the task list
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to update task';
      toast.error(errorMessage);
      throw err;
    }
  }, [fetchTasks]);

  // Move task to different column with optimistic updates
  const moveTask = useCallback(async (taskId: string, column: ColumnName) => {
    const originalTask = tasks.find(task => task.id === taskId);
    if (!originalTask) return;

    try {
      // Store original task for potential rollback
      addOptimisticUpdate(taskId, originalTask);
      
      // Optimistically update the UI immediately
      setTasks(prevTasks => 
        prevTasks.map(task => 
          task.id === taskId ? { ...task, column_name: column } : task
        )
      );
      
      setTaskAnimation(taskId, { isMoving: true });
      
      // Make API call
      const response = await apiService.moveTask(taskId, { column });
      if (response.success) {
        // Success - clear optimistic update
        const update = optimisticUpdates.current.get(taskId);
        if (update) {
          clearTimeout(update.timeout);
          optimisticUpdates.current.delete(taskId);
        }
        
        clearTaskAnimation(taskId);
        toast.success(response.message);
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to move task';
      toast.error(errorMessage);
      
      // Rollback optimistic update
      rollbackOptimisticUpdate(taskId);
      throw err;
    }
  }, [tasks, addOptimisticUpdate, rollbackOptimisticUpdate, setTaskAnimation, clearTaskAnimation]);

  // Group tasks by column
  const tasksByColumn = {
    'To Do': tasks.filter(task => task.column_name === 'To Do'),
    'In Progress': tasks.filter(task => task.column_name === 'In Progress'),
    'Done': tasks.filter(task => task.column_name === 'Done'),
  };

  // Setup WebSocket listeners and load tasks on mount
  useEffect(() => {
    // Load initial tasks
    fetchTasks();
    
    // Setup WebSocket event listeners
    const unsubscribeCreated = websocketService.on('task_created', (message: WebSocketMessage) => {
      handleTaskCreated(message.data as TaskCreatedEvent);
    });
    
    const unsubscribeUpdated = websocketService.on('task_updated', (message: WebSocketMessage) => {
      handleTaskUpdated(message.data as TaskUpdateEvent);
    });
    
    const unsubscribeMoved = websocketService.on('task_moved', (message: WebSocketMessage) => {
      handleTaskMoved(message.data as TaskMoveEvent);
    });
    
    const unsubscribeAssigned = websocketService.on('task_assigned', (message: WebSocketMessage) => {
      handleTaskAssigned(message.data as TaskAssignedEvent);
    });
    
    const unsubscribeCompleted = websocketService.on('task_completed', (message: WebSocketMessage) => {
      handleTaskCompleted(message.data as TaskCompletedEvent);
    });

    // Cleanup on unmount
    return () => {
      mountedRef.current = false;
      unsubscribeCreated();
      unsubscribeUpdated();
      unsubscribeMoved();
      unsubscribeAssigned();
      unsubscribeCompleted();
      
      // Clear any pending timeouts
      optimisticUpdates.current.forEach(({ timeout }) => clearTimeout(timeout));
      optimisticUpdates.current.clear();
    };
  }, [
    fetchTasks,
    handleTaskCreated,
    handleTaskUpdated,
    handleTaskMoved,
    handleTaskAssigned,
    handleTaskCompleted
  ]);

  return {
    tasks,
    tasksByColumn,
    loading,
    error,
    taskAnimations,
    fetchTasks,
    createTask,
    updateTaskOwner,
    moveTask,
    // Animation helpers
    getTaskAnimation: (taskId: string) => taskAnimations.get(taskId),
    // Real-time helpers
    rollbackOptimisticUpdate,
    // Utility functions
    isTaskAnimating: (taskId: string) => {
      const animation = taskAnimations.get(taskId);
      return animation ? (animation.isMoving || animation.isUpdating || animation.isNew) : false;
    }
  };
};