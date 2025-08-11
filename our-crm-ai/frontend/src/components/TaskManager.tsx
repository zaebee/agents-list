import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Tooltip,
  Card,
  CardContent,
  LinearProgress,
  SelectChangeEvent,
} from '@mui/material';
import {
  Add,
  PlayArrow,
  Pause,
  Stop,
  Visibility,
  Delete,
  Refresh,
  Assignment,
  Schedule,
  CheckCircle,
  Error,
  SmartToy,
} from '@mui/icons-material';
import { ApiService, Agent } from '../services/ApiService';

interface Task {
  id: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  agent_id?: string;
  agent_name?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  result?: {
    type: string;
    message: string;
    analysis?: string;
    suggestions?: string[];
  };
  error?: string;
  progress?: number;
}

interface TaskStats {
  total: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
}

export default function TaskManager() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [stats, setStats] = useState<TaskStats>({
    total: 0,
    pending: 0,
    running: 0,
    completed: 0,
    failed: 0,
  });
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [newTask, setNewTask] = useState({
    description: '',
    agent_id: '',
  });

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [tasksResponse, agentsResponse] = await Promise.all([
        ApiService.get('/api/tasks'),
        ApiService.get('/api/agents'),
      ]);

      const tasksData = tasksResponse.data.tasks || [];
      setTasks(tasksData);
      setAgents(agentsResponse.data.agents || []);

      // Calculate stats
      const stats = tasksData.reduce(
        (acc: TaskStats, task: Task) => {
          acc.total++;
          acc[task.status as keyof TaskStats]++;
          return acc;
        },
        { total: 0, pending: 0, running: 0, completed: 0, failed: 0 }
      );
      setStats(stats);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async () => {
    if (!newTask.description.trim()) return;

    try {
      await ApiService.post('/api/tasks', {
        description: newTask.description,
        agent_id: newTask.agent_id || undefined,
      });

      setNewTask({ description: '', agent_id: '' });
      setCreateDialogOpen(false);
      loadData();
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  const handleExecuteTask = async (taskId: string) => {
    try {
      await ApiService.post(`/api/tasks/${taskId}/execute`);
      loadData();
    } catch (error) {
      console.error('Failed to execute task:', error);
    }
  };

  const handlePauseTask = async (taskId: string) => {
    try {
      await ApiService.post(`/api/tasks/${taskId}/pause`);
      loadData();
    } catch (error) {
      console.error('Failed to pause task:', error);
    }
  };

  const handleStopTask = async (taskId: string) => {
    try {
      await ApiService.post(`/api/tasks/${taskId}/stop`);
      loadData();
    } catch (error) {
      console.error('Failed to stop task:', error);
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    if (!window.confirm('Are you sure you want to delete this task?')) return;

    try {
      await ApiService.delete(`/api/tasks/${taskId}`);
      loadData();
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  const handleViewTask = (task: Task) => {
    setSelectedTask(task);
    setViewDialogOpen(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'primary';
      case 'pending':
        return 'default';
      case 'failed':
        return 'error';
      case 'paused':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle />;
      case 'running':
        return <PlayArrow />;
      case 'pending':
        return <Schedule />;
      case 'failed':
        return <Error />;
      case 'paused':
        return <Pause />;
      default:
        return <Assignment />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
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
      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary.main">
                {stats.total}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Tasks
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="warning.main">
                {stats.pending}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Pending
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {stats.running}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Running
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="success.main">
                {stats.completed}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Completed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="error.main">
                {stats.failed}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Failed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Actions */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">
          Task Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadData}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Task
          </Button>
        </Box>
      </Box>

      {/* Tasks Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Task Description</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Agent</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map((task) => (
              <TableRow key={task.id} hover>
                <TableCell>
                  <Box sx={{ maxWidth: 300 }}>
                    <Typography variant="body2" noWrap>
                      {task.description}
                    </Typography>
                    {task.status === 'running' && task.progress !== undefined && (
                      <LinearProgress
                        variant="determinate"
                        value={task.progress}
                        sx={{ mt: 1 }}
                      />
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    icon={getStatusIcon(task.status)}
                    label={task.status}
                    color={getStatusColor(task.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {task.agent_name ? (
                    <Chip
                      icon={<SmartToy />}
                      label={task.agent_name}
                      variant="outlined"
                      size="small"
                    />
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      Auto-select
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {formatDate(task.created_at)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {task.completed_at
                      ? `${Math.round(
                          (new Date(task.completed_at).getTime() -
                            new Date(task.started_at || task.created_at).getTime()) /
                            1000
                        )}s`
                      : task.started_at
                      ? `${Math.round(
                          (Date.now() - new Date(task.started_at).getTime()) / 1000
                        )}s`
                      : '-'}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="View details">
                      <IconButton
                        size="small"
                        onClick={() => handleViewTask(task)}
                      >
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    
                    {task.status === 'pending' && (
                      <Tooltip title="Execute">
                        <IconButton
                          size="small"
                          onClick={() => handleExecuteTask(task.id)}
                          color="primary"
                        >
                          <PlayArrow />
                        </IconButton>
                      </Tooltip>
                    )}
                    
                    {task.status === 'running' && (
                      <>
                        <Tooltip title="Pause">
                          <IconButton
                            size="small"
                            onClick={() => handlePauseTask(task.id)}
                            color="warning"
                          >
                            <Pause />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Stop">
                          <IconButton
                            size="small"
                            onClick={() => handleStopTask(task.id)}
                            color="error"
                          >
                            <Stop />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                    
                    {['completed', 'failed', 'paused'].includes(task.status) && (
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteTask(task.id)}
                          color="error"
                        >
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {tasks.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No tasks found. Create your first task to get started!
        </Alert>
      )}

      {/* Create Task Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Task</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Task Description"
            fullWidth
            multiline
            rows={3}
            value={newTask.description}
            onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
            placeholder="Describe the task you want the AI agent to perform..."
          />
          
          <FormControl fullWidth margin="normal">
            <InputLabel>AI Agent (Optional)</InputLabel>
            <Select
              value={newTask.agent_id}
              label="AI Agent (Optional)"
              onChange={(e: SelectChangeEvent) =>
                setNewTask({ ...newTask, agent_id: e.target.value })
              }
            >
              <MenuItem value="">
                <em>Auto-select best agent</em>
              </MenuItem>
              {agents.map((agent) => (
                <MenuItem key={agent.id} value={agent.id}>
                  {agent.name} ({agent.provider}) - {agent.status}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateTask}
            variant="contained"
            disabled={!newTask.description.trim()}
          >
            Create Task
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Task Dialog */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Task Details
          {selectedTask && (
            <Chip
              icon={getStatusIcon(selectedTask.status)}
              label={selectedTask.status}
              color={getStatusColor(selectedTask.status) as any}
              size="small"
              sx={{ ml: 2 }}
            />
          )}
        </DialogTitle>
        <DialogContent>
          {selectedTask && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Description
              </Typography>
              <Typography variant="body1" paragraph>
                {selectedTask.description}
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body2">
                    {formatDate(selectedTask.created_at)}
                  </Typography>
                </Grid>
                {selectedTask.started_at && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Started
                    </Typography>
                    <Typography variant="body2">
                      {formatDate(selectedTask.started_at)}
                    </Typography>
                  </Grid>
                )}
                {selectedTask.completed_at && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Completed
                    </Typography>
                    <Typography variant="body2">
                      {formatDate(selectedTask.completed_at)}
                    </Typography>
                  </Grid>
                )}
                {selectedTask.agent_name && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Agent
                    </Typography>
                    <Typography variant="body2">
                      {selectedTask.agent_name}
                    </Typography>
                  </Grid>
                )}
              </Grid>

              {selectedTask.result && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Result
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {selectedTask.result.message}
                    </Typography>
                    
                    {selectedTask.result.suggestions && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Suggestions:
                        </Typography>
                        {selectedTask.result.suggestions.map((suggestion, index) => (
                          <Typography key={index} variant="body2" sx={{ ml: 1 }}>
                            • {suggestion}
                          </Typography>
                        ))}
                      </Box>
                    )}
                  </Paper>
                </Box>
              )}

              {selectedTask.error && (
                <Box sx={{ mt: 3 }}>
                  <Alert severity="error">
                    <Typography variant="body2">
                      {selectedTask.error}
                    </Typography>
                  </Alert>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          {selectedTask && selectedTask.status === 'pending' && (
            <Button
              onClick={() => {
                handleExecuteTask(selectedTask.id);
                setViewDialogOpen(false);
              }}
              variant="contained"
              startIcon={<PlayArrow />}
            >
              Execute Task
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}