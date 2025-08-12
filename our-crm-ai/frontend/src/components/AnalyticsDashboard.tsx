import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { Activity, DollarSign, Users, Zap, TrendingUp, TrendingDown, Clock, AlertCircle } from 'lucide-react';
import { useDashboardUpdates } from '../hooks/useRealTimeUpdates';
import { apiService } from '../services/api';

interface MetricCard {
  title: string;
  value: string | number;
  change: number;
  changeType: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
}

interface AnalyticsData {
  overview: {
    totalTasks: number;
    activeTasks: number;
    completedTasks: number;
    totalUsers: number;
    revenue: number;
    agentUtilization: number;
  };
  taskTrends: Array<{
    date: string;
    created: number;
    completed: number;
    failed: number;
  }>;
  agentPerformance: Array<{
    name: string;
    tasksCompleted: number;
    successRate: number;
    avgResponseTime: number;
    cost: number;
  }>;
  revenueData: Array<{
    month: string;
    revenue: number;
    subscriptions: number;
  }>;
  userTierDistribution: Array<{
    tier: string;
    users: number;
    revenue: number;
  }>;
  systemHealth: {
    uptime: number;
    responseTime: number;
    errorRate: number;
    activeConnections: number;
  };
}

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#ffdcd5', '#4facfe'];

const AnalyticsDashboard: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | '90d'>('7d');
  const [selectedMetric, setSelectedMetric] = useState<'tasks' | 'revenue' | 'agents'>('tasks');

  // Real-time updates for dashboard data
  useDashboardUpdates((data) => {
    if (data.type === 'metrics_update') {
      setAnalyticsData(current => current ? { ...current, ...data.payload } : null);
    }
  });

  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const data = await apiService.getAnalytics(timeRange);
      setAnalyticsData(data);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
      // Set mock data for demo
      setAnalyticsData(getMockAnalyticsData());
    } finally {
      setLoading(false);
    }
  };

  const getMockAnalyticsData = (): AnalyticsData => ({
    overview: {
      totalTasks: 12847,
      activeTasks: 234,
      completedTasks: 12613,
      totalUsers: 1456,
      revenue: 45230,
      agentUtilization: 78.5,
    },
    taskTrends: Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      created: Math.floor(Math.random() * 100) + 200,
      completed: Math.floor(Math.random() * 90) + 180,
      failed: Math.floor(Math.random() * 10) + 5,
    })),
    agentPerformance: [
      { name: 'Code Reviewer', tasksCompleted: 1234, successRate: 96.5, avgResponseTime: 2.3, cost: 125.67 },
      { name: 'Data Analyst', tasksCompleted: 987, successRate: 94.2, avgResponseTime: 3.1, cost: 87.43 },
      { name: 'Business Analyst', tasksCompleted: 876, successRate: 98.1, avgResponseTime: 1.8, cost: 92.15 },
      { name: 'Frontend Developer', tasksCompleted: 765, successRate: 92.7, avgResponseTime: 4.2, cost: 156.89 },
      { name: 'Security Auditor', tasksCompleted: 543, successRate: 99.2, avgResponseTime: 5.1, cost: 234.56 },
    ],
    revenueData: Array.from({ length: 12 }, (_, i) => ({
      month: new Date(2024, i, 1).toLocaleDateString('en-US', { month: 'short' }),
      revenue: Math.floor(Math.random() * 20000) + 30000,
      subscriptions: Math.floor(Math.random() * 100) + 200,
    })),
    userTierDistribution: [
      { tier: 'Free', users: 856, revenue: 0 },
      { tier: 'Pro', users: 485, revenue: 23765 },
      { tier: 'Enterprise', users: 115, revenue: 34425 },
    ],
    systemHealth: {
      uptime: 99.8,
      responseTime: 245,
      errorRate: 0.12,
      activeConnections: 1247,
    },
  });

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  if (loading || !analyticsData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const metricCards: MetricCard[] = [
    {
      title: 'Total Tasks',
      value: analyticsData.overview.totalTasks.toLocaleString(),
      change: 12.5,
      changeType: 'positive',
      icon: <Activity className="h-6 w-6" />,
    },
    {
      title: 'Active Tasks',
      value: analyticsData.overview.activeTasks.toLocaleString(),
      change: 8.2,
      changeType: 'positive',
      icon: <Zap className="h-6 w-6" />,
    },
    {
      title: 'Total Revenue',
      value: formatCurrency(analyticsData.overview.revenue),
      change: 15.3,
      changeType: 'positive',
      icon: <DollarSign className="h-6 w-6" />,
    },
    {
      title: 'Total Users',
      value: analyticsData.overview.totalUsers.toLocaleString(),
      change: 7.8,
      changeType: 'positive',
      icon: <Users className="h-6 w-6" />,
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Monitor system performance and business metrics</p>
        </div>
        
        <div className="flex items-center space-x-4 mt-4 sm:mt-0">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
          
          <button
            onClick={loadAnalyticsData}
            className="btn-primary flex items-center space-x-2"
          >
            <Activity className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* System Health Alert */}
      {analyticsData.systemHealth.uptime < 99.5 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 text-yellow-600" />
          <div>
            <p className="text-yellow-800 font-medium">System Health Alert</p>
            <p className="text-yellow-700 text-sm">
              Current uptime is {formatPercentage(analyticsData.systemHealth.uptime)}. 
              Consider investigating potential issues.
            </p>
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metricCards.map((metric, index) => (
          <div key={index} className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{metric.title}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{metric.value}</p>
              </div>
              <div className="p-3 bg-primary-100 rounded-lg">
                {metric.icon}
              </div>
            </div>
            
            <div className="mt-4 flex items-center">
              {metric.changeType === 'positive' ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
              <span className={`text-sm font-medium ml-1 ${
                metric.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
              }`}>
                {metric.change}%
              </span>
              <span className="text-sm text-gray-500 ml-1">vs previous period</span>
            </div>
          </div>
        ))}
      </div>

      {/* Chart Selection */}
      <div className="flex space-x-4 border-b border-gray-200">
        <button
          onClick={() => setSelectedMetric('tasks')}
          className={`py-2 px-4 border-b-2 transition-colors ${
            selectedMetric === 'tasks'
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Task Analytics
        </button>
        <button
          onClick={() => setSelectedMetric('revenue')}
          className={`py-2 px-4 border-b-2 transition-colors ${
            selectedMetric === 'revenue'
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Revenue Analytics
        </button>
        <button
          onClick={() => setSelectedMetric('agents')}
          className={`py-2 px-4 border-b-2 transition-colors ${
            selectedMetric === 'agents'
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Agent Performance
        </button>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {selectedMetric === 'tasks' && (
          <>
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">Task Trends</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={analyticsData.taskTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="created" stackId="1" stroke="#667eea" fill="#667eea" />
                  <Area type="monotone" dataKey="completed" stackId="2" stroke="#4ade80" fill="#4ade80" />
                  <Area type="monotone" dataKey="failed" stackId="3" stroke="#ef4444" fill="#ef4444" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">Task Success Rate</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analyticsData.taskTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(value: any, name: any) => [`${value}%`, name]} />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey={(entry: any) => ((entry.completed / (entry.completed + entry.failed)) * 100).toFixed(1)} 
                    stroke="#667eea" 
                    strokeWidth={2}
                    name="Success Rate"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </>
        )}

        {selectedMetric === 'revenue' && (
          <>
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">Revenue Trends</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analyticsData.revenueData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value as number)} />
                  <Legend />
                  <Bar dataKey="revenue" fill="#667eea" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">User Tier Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analyticsData.userTierDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ tier, users }) => `${tier}: ${users}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="users"
                  >
                    {analyticsData.userTierDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </>
        )}

        {selectedMetric === 'agents' && (
          <>
            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">Agent Performance</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analyticsData.agentPerformance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="tasksCompleted" fill="#667eea" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-6">
              <h3 className="text-lg font-semibold mb-4">Agent Success Rates</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analyticsData.agentPerformance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => `${value}%`} />
                  <Legend />
                  <Bar dataKey="successRate" fill="#4ade80" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>

      {/* System Health Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Activity className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Uptime</p>
              <p className="text-lg font-semibold">{formatPercentage(analyticsData.systemHealth.uptime)}</p>
            </div>
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Clock className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Response Time</p>
              <p className="text-lg font-semibold">{analyticsData.systemHealth.responseTime}ms</p>
            </div>
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Error Rate</p>
              <p className="text-lg font-semibold">{formatPercentage(analyticsData.systemHealth.errorRate)}</p>
            </div>
          </div>
        </div>

        <div className="card p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Users className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active Connections</p>
              <p className="text-lg font-semibold">{analyticsData.systemHealth.activeConnections.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Details Table */}
      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold">Agent Performance Details</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tasks Completed</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Success Rate</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Response Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {analyticsData.agentPerformance.map((agent, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{agent.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{agent.tasksCompleted.toLocaleString()}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      agent.successRate >= 95 
                        ? 'bg-green-100 text-green-800'
                        : agent.successRate >= 90
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {formatPercentage(agent.successRate)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{agent.avgResponseTime.toFixed(1)}s</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-900 font-medium">{formatCurrency(agent.cost)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;