// Authentication API service

import axios, { AxiosResponse } from 'axios';
import { LoginCredentials, RegisterData, User, UserFeatures } from '../contexts/AuthContext';

// API base URL - adjust based on environment
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token expiry
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// API response types
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterResponse {
  message: string;
  user_id: number;
  requires_verification: boolean;
}

export interface MessageResponse {
  message: string;
}

export interface SessionInfo {
  id: number;
  ip_address?: string;
  user_agent?: string;
  is_active: boolean;
  created_at: string;
  last_used: string;
  expires_at: string;
}

export interface MonthlyUsage {
  period: string;
  tasks_created: number;
  tasks_limit: number | null;
  subscription_tier: string;
  reset_date: string;
}

// Authentication API methods
export const authAPI = {
  // Authentication
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    const response: AxiosResponse<LoginResponse> = await api.post('/auth/login', credentials);
    return response.data;
  },

  async register(data: RegisterData): Promise<RegisterResponse> {
    const response: AxiosResponse<RegisterResponse> = await api.post('/auth/register', data);
    return response.data;
  },

  async logout(): Promise<MessageResponse> {
    const response: AxiosResponse<MessageResponse> = await api.post('/auth/logout');
    return response.data;
  },

  async logoutAll(): Promise<MessageResponse> {
    const response: AxiosResponse<MessageResponse> = await api.post('/auth/logout-all');
    return response.data;
  },

  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    const response: AxiosResponse<LoginResponse> = await api.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  // Email verification and password reset
  async verifyEmail(token: string): Promise<MessageResponse> {
    const response: AxiosResponse<MessageResponse> = await api.post('/auth/verify-email', {
      token,
    });
    return response.data;
  },

  async requestPasswordReset(email: string): Promise<MessageResponse> {
    const response: AxiosResponse<MessageResponse> = await api.post('/auth/request-password-reset', {
      email,
    });
    return response.data;
  },

  async resetPassword(token: string, newPassword: string): Promise<MessageResponse> {
    const response: AxiosResponse<MessageResponse> = await api.post('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
    return response.data;
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<MessageResponse> {
    const response: AxiosResponse<MessageResponse> = await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },

  // User profile management
  async getProfile(): Promise<User> {
    const response: AxiosResponse<User> = await api.get('/auth/me');
    return response.data;
  },

  async updateProfile(data: Partial<User>): Promise<User> {
    const response: AxiosResponse<{ message: string; requires_verification?: boolean }> = 
      await api.put('/users/profile', data);
    
    // Return updated user profile
    return this.getProfile();
  },

  // Session management
  async getSessions(): Promise<SessionInfo[]> {
    const response: AxiosResponse<SessionInfo[]> = await api.get('/users/sessions');
    return response.data;
  },

  async revokeSession(sessionId: number): Promise<MessageResponse> {
    const response: AxiosResponse<MessageResponse> = await api.delete(`/users/sessions/${sessionId}`);
    return response.data;
  },

  // Subscription and features
  async getUserFeatures(): Promise<UserFeatures> {
    const response: AxiosResponse<UserFeatures> = await api.get('/users/subscription/features');
    return response.data;
  },

  async getMonthlyUsage(): Promise<MonthlyUsage> {
    const response: AxiosResponse<MonthlyUsage> = await api.get('/users/usage/monthly');
    return response.data;
  },

  // Admin endpoints (for admin users)
  async getUsersList(params?: {
    page?: number;
    limit?: number;
    search?: string;
    role?: string;
    subscription_tier?: string;
    account_status?: string;
  }): Promise<{
    users: User[];
    pagination: {
      page: number;
      limit: number;
      total: number;
      pages: number;
    };
  }> {
    const response = await api.get('/users/admin/list', { params });
    return response.data;
  },

  async getUserStats(): Promise<{
    total_users: number;
    active_users: number;
    verified_users: number;
    subscription_breakdown: { [key: string]: number };
    role_breakdown: { [key: string]: number };
    recent_registrations: number;
  }> {
    const response = await api.get('/users/admin/stats');
    return response.data;
  },

  async updateUserAdmin(userId: number, data: {
    full_name?: string;
    email?: string;
    role?: 'user' | 'manager' | 'admin';
    subscription_tier?: 'free' | 'pro' | 'enterprise';
    account_status?: 'active' | 'suspended' | 'deleted' | 'pending_verification';
    is_active?: boolean;
  }): Promise<MessageResponse> {
    const response: AxiosResponse<MessageResponse> = await api.put(`/users/admin/${userId}`, data);
    return response.data;
  },

  async deleteUserAdmin(userId: number): Promise<MessageResponse> {
    const response: AxiosResponse<MessageResponse> = await api.delete(`/users/admin/${userId}`);
    return response.data;
  },
};

// Export the configured axios instance for use in other services
export default api;