import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Avatar,
  Button,
  LinearProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  SmartToy,
  Psychology,
  Code,
  Business,
  Science,
  Analytics,
  Refresh,
  PlayArrow,
  Pause,
  Info,
  CheckCircle,
  Warning,
  Error,
  Settings,
} from '@mui/icons-material';
import { ApiService, Agent, AgentSystemStatus } from '../services/ApiService';

interface AgentCardProps {
  agent: Agent;
  onTest: (agentId: string) => void;
  onInfo: (agent: Agent) => void;
  testing: boolean;
}

function AgentCard({ agent, onTest, onInfo, testing }: AgentCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available':
        return 'success';
      case 'demo':
        return 'info';
      case 'busy':
        return 'warning';
      case 'offline':
        return 'error';
      default:
        return 'default';
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'anthropic':
        return <Psychology sx={{ color: '#FF6B35' }} />;
      case 'openai':
        return <SmartToy sx={{ color: '#00A67E' }} />;
      case 'mistral':
        return <Science sx={{ color: '#FF7000' }} />;
      default:
        return <SmartToy />;
    }
  };

  return (
    <Card 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 4,
        }
      }}
    >
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
            {getProviderIcon(agent.provider)}
          </Avatar>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" component="div" noWrap>
              {agent.name}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 1 }}>
              <Chip
                label={agent.status}
                color={getStatusColor(agent.status) as any}
                size="small"
              />
              <Chip
                label={agent.provider}
                variant="outlined"
                size="small"
              />
            </Box>
          </Box>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, flex: 1 }}>
          {agent.description}
        </Typography>

        {agent.specializations && agent.specializations.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
              Specializations:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {agent.specializations.slice(0, 3).map((spec, index) => (
                <Chip
                  key={index}
                  label={spec}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              ))}
              {agent.specializations.length > 3 && (
                <Chip
                  label={`+${agent.specializations.length - 3}`}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              )}
            </Box>
          </Box>
        )}

        <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
          <Button
            variant="outlined"
            size="small"
            startIcon={<Info />}
            onClick={() => onInfo(agent)}
            fullWidth
          >
            Details
          </Button>
          <Button
            variant="contained"
            size="small"
            startIcon={testing ? <CircularProgress size={16} /> : <PlayArrow />}
            onClick={() => onTest(agent.id)}
            disabled={testing || agent.status === 'offline'}
            fullWidth
          >
            {testing ? 'Testing...' : 'Test'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}

export default function AgentDashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [systemStatus, setSystemStatus] = useState<AgentSystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [agentsResponse, statusResponse] = await Promise.all([
        ApiService.get('/api/agents'),
        ApiService.get('/api/agents/status'),
      ]);
      
      setAgents(agentsResponse.data.agents || []);
      setSystemStatus(statusResponse.data);
    } catch (error) {
      console.error('Failed to load agent data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTestAgent = async (agentId: string) => {
    setTesting(agentId);
    try {
      const response = await ApiService.post('/api/agents/execute', {
        agent_id: agentId,
        task: 'Hello! This is a test message. Please respond to confirm you are working correctly.',
      });
      
      // Show success feedback
      console.log('Test successful:', response.data);
    } catch (error) {
      console.error('Test failed:', error);
    } finally {
      setTesting(null);
    }
  };

  const handleShowInfo = (agent: Agent) => {
    setSelectedAgent(agent);
    setInfoDialogOpen(true);
  };

  const getSystemStatusIcon = () => {
    if (!systemStatus) return <Warning />;
    
    switch (systemStatus.system_status) {
      case 'ready':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'demo_mode':
        return <Warning sx={{ color: 'warning.main' }} />;
      case 'offline':
        return <Error sx={{ color: 'error.main' }} />;
      default:
        return <Warning />;
    }
  };

  const getSystemStatusMessage = () => {
    if (!systemStatus) return 'Loading system status...';
    
    switch (systemStatus.system_status) {
      case 'ready':
        return 'All systems operational';
      case 'demo_mode':
        return 'Running in demo mode - some features limited';
      case 'offline':
        return 'System offline - agents unavailable';
      default:
        return 'System status unknown';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* System Status */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: 'rgba(102, 126, 234, 0.05)' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getSystemStatusIcon()}
            AI Agent System Status
          </Typography>
          <Tooltip title="Refresh status">
            <IconButton onClick={loadData} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>

        <Alert severity={systemStatus?.system_status === 'ready' ? 'success' : 'warning'}>
          {getSystemStatusMessage()}
        </Alert>

        {systemStatus && (
          <Grid container spacing={3} sx={{ mt: 2 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="primary.main">
                  {systemStatus.total_agents}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Agents
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {systemStatus.active_agents}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Agents
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="info.main">
                  {systemStatus.demo_agents}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Demo Agents
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {Object.keys(systemStatus.providers).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Providers
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        )}
      </Paper>

      {/* Agent Grid */}
      <Typography variant="h5" gutterBottom>
        Available AI Agents
      </Typography>
      
      <Grid container spacing={3}>
        {agents.map((agent) => (
          <Grid item xs={12} sm={6} md={4} key={agent.id}>
            <AgentCard
              agent={agent}
              onTest={handleTestAgent}
              onInfo={handleShowInfo}
              testing={testing === agent.id}
            />
          </Grid>
        ))}
      </Grid>

      {agents.length === 0 && (
        <Alert severity="info" sx={{ mt: 3 }}>
          No AI agents available. Please check your configuration.
        </Alert>
      )}

      {/* Agent Details Dialog */}
      <Dialog
        open={infoDialogOpen}
        onClose={() => setInfoDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <SmartToy />
            </Avatar>
            {selectedAgent?.name}
            <Chip
              label={selectedAgent?.status}
              color={selectedAgent?.status === 'available' ? 'success' : 'default'}
              size="small"
            />
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedAgent && (
            <Box>
              <Typography variant="body1" paragraph>
                {selectedAgent.description}
              </Typography>
              
              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Technical Details
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <Settings />
                  </ListItemIcon>
                  <ListItemText
                    primary="Provider"
                    secondary={selectedAgent.provider}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Code />
                  </ListItemIcon>
                  <ListItemText
                    primary="Model"
                    secondary={selectedAgent.model || 'Default'}
                  />
                </ListItem>
              </List>

              {selectedAgent.specializations && selectedAgent.specializations.length > 0 && (
                <>
                  <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                    Specializations
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {selectedAgent.specializations.map((spec, index) => (
                      <Chip
                        key={index}
                        label={spec}
                        variant="outlined"
                        size="small"
                      />
                    ))}
                  </Box>
                </>
              )}

              {selectedAgent.capabilities && selectedAgent.capabilities.length > 0 && (
                <>
                  <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                    Capabilities
                  </Typography>
                  <List dense>
                    {selectedAgent.capabilities.map((capability, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <CheckCircle color="success" />
                        </ListItemIcon>
                        <ListItemText primary={capability} />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoDialogOpen(false)}>
            Close
          </Button>
          {selectedAgent && (
            <Button
              variant="contained"
              startIcon={testing === selectedAgent.id ? <CircularProgress size={16} /> : <PlayArrow />}
              onClick={() => {
                handleTestAgent(selectedAgent.id);
                setInfoDialogOpen(false);
              }}
              disabled={testing === selectedAgent.id || selectedAgent.status === 'offline'}
            >
              {testing === selectedAgent.id ? 'Testing...' : 'Test Agent'}
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}