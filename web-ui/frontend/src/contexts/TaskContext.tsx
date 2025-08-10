// src/contexts/TaskContext.tsx
import React, { createContext, useContext, ReactNode } from 'react';
import { useTasks } from '../hooks/useTasks';

type TaskContextType = ReturnType<typeof useTasks>;

const TaskContext = createContext<TaskContextType | undefined>(undefined);

export const TaskProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const tasks = useTasks();
  return <TaskContext.Provider value={tasks}>{children}</TaskContext.Provider>;
};

export const useTaskContext = () => {
  const context = useContext(TaskContext);
  if (context === undefined) {
    throw new Error('useTaskContext must be used within a TaskProvider');
  }
  return context;
};
