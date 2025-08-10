// Custom React hook for task management

import { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-toastify';
import { apiService } from '../services/api';
import { Task, TaskCreate, TaskUpdate, ColumnName } from '../types';

export const useTasks = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  // Move task to different column
  const moveTask = useCallback(async (taskId: string, column: ColumnName) => {
    try {
      const response = await apiService.moveTask(taskId, { column });
      if (response.success) {
        toast.success(response.message);
        
        // Optimistically update the UI
        setTasks(prevTasks => 
          prevTasks.map(task => 
            task.id === taskId ? { ...task, column_name: column } : task
          )
        );
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to move task';
      toast.error(errorMessage);
      // Revert optimistic update by refetching
      await fetchTasks();
      throw err;
    }
  }, [fetchTasks]);

  // Group tasks by column
  const tasksByColumn = {
    'To Do': tasks.filter(task => task.column_name === 'To Do'),
    'In Progress': tasks.filter(task => task.column_name === 'In Progress'),
    'Done': tasks.filter(task => task.column_name === 'Done'),
  };

  // Load tasks on mount
  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  return {
    tasks,
    tasksByColumn,
    loading,
    error,
    fetchTasks,
    createTask,
    updateTaskOwner,
    moveTask,
  };
};