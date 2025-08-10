import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const fetchAnalytics = async () => {
  try {
    const [taskCompletion, agentPerformance, executiveDashboard] = await Promise.all([
      axios.get(`${API_BASE_URL}/analytics/task-completion`),
      axios.get(`${API_BASE_URL}/analytics/agent-performance`),
      axios.get(`${API_BASE_URL}/analytics/executive-dashboard`)
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
    const response = await axios.get(`${API_BASE_URL}/analytics/export`, {
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