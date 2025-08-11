/**
 * API Service
 * Centralized HTTP client with authentication and error handling
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { AuthService } from './AuthService';

class ApiServiceClass {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NODE_ENV === 'development' ? 'http://localhost:5001' : '',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth headers
    this.client.interceptors.request.use(
      (config) => {
        const authHeaders = AuthService.getAuthHeader();
        config.headers = { ...config.headers, ...authHeaders };
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          AuthService.logout();
          window.location.reload();
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * GET request
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config);
  }

  /**
   * POST request
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config);
  }

  /**
   * PUT request
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config);
  }

  /**
   * DELETE request
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config);
  }

  /**
   * Upload file
   */
  async uploadFile<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<AxiosResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.client.post<T>(url, formData, {
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
  }
}

// Export singleton instance
export const ApiService = new ApiServiceClass();

// Types for AI API responses
export interface Agent {
  id: string;
  name: string;
  description: string;
  provider: string;
  model: string;
  status: 'available' | 'demo' | 'busy' | 'offline';
  specializations: string[];
  capabilities: string[];
}

export interface AgentAnalysis {
  task_description: string;
  suggested_agent: {
    id: string;
    name: string;
    confidence: number;
    reasoning: string;
  };
  all_agents: Array<{ id: string; name: string }>;
  timestamp: string;
}

export interface TaskExecution {
  task_id: string;
  agent_id: string;
  status: 'demo_completed' | 'processing' | 'completed' | 'failed';
  result?: {
    type: string;
    message: string;
    suggestions?: string[];
    analysis?: string;
    recommendations?: string[];
  };
  execution_time?: string;
  timestamp: string;
  demo_mode: boolean;
}

export interface AgentSystemStatus {
  system_status: 'ready' | 'demo_mode' | 'offline';
  total_agents: number;
  active_agents: number;
  demo_agents: number;
  providers: {
    [key: string]: {
      configured: boolean;
      status: string;
      agents: string[];
    };
  };
  timestamp: string;
}