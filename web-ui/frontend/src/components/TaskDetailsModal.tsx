// Modal component for viewing and managing task details

import React, { useState, useEffect } from 'react';
import { X, User, MessageSquare, Send, Clock, Target } from 'lucide-react';
import { apiService } from '../services/api';
import { TaskDetails, TaskComment } from '../types';

interface TaskDetailsModalProps {
  taskId: string | null;
  isOpen: boolean;
  onClose: () => void;
}

const TaskDetailsModal: React.FC<TaskDetailsModalProps> = ({
  taskId,
  isOpen,
  onClose
}) => {
  const [task, setTask] = useState<TaskDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [addingComment, setAddingComment] = useState(false);

  // Load task details when modal opens
  useEffect(() => {
    const loadTaskDetails = async () => {
      if (!taskId || !isOpen) {
        setTask(null);
        return;
      }

      try {
        setLoading(true);
        const taskDetails = await apiService.getTaskDetails(taskId);
        setTask(taskDetails);
      } catch (error) {
        console.error('Failed to load task details:', error);
      } finally {
        setLoading(false);
      }
    };

    loadTaskDetails();
  }, [taskId, isOpen]);

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !taskId) return;

    try {
      setAddingComment(true);
      const commentData: TaskComment = { message: newComment };
      await apiService.addComment(taskId, commentData);
      
      // Refresh task details to show new comment
      const updatedTask = await apiService.getTaskDetails(taskId);
      setTask(updatedTask);
      setNewComment('');
    } catch (error) {
      console.error('Failed to add comment:', error);
    } finally {
      setAddingComment(false);
    }
  };

  const formatAgentName = (agent?: string) => {
    if (!agent) return 'Unassigned';
    return agent.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getOwnerColor = (owner?: string) => {
    if (!owner) return 'bg-gray-100 text-gray-500';
    
    const colorMap: { [key: string]: string } = {
      'frontend-developer': 'bg-blue-100 text-blue-700',
      'backend-architect': 'bg-green-100 text-green-700',
      'ai-engineer': 'bg-purple-100 text-purple-700',
      'business-analyst': 'bg-orange-100 text-orange-700',
      'deployment-engineer': 'bg-red-100 text-red-700',
      'api-documenter': 'bg-cyan-100 text-cyan-700',
    };
    
    return colorMap[owner] || 'bg-indigo-100 text-indigo-700';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'To Do':
        return 'bg-red-100 text-red-700';
      case 'In Progress':
        return 'bg-yellow-100 text-yellow-700';
      case 'Done':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Task Details</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading task details...</p>
          </div>
        ) : task ? (
          <div className="p-6 space-y-6">
            {/* Task Header Info */}
            <div className="space-y-4">
              {/* Title and Status */}
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div className="flex-1">
                  <h1 className="text-2xl font-bold text-gray-900 mb-2">
                    {task.title}
                  </h1>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span className="font-mono">ID: #{task.id.slice(-8)}</span>
                    <span className={`px-2 py-1 rounded-full font-medium ${getStatusColor(task.column_name)}`}>
                      {task.column_name}
                    </span>
                  </div>
                </div>
              </div>

              {/* Owner */}
              <div className="flex items-center space-x-3">
                <User size={20} className="text-gray-400" />
                <div className={`px-3 py-1 rounded-full text-sm font-medium flex items-center space-x-2 ${getOwnerColor(task.owner)}`}>
                  <span>Assigned to: {formatAgentName(task.owner)}</span>
                </div>
              </div>

              {/* Description */}
              {task.description && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-2 flex items-center space-x-2">
                    <Target size={16} />
                    <span>Description</span>
                  </h3>
                  <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {task.description}
                  </p>
                </div>
              )}
            </div>

            {/* Comments Section */}
            <div className="border-t pt-6">
              <div className="flex items-center space-x-2 mb-4">
                <MessageSquare size={20} className="text-gray-400" />
                <h3 className="font-medium text-gray-900">
                  Comments ({task.comments.length})
                </h3>
              </div>

              {/* Existing Comments */}
              <div className="space-y-3 mb-6 max-h-60 overflow-y-auto">
                {task.comments.length === 0 ? (
                  <p className="text-gray-500 text-sm italic">No comments yet. Be the first to add one!</p>
                ) : (
                  task.comments.map((comment, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-3">
                      <p className="text-gray-700 text-sm leading-relaxed">
                        {comment.text}
                      </p>
                    </div>
                  ))
                )}
              </div>

              {/* Add Comment Form */}
              <form onSubmit={handleAddComment} className="space-y-3">
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Add a comment..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={!newComment.trim() || addingComment}
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                  >
                    <Send size={16} />
                    <span>{addingComment ? 'Adding...' : 'Add Comment'}</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center">
            <p className="text-gray-500">Failed to load task details</p>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default TaskDetailsModal;