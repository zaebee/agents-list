// src/components/ArchivedTasks.tsx

import React from 'react';
import { useTaskContext } from '../contexts/TaskContext';
import { Task } from '../types';
import { ArchiveRestore } from 'lucide-react';

const ArchivedTasks: React.FC = () => {
  const { archivedTasks, archiveTask, loading } = useTaskContext();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading archived tasks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Archived Tasks</h2>
      {archivedTasks.length === 0 ? (
        <p className="text-gray-500">No archived tasks.</p>
      ) : (
        <ul className="divide-y divide-gray-200">
          {archivedTasks.map((task: Task) => (
            <li key={task.id} className="py-4 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium">{task.title}</h3>
                <p className="text-gray-500">{task.description}</p>
              </div>
              <button
                onClick={() => archiveTask(task.id, false)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <ArchiveRestore size={16} />
                <span>Unarchive</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ArchivedTasks;
