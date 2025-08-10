// Authentication context for React application

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { authAPI } from '../services/authAPI';

// Types
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: 'user' | 'manager' | 'admin';
  subscription_tier: 'free' | 'pro' | 'enterprise';
  is_verified: boolean;
  account_status: 'active' | 'suspended' | 'deleted' | 'pending_verification';
  created_at: string;
  last_login?: string;
  monthly_tasks_created: number;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  username_or_email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface UserFeatures {
  subscription_tier: string;
  features: {
    [key: string]: {
      has_access: boolean;
      description: string;
      usage_limit: number | null;
      current_usage: number;
    };
  };
}

// Action types
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; token: string; refreshToken: string } }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'UPDATE_USER'; payload: User }
  | { type: 'CLEAR_ERROR' };

// Initial state
const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

// Reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };

    case 'AUTH_FAILURE':
      return {
        ...state,
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };

    case 'LOGOUT':
      return {
        ...state,
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };

    case 'UPDATE_USER':
      return {
        ...state,
        user: action.payload,
      };

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };

    default:
      return state;
  }
}

// Context
export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  refreshTokens: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  requestPasswordReset: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  verifyEmail: (token: string) => Promise<void>;
  getUserFeatures: () => Promise<UserFeatures>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');

      if (token && refreshToken) {
        try {
          // Try to get user profile to validate token
          const user = await authAPI.getProfile();
          dispatch({
            type: 'AUTH_SUCCESS',
            payload: { user, token, refreshToken },
          });
        } catch (error) {
          // Token might be expired, try to refresh
          try {
            await refreshTokens();
          } catch (refreshError) {
            // Both tokens are invalid, logout
            logout();
          }
        }
      }
    };

    initializeAuth();
  }, []);

  // Auto-refresh token before expiry
  useEffect(() => {
    if (state.isAuthenticated && state.refreshToken) {
      // Set up token refresh timer (refresh 5 minutes before expiry)
      const refreshInterval = setInterval(async () => {
        try {
          await refreshTokens();
        } catch (error) {
          console.error('Failed to refresh token:', error);
          logout();
        }
      }, 25 * 60 * 1000); // 25 minutes

      return () => clearInterval(refreshInterval);
    }
  }, [state.isAuthenticated, state.refreshToken]);

  const login = async (credentials: LoginCredentials) => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await authAPI.login(credentials);
      
      // Store tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: response.user,
          token: response.access_token,
          refreshToken: response.refresh_token,
        },
      });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed';
      dispatch({ type: 'AUTH_FAILURE', payload: message });
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    dispatch({ type: 'AUTH_START' });

    try {
      await authAPI.register(data);
      // Registration successful, but user needs to verify email
      dispatch({ type: 'LOGOUT' }); // Clear loading state
    } catch (error: any) {
      const message = error.response?.data?.detail?.message || 
                     error.response?.data?.detail || 
                     'Registration failed';
      dispatch({ type: 'AUTH_FAILURE', payload: message });
      throw error;
    }
  };

  const logout = async () => {
    try {
      if (state.token) {
        await authAPI.logout();
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage and state regardless of API call result
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      dispatch({ type: 'LOGOUT' });
    }
  };

  const logoutAll = async () => {
    try {
      if (state.token) {
        await authAPI.logoutAll();
      }
    } catch (error) {
      console.error('Logout all error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      dispatch({ type: 'LOGOUT' });
    }
  };

  const refreshTokens = async () => {
    if (!state.refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await authAPI.refreshToken(state.refreshToken);
      
      // Update stored tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: response.user,
          token: response.access_token,
          refreshToken: response.refresh_token,
        },
      });
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      dispatch({ type: 'LOGOUT' });
      throw error;
    }
  };

  const updateProfile = async (data: Partial<User>) => {
    try {
      const updatedUser = await authAPI.updateProfile(data);
      dispatch({ type: 'UPDATE_USER', payload: updatedUser });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Profile update failed';
      dispatch({ type: 'AUTH_FAILURE', payload: message });
      throw error;
    }
  };

  const changePassword = async (currentPassword: string, newPassword: string) => {
    try {
      await authAPI.changePassword(currentPassword, newPassword);
    } catch (error: any) {
      const message = error.response?.data?.detail?.message || 
                     error.response?.data?.detail || 
                     'Password change failed';
      throw new Error(message);
    }
  };

  const requestPasswordReset = async (email: string) => {
    try {
      await authAPI.requestPasswordReset(email);
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Password reset request failed';
      throw new Error(message);
    }
  };

  const resetPassword = async (token: string, newPassword: string) => {
    try {
      await authAPI.resetPassword(token, newPassword);
    } catch (error: any) {
      const message = error.response?.data?.detail?.message || 
                     error.response?.data?.detail || 
                     'Password reset failed';
      throw new Error(message);
    }
  };

  const verifyEmail = async (token: string) => {
    try {
      await authAPI.verifyEmail(token);
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Email verification failed';
      throw new Error(message);
    }
  };

  const getUserFeatures = async (): Promise<UserFeatures> => {
    try {
      return await authAPI.getUserFeatures();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to fetch user features';
      throw new Error(message);
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    logoutAll,
    refreshTokens,
    updateProfile,
    changePassword,
    requestPasswordReset,
    resetPassword,
    verifyEmail,
    getUserFeatures,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Hook for subscription tier checks
export const useSubscription = () => {
  const { user } = useAuth();
  
  const hasFeature = (feature: string, features: UserFeatures) => {
    return features.features[feature]?.has_access || false;
  };

  const isFreeTier = () => user?.subscription_tier === 'free';
  const isProTier = () => user?.subscription_tier === 'pro';
  const isEnterpriseTier = () => user?.subscription_tier === 'enterprise';
  
  const hasProOrHigher = () => ['pro', 'enterprise'].includes(user?.subscription_tier || '');
  const hasEnterpriseOnly = () => user?.subscription_tier === 'enterprise';

  return {
    subscriptionTier: user?.subscription_tier,
    isFreeTier,
    isProTier,
    isEnterpriseTier,
    hasProOrHigher,
    hasEnterpriseOnly,
    hasFeature,
  };
};

// Hook for role-based access
export const useRole = () => {
  const { user } = useAuth();
  
  const isUser = () => user?.role === 'user';
  const isManager = () => user?.role === 'manager';
  const isAdmin = () => user?.role === 'admin';
  
  const hasManagerAccess = () => ['manager', 'admin'].includes(user?.role || '');
  const hasAdminAccess = () => user?.role === 'admin';

  return {
    role: user?.role,
    isUser,
    isManager,
    isAdmin,
    hasManagerAccess,
    hasAdminAccess,
  };
};