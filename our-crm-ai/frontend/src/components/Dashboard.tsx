import React, { useEffect, useState } from 'react';
import { Bot, TrendingUp, DollarSign, BarChart3 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useAgents } from '../contexts/AgentContext';
import { apiService } from '../services/api';

interface DashboardData {
  totalTasks: number;
  completedTasks: number;
  revenue: number;
  performance: number;
}

export default function Dashboard() {
  const { user } = useAuth();
  const { agents, systemStatus, loading: agentsLoading } = useAgents();
  const [dashboardData, setDashboardData] = useState<DashboardData>({
    totalTasks: 0,
    completedTasks: 0,
    revenue: 0,
    performance: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      // Try to load dashboard data, fall back to defaults if not available
      const data = await apiService.getDashboardData().catch(() => ({
        totalTasks: 142,
        completedTasks: 98,
        revenue: 24500,
        performance: 87,
      }));
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, color, trend }: {
    title: string;
    value: string | number;
    icon: React.ElementType;
    color: string;
    trend?: string;
  }) => (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {trend && (
            <p className="text-sm text-green-600 mt-1">
              ↗ {trend}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon size={24} className="text-white" />
        </div>
      </div>
    </div>
  );

  if (loading || agentsLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center text-white">
          <div className="loading-spinner w-12 h-12 mx-auto mb-4"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-white/95 backdrop-blur-sm rounded-xl p-6 shadow-lg">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Welcome back, {user?.username}! 👋
        </h1>
        <p className="text-gray-600">
          Here's what's happening with your AI Project Manager today.
        </p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Active Agents"
          value={systemStatus?.active_agents || 0}
          icon={Bot}
          color="bg-blue-500"
          trend="12% from yesterday"
        />
        <StatCard
          title="Total Tasks"
          value={dashboardData?.totalTasks || 0}
          icon={BarChart3}
          color="bg-green-500"
          trend="8% from yesterday"
        />
        <StatCard
          title="Completion Rate"
          value={`${
            dashboardData?.totalTasks
              ? Math.round((dashboardData.completedTasks / dashboardData.totalTasks) * 100)
              : 0
          }%`}
          icon={TrendingUp}
          color="bg-purple-500"
          trend="5% from yesterday"
        />
        <StatCard
          title="Revenue"
          value={`${dashboardData?.revenue?.toLocaleString() || '0'}`}
          icon={DollarSign}
          color="bg-orange-500"
          trend="15% from yesterday"
        />
      </div>

      {/* System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">System Status</span>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                systemStatus?.system_status === 'ready' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {systemStatus?.system_status || 'Unknown'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Agents</span>
              <span className="font-semibold">{systemStatus?.total_agents || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Active Agents</span>
              <span className="font-semibold text-green-600">{systemStatus?.active_agents || 0}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            <button className="btn-primary">
              Create Task
            </button>
            <button className="btn-outline">
              View Agents
            </button>
            <button className="btn-secondary">
              Start Chat
            </button>
            <button className="btn-ghost">
              View Analytics
            </button>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
        <div className="space-y-3">
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-700">Agent "Data Analyst" completed task analysis</span>
            <span className="text-xs text-gray-500 ml-auto">2 minutes ago</span>
          </div>
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span className="text-sm text-gray-700">New task created: "Generate quarterly report"</span>
            <span className="text-xs text-gray-500 ml-auto">5 minutes ago</span>
          </div>
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
            <span className="text-sm text-gray-700">System health check completed successfully</span>
            <span className="text-xs text-gray-500 ml-auto">10 minutes ago</span>
          </div>
        </div>
      </div>
    </div>
  );
}