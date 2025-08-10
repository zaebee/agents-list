import api from './authAPI';
import { AnalyticsData } from '../types';

export const fetchAnalytics = async (): Promise<AnalyticsData> => {
  try {
    const [taskCompletion, agentPerformance, executiveDashboard] = await Promise.all([
      api.get('/analytics/task-completion'),
      api.get('/analytics/agent-performance'),
      api.get('/analytics/executive-dashboard')
    ]);

    return {
      taskCompletion: taskCompletion.data,
      agentPerformance: agentPerformance.data,
      executiveDashboard: executiveDashboard.data
    };
  } catch (error) {
    console.error('Error fetching analytics:', error);
    throw error;
  }
};

export const exportAnalytics = async (format: 'csv' | 'json' = 'csv') => {
  try {
    const response = await api.get('/analytics/export', {
      params: { format },
      responseType: 'blob'
    });

    const blob = new Blob([response.data], { 
      type: format === 'csv' ? 'text/csv' : 'application/json' 
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analytics_export.${format}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error('Error exporting analytics:', error);
    throw error;
  }
};
