// Main dashboard component with task board layout

import React, { useState, useEffect } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { Plus, Bot, RefreshCw, Activity, BarChart3, Kanban, Bell, Archive } from 'lucide-react';
import TaskColumn from './TaskColumn';
import CreateTaskModal from './CreateTaskModal';
import TaskDetailsModal from './TaskDetailsModal';
import AnalyticsDashboard from './AnalyticsDashboard';
import ConnectionStatus, { useConnectionStatus } from './ConnectionStatus';
import NotificationSettings from './NotificationSettings';
import { useTaskContext } from '../contexts/TaskContext';
import notificationService from '../services/notifications';
import { ColumnName } from '../types';
import ArchivedTasks from './ArchivedTasks';

const Dashboard: React.FC = () => {
  const {
    tasksByColumn,
    loading,
    error,
    fetchTasks,
    createTask,
    moveTask,
    taskAnimations,
    isTaskAnimating
  } = useTaskContext();

  const { connectionState, isConnected } = useConnectionStatus();

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [isTaskDetailsOpen, setIsTaskDetailsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'board' | 'analytics' | 'archived'>('board');
  const [showNotificationPrompt, setShowNotificationPrompt] = useState(false);
  const [showNotificationSettings, setShowNotificationSettings] = useState(false);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>('default');

  // Check notification permission and show prompt if needed
  useEffect(() => {
    const checkNotificationPermission = async () => {
      if (notificationService.isSupported()) {
        const permission = Notification.permission;
        setNotificationPermission(permission);
        
        // Show prompt after a short delay if permission is default
        if (permission === 'default') {
          setTimeout(() => setShowNotificationPrompt(true), 3000);
        }
      }
    };
    
    checkNotificationPermission();
  }, []);

  const handleRequestNotificationPermission = async () => {
    const permission = await notificationService.requestPermission();
    setNotificationPermission(permission);
    setShowNotificationPrompt(false);
    
    if (permission === 'granted') {
      await notificationService.testNotification();
    }
  };

  const handleTaskMove = async (taskId: string, targetColumn: ColumnName) => {
    try {
      await moveTask(taskId, targetColumn);
    } catch (error) {
      console.error('Failed to move task:', error);
    }
  };

  const handleTaskClick = (taskId: string) => {
    setSelectedTaskId(taskId);
    setIsTaskDetailsOpen(true);
  };

  const handleCloseTaskDetails = () => {
    setIsTaskDetailsOpen(false);
    setSelectedTaskId(null);
  };

  const totalTasks = Object.values(tasksByColumn).reduce((sum, tasks) => sum + tasks.length, 0);
  const completedTasks = tasksByColumn['Done'].length;
  const inProgressTasks = tasksByColumn['In Progress'].length;

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Something went wrong</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchTasks}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2 mx-auto"
          >
            <RefreshCw size={16} />
            <span>Try Again</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              {/* Logo and Title */}
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <Bot className="text-blue-600" size={28} />
                  <h1 className="text-xl font-bold text-gray-900">AI-CRM Dashboard</h1>
                </div>
                {/* Connection Status */}
                <ConnectionStatus className="ml-4" />
              </div>

              {/* Stats */}
              <div className="hidden sm:flex items-center space-x-6 text-sm">
                <div className="flex items-center space-x-2">
                  <Activity className="text-gray-400" size={16} />
                  <span className="text-gray-600">Total: {totalTasks}</span>
                </div>
                <div className="text-yellow-600">
                  In Progress: {inProgressTasks}
                </div>
                <div className="text-green-600">
                  Completed: {completedTasks}
                </div>
              </div>

              {/* Navigation Tabs */}
              <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setActiveTab('board')}
                  className={`px-4 py-2 rounded-md flex items-center space-x-2 transition-colors ${
                    activeTab === 'board'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Kanban size={16} />
                  <span>Task Board</span>
                </button>
                <button
                  onClick={() => setActiveTab('archived')}
                  className={`px-4 py-2 rounded-md flex items-center space-x-2 transition-colors ${
                    activeTab === 'archived'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Archive size={16} />
                  <span>Archived</span>
                </button>
                <button
                  onClick={() => setActiveTab('analytics')}
                  className={`px-4 py-2 rounded-md flex items-center space-x-2 transition-colors ${
                    activeTab === 'analytics'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <BarChart3 size={16} />
                  <span>Analytics</span>
                </button>
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowNotificationSettings(true)}
                  className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
                  title="Notification settings"
                >
                  <Bell size={18} />
                </button>
                <button
                  onClick={fetchTasks}
                  disabled={loading}
                  className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
                  title="Refresh tasks"
                >
                  <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                </button>
                {activeTab === 'board' && (
                  <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2"
                  >
                    <Plus size={16} />
                    <span>New Task</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeTab === 'analytics' ? (
            <AnalyticsDashboard />
          ) : activeTab === 'archived' ? (
            <ArchivedTasks />
          ) : loading && tasksByColumn['To Do'].length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-500">Loading tasks...</p>
              </div>
            </div>
          ) : (
            <>
              {/* Mobile Stats */}
              <div className="sm:hidden mb-6">
                <div className="bg-white rounded-lg shadow p-4">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-600">Total: {totalTasks}</span>
                    <span className="text-yellow-600">Progress: {inProgressTasks}</span>
                    <span className="text-green-600">Done: {completedTasks}</span>
                  </div>
                </div>
              </div>

              {/* Task Board */}
              <div className="flex flex-col lg:flex-row gap-6 overflow-x-auto">
                <TaskColumn
                  title="To Do"
                  columnName="To Do"
                  tasks={tasksByColumn['To Do']}
                  onTaskMove={handleTaskMove}
                  onTaskClick={handleTaskClick}
                  onAddTask={() => setIsCreateModalOpen(true)}
                  getTaskAnimation={(taskId) => taskAnimations.get(taskId)}
                  isRealTimeActive={isConnected}
                />
                <TaskColumn
                  title="In Progress"
                  columnName="In Progress"
                  tasks={tasksByColumn['In Progress']}
                  onTaskMove={handleTaskMove}
                  onTaskClick={handleTaskClick}
                  getTaskAnimation={(taskId) => taskAnimations.get(taskId)}
                  isRealTimeActive={isConnected}
                />
                <TaskColumn
                  title="Done"
                  columnName="Done"
                  tasks={tasksByColumn['Done']}
                  onTaskMove={handleTaskMove}
                  onTaskClick={handleTaskClick}
                  getTaskAnimation={(taskId) => taskAnimations.get(taskId)}
                  isRealTimeActive={isConnected}
                />
              </div>

              {/* Empty State */}
              {totalTasks === 0 && !loading && (
                <div className="text-center py-12">
                  <Bot className="mx-auto text-gray-300 mb-4" size={64} />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No tasks yet</h3>
                  <p className="text-gray-500 mb-6">
                    Create your first task to get started with AI-powered task management
                  </p>
                  <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 mx-auto"
                  >
                    <Plus size={20} />
                    <span>Create First Task</span>
                  </button>
                </div>
              )}
            </>
          )}
        </main>

        {/* Modals */}
        <CreateTaskModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onSubmit={createTask}
        />

        <TaskDetailsModal
          taskId={selectedTaskId}
          isOpen={isTaskDetailsOpen}
          onClose={handleCloseTaskDetails}
        />

        <NotificationSettings
          isOpen={showNotificationSettings}
          onClose={() => setShowNotificationSettings(false)}
        />

        {/* Notification Permission Prompt */}
        {showNotificationPrompt && (
          <div className="fixed bottom-4 right-4 max-w-md bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-50">
            <div className="flex items-start space-x-3">
              <Bell className="text-blue-500 flex-shrink-0 mt-1" size={20} />
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 mb-1">
                  Enable Notifications
                </h4>
                <p className="text-sm text-gray-600 mb-3">
                  Stay updated with real-time task notifications. Get notified when tasks are assigned, completed, or updated.
                </p>
                <div className="flex space-x-2">
                  <button
                    onClick={handleRequestNotificationPermission}
                    className="px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Enable
                  </button>
                  <button
                    onClick={() => setShowNotificationPrompt(false)}
                    className="px-3 py-2 text-gray-600 text-sm font-medium rounded-md hover:bg-gray-100 transition-colors"
                  >
                    Not Now
                  </button>
                </div>
              </div>
              <button
                onClick={() => setShowNotificationPrompt(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                ×
              </button>
            </div>
          </div>
        )}
      </div>
    </DndProvider>
  );
};

export default Dashboard;