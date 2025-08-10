import React, { useState, useEffect } from 'react';
import { Download, BarChart3, TrendingUp, Users, Activity } from 'lucide-react';
import { fetchAnalytics, exportAnalytics } from '../services/analyticsService';
import { AnalyticsData } from '../types';

const AnalyticsDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const handleExport = async (format: 'csv' | 'json') => {
    setExporting(true);
    try {
      await exportAnalytics(format);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        const data = await fetchAnalytics();
        setAnalytics(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to load analytics:', error);
        setLoading(false);
      }
    };

    loadAnalytics();
    const intervalId = setInterval(loadAnalytics, 5 * 60 * 1000); // Refresh every 5 minutes

    return () => clearInterval(intervalId);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading analytics...</span>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center p-8">
        <h3 className="text-lg font-semibold text-gray-600">Unable to load analytics</h3>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Export Actions */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <BarChart3 className="mr-3" size={28} />
          Analytics Dashboard
        </h2>
        <div className="flex space-x-2">
          <button
            onClick={() => handleExport('csv')}
            disabled={exporting}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
          >
            <Download size={16} />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => handleExport('json')}
            disabled={exporting}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
          >
            <Download size={16} />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Tasks</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.taskCompletion.totalTasks}</p>
            </div>
            <Activity className="text-blue-500" size={24} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Completion Rate</p>
              <p className="text-2xl font-bold text-green-600">{analytics.taskCompletion.completionRate.toFixed(1)}%</p>
            </div>
            <TrendingUp className="text-green-500" size={24} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Agents</p>
              <p className="text-2xl font-bold text-purple-600">{analytics.executiveDashboard.systemOverview.totalAgents}</p>
            </div>
            <Users className="text-purple-500" size={24} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">System Health</p>
              <p className="text-2xl font-bold text-blue-600">{analytics.executiveDashboard.systemOverview.systemHealth}%</p>
            </div>
            <BarChart3 className="text-blue-500" size={24} />
          </div>
        </div>
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Overview */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">System Overview</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Agents</span>
              <span className="font-medium">{analytics.executiveDashboard.systemOverview.totalAgents}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Active Integrations</span>
              <span className="font-medium">{analytics.executiveDashboard.systemOverview.activeIntegrations}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Workflow Efficiency</span>
              <span className="font-medium">{analytics.executiveDashboard.performanceKPIs.workflowEfficiency.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Top Performing Agents */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Top Performing Agents</h3>
          <div className="space-y-3">
            {analytics.executiveDashboard.performanceKPIs.topPerformingAgents.length > 0 ? (
              analytics.executiveDashboard.performanceKPIs.topPerformingAgents.map((agent, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span className="text-gray-600 truncate mr-2">{agent.agent}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all" 
                        style={{ width: `${Math.min(agent.successRate, 100)}%` }}
                      ></div>
                    </div>
                    <span className="font-medium text-sm w-12 text-right">{agent.successRate.toFixed(1)}%</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm">No agent performance data available yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Task Completion Details */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Task Completion Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{analytics.taskCompletion.totalTasks}</div>
            <div className="text-sm text-gray-600">Total Tasks</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{analytics.taskCompletion.completedTasks}</div>
            <div className="text-sm text-gray-600">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{analytics.taskCompletion.totalTasks - analytics.taskCompletion.completedTasks}</div>
            <div className="text-sm text-gray-600">In Progress</div>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Completion Progress</span>
            <span>{analytics.taskCompletion.completionRate.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all" 
              style={{ width: `${Math.min(analytics.taskCompletion.completionRate, 100)}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;