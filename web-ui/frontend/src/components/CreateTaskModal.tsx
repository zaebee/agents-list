// Modal component for creating new tasks with AI agent suggestions

import React, { useState, useEffect } from 'react';
import { X, Bot, Lightbulb, AlertTriangle } from 'lucide-react';
import { apiService } from '../services/api';
import { TaskCreate, AgentSuggestion, PMAnalysis } from '../types';

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (task: TaskCreate) => Promise<void>;
}

const CreateTaskModal: React.FC<CreateTaskModalProps> = ({
  isOpen,
  onClose,
  onSubmit
}) => {
  const [formData, setFormData] = useState<TaskCreate>({
    title: '',
    description: '',
    owner: '',
    no_ai_suggest: false
  });
  
  const [suggestions, setSuggestions] = useState<AgentSuggestion[]>([]);
  const [pmAnalysis, setPmAnalysis] = useState<PMAnalysis | null>(null);
  const [availableAgents, setAvailableAgents] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [showPmAnalysis, setShowPmAnalysis] = useState(false);

  // Load available agents on mount
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const agents = await apiService.listAgents();
        setAvailableAgents(agents);
      } catch (error) {
        console.error('Failed to load agents:', error);
      }
    };
    
    if (isOpen) {
      loadAgents();
    }
  }, [isOpen]);

  // Auto-suggest agents when title or description changes
  useEffect(() => {
    const getSuggestions = async () => {
      if (!formData.title.trim() || formData.no_ai_suggest) {
        setSuggestions([]);
        return;
      }

      try {
        const taskForSuggestion = {
          title: formData.title,
          description: formData.description || '',
        };
        
        const agentSuggestions = await apiService.suggestAgents(taskForSuggestion);
        setSuggestions(agentSuggestions.slice(0, 3)); // Show top 3 suggestions
      } catch (error) {
        console.error('Failed to get suggestions:', error);
      }
    };

    const debounceTimer = setTimeout(getSuggestions, 500);
    return () => clearTimeout(debounceTimer);
  }, [formData.title, formData.description, formData.no_ai_suggest]);

  const handlePMAnalysis = async () => {
    if (!formData.title.trim()) return;
    
    try {
      setAnalyzing(true);
      const analysis = await apiService.pmAnalyzeTask(formData);
      setPmAnalysis(analysis);
      setShowPmAnalysis(true);
      
      // Auto-assign suggested agent if direct assignment
      if (analysis.type === 'direct_assignment' && analysis.assigned_agent) {
        setFormData(prev => ({ ...prev, owner: analysis.assigned_agent! }));
      }
    } catch (error) {
      console.error('PM Analysis failed:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) return;

    try {
      setLoading(true);
      await onSubmit(formData);
      handleClose();
    } catch (error) {
      console.error('Failed to create task:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      title: '',
      description: '',
      owner: '',
      no_ai_suggest: false
    });
    setSuggestions([]);
    setPmAnalysis(null);
    setShowPmAnalysis(false);
    onClose();
  };

  const formatAgentName = (agent: string) => {
    return agent.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Create New Task</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Task Title *
            </label>
            <input
              type="text"
              id="title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter a clear, descriptive task title"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Provide additional details about the task requirements"
            />
          </div>

          {/* PM Analysis */}
          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Bot className="text-blue-500" size={20} />
                <span className="font-medium text-gray-900">AI-Powered Analysis</span>
              </div>
              <button
                type="button"
                onClick={handlePMAnalysis}
                disabled={!formData.title.trim() || analyzing}
                className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {analyzing ? 'Analyzing...' : 'PM Analysis'}
              </button>
            </div>

            {/* PM Analysis Results */}
            {showPmAnalysis && pmAnalysis && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div className="flex items-start space-x-2">
                  <Lightbulb className="text-blue-500 mt-0.5" size={16} />
                  <div className="flex-1">
                    <h4 className="font-medium text-blue-900 mb-2">PM Recommendation</h4>
                    <p className="text-sm text-blue-800 mb-3">{pmAnalysis.recommendation}</p>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="font-medium">Priority:</span> {pmAnalysis.priority}
                      </div>
                      <div>
                        <span className="font-medium">Complexity:</span> {pmAnalysis.analysis.complexity}
                      </div>
                      <div>
                        <span className="font-medium">Estimated:</span> {pmAnalysis.analysis.estimated_hours} hours
                      </div>
                      {pmAnalysis.assigned_agent && (
                        <div>
                          <span className="font-medium">Assigned:</span> {formatAgentName(pmAnalysis.assigned_agent)}
                        </div>
                      )}
                    </div>
                    
                    {pmAnalysis.analysis.risk_factors.length > 0 && (
                      <div className="mt-3">
                        <div className="flex items-center space-x-1 text-orange-700">
                          <AlertTriangle size={14} />
                          <span className="text-xs font-medium">Risk Factors:</span>
                        </div>
                        <ul className="text-xs text-orange-600 mt-1 ml-4 space-y-1">
                          {pmAnalysis.analysis.risk_factors.map((risk, idx) => (
                            <li key={idx}>• {risk}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Agent Suggestions */}
          {suggestions.length > 0 && !formData.no_ai_suggest && (
            <div>
              <div className="flex items-center space-x-2 mb-3">
                <Bot className="text-green-500" size={20} />
                <span className="font-medium text-gray-900">AI Agent Suggestions</span>
              </div>
              <div className="grid gap-2">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => setFormData({ ...formData, owner: suggestion.agent })}
                    className={`p-3 text-left border rounded-md hover:border-blue-400 transition-colors ${
                      formData.owner === suggestion.agent
                        ? 'border-blue-400 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium text-gray-900">
                          {formatAgentName(suggestion.agent)}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                          Keywords: {suggestion.matched_keywords.join(', ')}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-green-600">
                          {suggestion.confidence.toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Manual Agent Selection */}
          <div>
            <label htmlFor="owner" className="block text-sm font-medium text-gray-700 mb-2">
              Assign to Agent
            </label>
            <select
              id="owner"
              value={formData.owner}
              onChange={(e) => setFormData({ ...formData, owner: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select an agent (optional)</option>
              {availableAgents.map((agent) => (
                <option key={agent} value={agent}>
                  {formatAgentName(agent)}
                </option>
              ))}
            </select>
          </div>

          {/* Options */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="no_ai_suggest"
              checked={formData.no_ai_suggest}
              onChange={(e) => setFormData({ ...formData, no_ai_suggest: e.target.checked })}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="no_ai_suggest" className="ml-2 block text-sm text-gray-700">
              Skip AI agent suggestions
            </label>
          </div>

          {/* Submit Buttons */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!formData.title.trim() || loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateTaskModal;