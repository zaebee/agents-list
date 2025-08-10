// Task column component with drag and drop functionality

import React from 'react';
import { useDrop } from 'react-dnd';
import { Plus } from 'lucide-react';
import TaskCard from './TaskCard';
import { Task, ColumnName } from '../types';

interface TaskColumnProps {
  title: string;
  columnName: ColumnName;
  tasks: Task[];
  onTaskMove: (taskId: string, targetColumn: ColumnName) => void;
  onTaskClick: (taskId: string) => void;
  onAddTask?: () => void;
}

const TaskColumn: React.FC<TaskColumnProps> = ({
  title,
  columnName,
  tasks,
  onTaskMove,
  onTaskClick,
  onAddTask
}) => {
  const [{ isOver, canDrop }, drop] = useDrop(() => ({
    accept: 'task',
    drop: (item: { id: string; currentColumn: ColumnName }) => {
      if (item.currentColumn !== columnName) {
        onTaskMove(item.id, columnName);
      }
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop(),
    }),
  }));

  const getColumnColor = (columnName: ColumnName) => {
    switch (columnName) {
      case 'To Do':
        return 'border-red-200 bg-red-50';
      case 'In Progress':
        return 'border-yellow-200 bg-yellow-50';
      case 'Done':
        return 'border-green-200 bg-green-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const getHeaderColor = (columnName: ColumnName) => {
    switch (columnName) {
      case 'To Do':
        return 'text-red-700 bg-red-100';
      case 'In Progress':
        return 'text-yellow-700 bg-yellow-100';
      case 'Done':
        return 'text-green-700 bg-green-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const dropZoneClasses = `
    min-h-[600px] rounded-lg border-2 transition-all duration-200
    ${getColumnColor(columnName)}
    ${isOver && canDrop ? 'border-blue-400 bg-blue-50' : ''}
    ${canDrop ? 'border-dashed' : 'border-solid'}
  `;

  return (
    <div className="flex flex-col w-full max-w-sm">
      {/* Column Header */}
      <div className={`flex items-center justify-between p-4 rounded-t-lg font-semibold ${getHeaderColor(columnName)}`}>
        <div className="flex items-center space-x-2">
          <h2 className="text-lg">{title}</h2>
          <span className="text-sm font-medium bg-white bg-opacity-50 px-2 py-1 rounded-full">
            {tasks.length}
          </span>
        </div>
        
        {/* Add Task Button (only for To Do column) */}
        {columnName === 'To Do' && onAddTask && (
          <button
            onClick={onAddTask}
            className="p-1 rounded-md hover:bg-white hover:bg-opacity-50 transition-colors"
            title="Add new task"
          >
            <Plus size={18} />
          </button>
        )}
      </div>
      
      {/* Drop Zone */}
      <div ref={drop} className={dropZoneClasses}>
        <div className="p-4 space-y-3">
          {tasks.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 text-sm">
                {isOver && canDrop ? 'Drop task here' : `No tasks in ${title}`}
              </div>
            </div>
          ) : (
            tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onTaskClick={onTaskClick}
              />
            ))
          )}
          
          {/* Drop indicator */}
          {isOver && canDrop && (
            <div className="border-2 border-dashed border-blue-400 rounded-lg p-4 bg-blue-50">
              <div className="text-center text-blue-600 font-medium">
                Drop task here
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TaskColumn;