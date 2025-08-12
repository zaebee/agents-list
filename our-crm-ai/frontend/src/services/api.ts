// API service for communicating with the AI Project Manager backend
import axios, { AxiosInstance } from 'axios';
import { toast } from 'react-toastify';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://zae.life:5001' 
  : '';

const TOKEN_KEY = 'ai_pm_token';

// Create axios instance with authentication
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor to add auth headers
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor for error handling
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        toast.error('Session expired. Please login again.');
        window.location.reload();
      }
      return Promise.reject(error);
    }
  );

  return client;
};

const api = createApiClient();

// API service with typed methods
export const apiService = {
  // Health check
  async healthCheck(): Promise<{ status: string; config_loaded: boolean }> {
    const response = await api.get('/api/health');
    return response.data;
  },

  // Agent operations
  async getAgents(): Promise<{ agents: any[]; total: number }> {
    const response = await api.get('/api/agents');
    return response.data;
  },

  async getSystemStatus(): Promise<any> {
    const response = await api.get('/api/agents/status');
    return response.data;
  },

  async analyzeTask(taskDescription: string): Promise<any> {
    const response = await api.post('/api/agents/analyze', {
      task_description: taskDescription,
    });
    return response.data;
  },

  async executeTask(task: { agent_id: string; task: string }): Promise<any> {
    const response = await api.post('/api/agents/execute', task);
    return response.data;
  },

  // Task operations
  async getTasks(): Promise<any[]> {
    const response = await api.get('/api/tasks');
    return response.data.tasks || [];
  },

  async createTask(task: { description: string; agent_id?: string }): Promise<any> {
    const response = await api.post('/api/tasks', task);
    return response.data;
  },

  async updateTask(taskId: string, updates: any): Promise<any> {
    const response = await api.put(`/api/tasks/${taskId}`, updates);
    return response.data;
  },

  async deleteTask(taskId: string): Promise<void> {
    await api.delete(`/api/tasks/${taskId}`);
  },

  async executeTaskById(taskId: string): Promise<any> {
    const response = await api.post(`/api/tasks/${taskId}/execute`);
    return response.data;
  },

  async pauseTask(taskId: string): Promise<any> {
    const response = await api.post(`/api/tasks/${taskId}/pause`);
    return response.data;
  },

  async stopTask(taskId: string): Promise<any> {
    const response = await api.post(`/api/tasks/${taskId}/stop`);
    return response.data;
  },

  // Dashboard data
  async getDashboardData(): Promise<any> {
    const response = await api.get('/api/executive-dashboard');
    return response.data;
  },

  // Analytics
  async getAnalytics(timeRange: string): Promise<any> {
    const response = await api.get(`/api/analytics?timeRange=${timeRange}`);
    return response.data;
  },

  // Billing operations
  async getBillingInfo(): Promise<any> {
    const response = await api.get('/api/billing/subscription');
    return response.data;
  },

  async getUsageInfo(): Promise<any> {
    const response = await api.get('/api/billing/usage');
    return response.data;
  },

  async getPricing(): Promise<any> {
    const response = await api.get('/api/billing/pricing');
    return response.data;
  },

  async createSubscription(subscriptionData: any): Promise<any> {
    const response = await api.post('/api/billing/subscription', subscriptionData);
    return response.data;
  },

  async cancelSubscription(): Promise<any> {
    const response = await api.post('/api/billing/cancel');
    return response.data;
  },

  async getInvoices(): Promise<any> {
    const response = await api.get('/api/billing/invoices');
    return response.data;
  },

  // File upload
  async uploadFile(file: File, onProgress?: (progress: number) => void): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = (progressEvent.loaded / progressEvent.total) * 100;
          onProgress(Math.round(progress));
        }
      },
    });

    return response.data;
  },
};

export default api;
