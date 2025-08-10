// Individual task card component with drag and drop functionality

import React from 'react';
import { useDrag } from 'react-dnd';
import { User, Clock, Sparkles, ArrowRight } from 'lucide-react';
import { Task, TaskAnimationState } from '../types';

interface TaskCardProps {
  task: Task;
  onTaskClick: (taskId: string) => void;
  onOwnerChange?: (taskId: string, owner: string) => void;
  animationState?: TaskAnimationState;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, onTaskClick, onOwnerChange, animationState }) => {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'task',
    item: { id: task.id, currentColumn: task.column_name },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  }));

  const getOwnerColor = (owner?: string) => {
    if (!owner) return 'bg-gray-100 text-gray-500';
    
    // Color mapping for different agent types
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

  const formatAgentName = (agent?: string) => {
    if (!agent) return 'Unassigned';
    return agent.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Get animation classes based on state
  const getAnimationClasses = () => {
    if (!animationState) return '';
    
    const classes = [];
    
    if (animationState.isNew) {
      classes.push('animate-pulse border-green-300 bg-green-50');
    }
    
    if (animationState.isMoving) {
      classes.push('animate-bounce border-blue-300 bg-blue-50');
    }
    
    if (animationState.isUpdating) {
      classes.push('animate-pulse border-yellow-300 bg-yellow-50');
    }
    
    return classes.join(' ');
  };

  const isAnimating = animationState && (animationState.isNew || animationState.isMoving || animationState.isUpdating);

  return (
    <div
      ref={drag}
      className={`
        bg-white rounded-lg border border-gray-200 p-4 shadow-sm cursor-pointer
        transition-all duration-300 hover:shadow-md hover:border-gray-300
        ${isDragging ? 'opacity-50 rotate-2 scale-105' : ''}
        ${getAnimationClasses()}
        ${isAnimating ? 'relative overflow-hidden' : ''}
      `}
      onClick={() => onTaskClick(task.id)}
    >
      {/* Task Title */}
      <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
        {task.title}
      </h3>
      
      {/* Task Description */}
      {task.description && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {task.description}
        </p>
      )}
      
      {/* Task Metadata */}
      <div className="flex items-center justify-between">
        {/* AI Owner Badge */}
        <div className="flex items-center space-x-2">
          {task.owner ? (
            <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${getOwnerColor(task.owner)}`}>
              <User size={12} />
              <span>{formatAgentName(task.owner)}</span>
            </div>
          ) : (
            <div className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500 flex items-center space-x-1">
              <User size={12} />
              <span>Unassigned</span>
            </div>
          )}
        </div>
        
        {/* Task ID (shortened) */}
        <div className="text-xs text-gray-400 font-mono">
          #{task.id.slice(-8)}
        </div>
      </div>
      
      {/* Animation Indicators */}
      {isAnimating && !isDragging && (
        <div className="absolute top-2 right-2 z-10">
          {animationState?.isNew && (
            <div className="flex items-center space-x-1 px-2 py-1 bg-green-500 text-white text-xs rounded-full">
              <Sparkles size={12} />
              <span>New</span>
            </div>
          )}
          {animationState?.isMoving && (
            <div className="flex items-center space-x-1 px-2 py-1 bg-blue-500 text-white text-xs rounded-full">
              <ArrowRight size={12} />
              <span>Moving</span>
            </div>
          )}
          {animationState?.isUpdating && (
            <div className="flex items-center space-x-1 px-2 py-1 bg-yellow-500 text-white text-xs rounded-full">
              <Clock size={12} />
              <span>Updating</span>
            </div>
          )}
        </div>
      )}

      {/* Drag indicator */}
      {isDragging && (
        <div className="absolute inset-0 bg-blue-50 border-2 border-blue-300 border-dashed rounded-lg flex items-center justify-center">
          <div className="text-blue-500 font-medium">Moving task...</div>
        </div>
      )}

      {/* Shimmer effect for animations */}
      {isAnimating && (
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse"></div>
      )}
    </div>
  );
};

export default TaskCard;