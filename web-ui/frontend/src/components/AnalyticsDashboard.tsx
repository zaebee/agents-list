import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Grid, LinearProgress } from '@mui/material';
import { fetchAnalytics } from '../services/analyticsService';

interface AnalyticsData {
  taskCompletion: {
    totalTasks: number;
    completedTasks: number;
    completionRate: number;
  };
  agentPerformance: {
    [agentName: string]: {
      totalTasks: number;
      completedTasks: number;
      successRate: number;
    };
  };
  executiveDashboard: {
    systemOverview: {
      totalAgents: number;
      activeIntegrations: number;
      systemHealth: number;
    };
    performanceKPIs: {
      taskCompletionRate: number;
      topPerformingAgents: Array<{
        agent: string;
        successRate: number;
      }>;
      workflowEfficiency: number;
    };
  };
}

const AnalyticsDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        const data = await fetchAnalytics();
        setAnalytics(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to load analytics:', error);
        setLoading(false);
      }
    };

    loadAnalytics();
    const intervalId = setInterval(loadAnalytics, 5 * 60 * 1000); // Refresh every 5 minutes

    return () => clearInterval(intervalId);
  }, []);

  if (loading) {
    return <LinearProgress />;
  }

  if (!analytics) {
    return <Typography variant="h6">Unable to load analytics</Typography>;
  }

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6">System Overview</Typography>
            <Typography>Total Agents: {analytics.executiveDashboard.systemOverview.totalAgents}</Typography>
            <Typography>Active Integrations: {analytics.executiveDashboard.systemOverview.activeIntegrations}</Typography>
            <Typography>System Health: {analytics.executiveDashboard.systemOverview.systemHealth}%</Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6">Task Performance</Typography>
            <Typography>Total Tasks: {analytics.taskCompletion.totalTasks}</Typography>
            <Typography>Completed Tasks: {analytics.taskCompletion.completedTasks}</Typography>
            <Typography>Completion Rate: {analytics.taskCompletion.completionRate.toFixed(2)}%</Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6">Top Performing Agents</Typography>
            {analytics.executiveDashboard.performanceKPIs.topPerformingAgents.map((agent, index) => (
              <Typography key={index}>
                {agent.agent}: {agent.successRate.toFixed(2)}% Success Rate
              </Typography>
            ))}
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6">Workflow Efficiency</Typography>
            <Typography>
              Overall Efficiency: {analytics.executiveDashboard.performanceKPIs.workflowEfficiency.toFixed(2)}%
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default AnalyticsDashboard;