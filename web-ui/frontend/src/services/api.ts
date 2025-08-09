// API service for communicating with the FastAPI backend

import axios, { AxiosResponse } from 'axios';
import {
  Task,
  TaskCreate,
  TaskUpdate,
  TaskMove,
  TaskComment,
  TaskDetails,
  AgentSuggestion,
  ApiResponse,
  PMAnalysis
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const apiService = {
  // Health check
  async healthCheck(): Promise<{ status: string; config_loaded: boolean }> {
    const response = await api.get('/health');
    return response.data;
  },

  // Task operations
  async listTasks(): Promise<Task[]> {
    const response = await api.get('/tasks');
    return response.data;
  },

  async createTask(task: TaskCreate): Promise<ApiResponse> {
    const response = await api.post('/tasks', task);
    return response.data;
  },

  async updateTask(taskId: string, update: TaskUpdate): Promise<ApiResponse> {
    const response = await api.put(`/tasks/${taskId}`, update);
    return response.data;
  },

  async moveTask(taskId: string, move: TaskMove): Promise<ApiResponse> {
    const response = await api.put(`/tasks/${taskId}/move`, move);
    return response.data;
  },

  async getTaskDetails(taskId: string): Promise<TaskDetails> {
    const response = await api.get(`/tasks/${taskId}`);
    return response.data;
  },

  async addComment(taskId: string, comment: TaskComment): Promise<ApiResponse> {
    const response = await api.post(`/tasks/${taskId}/comments`, comment);
    return response.data;
  },

  // Agent operations
  async listAgents(): Promise<string[]> {
    const response = await api.get('/agents');
    return response.data;
  },

  async suggestAgents(task: TaskCreate): Promise<AgentSuggestion[]> {
    const response = await api.post('/agents/suggest', task);
    return response.data;
  },

  // PM Agent Gateway
  async pmAnalyzeTask(task: TaskCreate): Promise<PMAnalysis> {
    const response = await api.post('/pm/analyze', task);
    return response.data;
  },
};

export default apiService;