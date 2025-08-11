import React, { useEffect, useState } from 'react';
import { CheckSquare, Clock, Play, Pause, Trash2, Plus } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { toast } from 'react-toastify';

interface Task {
  id: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  agent_id?: string;
  created_at: string;
  updated_at: string;
  result?: any;
}

export default function TaskManager() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [newTaskDescription, setNewTaskDescription] = useState('');
  const [showCreateTask, setShowCreateTask] = useState(false);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const tasksData = await apiService.getTasks();
      setTasks(tasksData);
    } catch (error: any) {
      console.error('Failed to load tasks:', error);
      toast.error('Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  const createTask = async () => {
    if (!newTaskDescription.trim()) return;

    try {
      const task = await apiService.createTask({
        description: newTaskDescription.trim(),
      });
      setTasks(prev => [task, ...prev]);
      setNewTaskDescription('');
      setShowCreateTask(false);
      toast.success('Task created successfully!');
    } catch (error: any) {
      console.error('Failed to create task:', error);
      toast.error('Failed to create task');
    }
  };

  const executeTask = async (taskId: string) => {
    try {
      await apiService.executeTaskById(taskId);
      toast.success('Task execution started!');
      loadTasks(); // Refresh tasks
    } catch (error: any) {
      console.error('Failed to execute task:', error);
      toast.error('Failed to execute task');
    }
  };

  const deleteTask = async (taskId: string) => {
    try {
      await apiService.deleteTask(taskId);
      setTasks(prev => prev.filter(task => task.id !== taskId));
      toast.success('Task deleted successfully!');
    } catch (error: any) {
      console.error('Failed to delete task:', error);
      toast.error('Failed to delete task');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckSquare size={16} />;
      case 'running':
        return <Clock size={16} />;
      default:
        return <Clock size={16} />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center text-white">
          <div className="loading-spinner w-12 h-12 mx-auto mb-4"></div>
          <p>Loading tasks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white/95 backdrop-blur-sm rounded-xl p-6 shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Task Manager</h1>
            <p className="text-gray-600">Manage and monitor your AI tasks</p>
          </div>
          <button
            onClick={() => setShowCreateTask(true)}
            className="btn-primary flex items-center space-x-2"
          >
            <Plus size={20} />
            <span>Create Task</span>
          </button>
        </div>
      </div>

      {/* Create Task Modal */}
      {showCreateTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Create New Task</h3>
            <textarea
              value={newTaskDescription}
              onChange={(e) => setNewTaskDescription(e.target.value)}
              placeholder="Describe your task..."
              className="input-field min-h-24 mb-4"
              rows={4}
            />
            <div className="flex space-x-3">
              <button
                onClick={createTask}
                className="btn-primary flex-1"
                disabled={!newTaskDescription.trim()}
              >
                Create Task
              </button>
              <button
                onClick={() => {
                  setShowCreateTask(false);
                  setNewTaskDescription('');
                }}
                className="btn-ghost flex-1"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tasks Grid */}
      <div className="grid grid-cols-1 gap-4">
        {tasks.length === 0 ? (
          <div className="card text-center py-12">
            <CheckSquare size={48} className="mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No tasks yet</h3>
            <p className="text-gray-500 mb-4">Create your first task to get started.</p>
            <button
              onClick={() => setShowCreateTask(true)}
              className="btn-primary"
            >
              Create Task
            </button>
          </div>
        ) : (
          tasks.map((task) => (
            <div key={task.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                      {getStatusIcon(task.status)}
                      <span className="capitalize">{task.status}</span>
                    </span>
                    <span className="text-xs text-gray-500">
                      Created {new Date(task.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-gray-900 mb-2">{task.description}</p>
                  {task.agent_id && (
                    <p className="text-xs text-gray-500">Agent: {task.agent_id}</p>
                  )}
                </div>
                <div className="flex items-center space-x-2 ml-4">
                  {task.status === 'pending' && (
                    <button
                      onClick={() => executeTask(task.id)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                      title="Execute task"
                    >
                      <Play size={16} />
                    </button>
                  )}
                  {task.status === 'running' && (
                    <button
                      className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg"
                      title="Pause task"
                    >
                      <Pause size={16} />
                    </button>
                  )}
                  <button
                    onClick={() => deleteTask(task.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                    title="Delete task"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              {task.result && (
                <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Result:</p>
                  <pre className="text-sm text-gray-800 whitespace-pre-wrap">
                    {typeof task.result === 'string' ? task.result : JSON.stringify(task.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}