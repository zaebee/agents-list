import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  IconButton,
  AppBar,
  Toolbar,
  Button,
  Chip,
  Avatar,
  Menu,
  MenuItem,
  Badge,
  Tooltip,
} from '@mui/material';
import {
  SmartToy,
  Dashboard as DashboardIcon,
  Chat,
  Assignment,
  AccountCircle,
  Logout,
  Notifications,
  Analytics,
  TrendingUp,
  AttachMoney,
  Assessment,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Chart components
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';
import { Doughnut, Line, Bar } from 'react-chartjs-2';

import { ApiService, AgentSystemStatus } from '../services/ApiService';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

interface DashboardProps {
  user: {
    username: string;
    email: string;
    role: string;
    id: string;
  };
  onLogout: () => void;
}

interface ExecutiveDashboardData {
  overall_metrics: {
    total_projects: number;
    projected_revenue: number;
    total_investment: number;
    avg_roi: number;
    avg_risk_score: number;
  };
  project_status_breakdown: Record<string, number>;
  recent_projects: Array<{
    id: string;
    name: string;
    status: string;
    completion_percentage: number;
    projected_roi: number;
    target_revenue: number;
    created_at: string;
  }>;
  generated_at: string;
}

export default function Dashboard({ user, onLogout }: DashboardProps) {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [dashboardData, setDashboardData] = useState<ExecutiveDashboardData | null>(null);
  const [agentStatus, setAgentStatus] = useState<AgentSystemStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    loadAgentStatus();
    
    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      loadDashboardData();
      loadAgentStatus();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await ApiService.get('/api/executive-dashboard');
      setDashboardData(response.data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAgentStatus = async () => {
    try {
      const response = await ApiService.get('/api/agents/status');
      setAgentStatus(response.data);
    } catch (error) {
      console.error('Failed to load agent status:', error);
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  // Chart configurations
  const projectStatusData = {
    labels: Object.keys(dashboardData?.project_status_breakdown || {}),
    datasets: [
      {
        data: Object.values(dashboardData?.project_status_breakdown || {}),
        backgroundColor: [
          '#667eea',
          '#764ba2',
          '#f093fb',
          '#f5576c',
          '#4facfe',
        ],
        borderWidth: 0,
      },
    ],
  };

  const revenueProjectionData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'Projected Revenue',
        data: [450000, 520000, 680000, 890000, 1200000, 1400000],
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        tension: 0.4,
      },
    ],
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* App Bar */}
      <AppBar 
        position=\"static\" 
        elevation={0}
        sx={{ 
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          color: 'primary.main',
          mb: 3
        }}
      >
        <Toolbar>
          <Typography variant=\"h6\" component=\"div\" sx={{ flexGrow: 1, fontWeight: 700 }}>
            🎯 AI Project Manager
          </Typography>

          {/* AI Status Indicator */}
          {agentStatus && (
            <Tooltip title={`AI System: ${agentStatus.system_status}`}>
              <Chip
                icon={<SmartToy />}
                label={`${agentStatus.active_agents}/${agentStatus.total_agents} Agents`}
                color={agentStatus.active_agents > 0 ? 'success' : 'warning'}
                variant=\"outlined\"
                sx={{ mr: 2 }}
              />
            </Tooltip>
          )}

          <Badge badgeContent={3} color=\"error\">
            <IconButton color=\"inherit\">
              <Notifications />
            </IconButton>
          </Badge>

          <IconButton
            size=\"large\"
            edge=\"end\"
            aria-label=\"account menu\"
            aria-controls=\"account-menu\"
            aria-haspopup=\"true\"
            onClick={handleMenuOpen}
            color=\"inherit\"
          >
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
              {user.username.charAt(0).toUpperCase()}
            </Avatar>
          </IconButton>

          <Menu
            id=\"account-menu\"
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            onClick={handleMenuClose}
          >
            <MenuItem>
              <AccountCircle sx={{ mr: 1 }} />
              {user.username} ({user.role})
            </MenuItem>
            <MenuItem onClick={onLogout}>
              <Logout sx={{ mr: 1 }} />
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Navigation Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card 
            sx={{ cursor: 'pointer', transition: 'transform 0.2s' }}
            onClick={() => navigate('/agents')}
            onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
            onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <CardContent sx={{ textAlign: 'center' }}>
              <SmartToy sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant=\"h6\">AI Agents</Typography>
              <Typography variant=\"body2\" color=\"textSecondary\">
                Manage AI assistants
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card 
            sx={{ cursor: 'pointer', transition: 'transform 0.2s' }}
            onClick={() => navigate('/chat')}
            onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
            onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <CardContent sx={{ textAlign: 'center' }}>
              <Chat sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
              <Typography variant=\"h6\">AI Chat</Typography>
              <Typography variant=\"body2\" color=\"textSecondary\">
                Chat with agents
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card 
            sx={{ cursor: 'pointer', transition: 'transform 0.2s' }}
            onClick={() => navigate('/tasks')}
            onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
            onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <CardContent sx={{ textAlign: 'center' }}>
              <Assignment sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant=\"h6\">Task Manager</Typography>
              <Typography variant=\"body2\" color=\"textSecondary\">
                Manage AI tasks
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ cursor: 'pointer', transition: 'transform 0.2s' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Analytics sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant=\"h6\">Analytics</Typography>
              <Typography variant=\"body2\" color=\"textSecondary\">
                Business insights
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Metrics Overview */}
      {dashboardData && (
        <>
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 3, textAlign: 'center' }}>
                <TrendingUp sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                <Typography variant=\"h4\" color=\"success.main\">
                  {dashboardData.overall_metrics.total_projects}
                </Typography>
                <Typography variant=\"body2\" color=\"textSecondary\">
                  Active Projects
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 3, textAlign: 'center' }}>
                <AttachMoney sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant=\"h4\" color=\"primary.main\">
                  {formatCurrency(dashboardData.overall_metrics.projected_revenue)}
                </Typography>
                <Typography variant=\"body2\" color=\"textSecondary\">
                  Projected Revenue
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 3, textAlign: 'center' }}>
                <Assessment sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                <Typography variant=\"h4\" color=\"warning.main\">
                  {formatPercentage(dashboardData.overall_metrics.avg_roi)}
                </Typography>
                <Typography variant=\"body2\" color=\"textSecondary\">
                  Average ROI
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 3, textAlign: 'center' }}>
                <SmartToy sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                <Typography variant=\"h4\" color=\"secondary.main\">
                  {agentStatus?.active_agents || 0}
                </Typography>
                <Typography variant=\"body2\" color=\"textSecondary\">
                  Active AI Agents
                </Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* Charts */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 3 }}>
                <Typography variant=\"h6\" gutterBottom>
                  Project Status Distribution
                </Typography>
                <Doughnut 
                  data={projectStatusData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                      legend: {
                        position: 'bottom',
                      },
                    },
                  }}
                />
              </Paper>
            </Grid>

            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 3 }}>
                <Typography variant=\"h6\" gutterBottom>
                  Revenue Projection
                </Typography>
                <Line 
                  data={revenueProjectionData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                      legend: {
                        position: 'top',
                      },
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        ticks: {
                          callback: (value) => formatCurrency(Number(value)),
                        },
                      },
                    },
                  }}
                />
              </Paper>
            </Grid>
          </Grid>
        </>
      )}
    </Box>
  );
}