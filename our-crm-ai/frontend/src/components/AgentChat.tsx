import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
  Divider,
  Card,
  CardContent,
  Grid,
  Alert,
  IconButton,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import {
  Send,
  SmartToy,
  Person,
  ContentCopy,
  Refresh,
  Psychology,
  Speed,
  Stars,
} from '@mui/icons-material';
import { ApiService, Agent, AgentAnalysis, TaskExecution } from '../services/ApiService';

interface Message {
  id: string;
  type: 'user' | 'agent' | 'system';
  content: string;
  timestamp: Date;
  agent?: Agent;
  taskId?: string;
}

export default function AgentChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      type: 'system',
      content: 'Welcome to AI Agent Chat! Describe your task and I\'ll connect you with the best AI agent.',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [analysisMode, setAnalysisMode] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadAgents();
    scrollToBottom();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadAgents = async () => {
    try {
      const response = await ApiService.get('/api/agents');
      setAgents(response.data.agents || []);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      if (analysisMode) {
        // Get agent recommendation
        const analysisResponse = await ApiService.post<AgentAnalysis>('/api/agents/analyze', {
          task_description: input,
        });

        const analysis = analysisResponse.data;
        const systemMessage: Message = {
          id: Date.now().toString() + '_analysis',
          type: 'system',
          content: `**Recommended Agent:** ${analysis.suggested_agent.name} (${(analysis.suggested_agent.confidence * 100).toFixed(0)}% confidence)

**Reasoning:** ${analysis.suggested_agent.reasoning}

Would you like to proceed with this agent or select a different one?`,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, systemMessage]);
        setSelectedAgent(analysis.suggested_agent.id);
      } else if (selectedAgent) {
        // Execute task with selected agent
        const agent = agents.find((a) => a.id === selectedAgent);
        const taskResponse = await ApiService.post<TaskExecution>('/api/agents/execute', {
          agent_id: selectedAgent,
          task: input,
        });

        const task = taskResponse.data;
        const agentMessage: Message = {
          id: Date.now().toString() + '_response',
          type: 'agent',
          content: task.result?.message || 'Task completed successfully.',
          timestamp: new Date(),
          agent,
          taskId: task.task_id,
        };

        setMessages((prev) => [...prev, agentMessage]);

        if (task.result?.suggestions?.length) {
          const suggestionsMessage: Message = {
            id: Date.now().toString() + '_suggestions',
            type: 'system',
            content: `**Suggestions:**\n${task.result.suggestions.map((s) => `• ${s}`).join('\n')}`,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, suggestionsMessage]);
        }
      }
    } catch (error: any) {
      const errorMessage: Message = {
        id: Date.now().toString() + '_error',
        type: 'system',
        content: `Error: ${error.response?.data?.error || 'Failed to process request'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleAgentSelect = (event: SelectChangeEvent) => {
    setSelectedAgent(event.target.value);
    setAnalysisMode(false);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const resetChat = () => {
    setMessages([
      {
        id: 'welcome',
        type: 'system',
        content: 'Welcome to AI Agent Chat! Describe your task and I\'ll connect you with the best AI agent.',
        timestamp: new Date(),
      },
    ]);
    setSelectedAgent('');
    setAnalysisMode(true);
  };

  const getMessageIcon = (message: Message) => {
    switch (message.type) {
      case 'user':
        return <Person sx={{ color: 'primary.main' }} />;
      case 'agent':
        return <SmartToy sx={{ color: 'secondary.main' }} />;
      case 'system':
        return <Psychology sx={{ color: 'info.main' }} />;
      default:
        return <SmartToy />;
    }
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Box sx={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      {/* Chat Header */}
      <Paper sx={{ p: 2, mb: 2, bgcolor: 'rgba(102, 126, 234, 0.05)' }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Select AI Agent</InputLabel>
              <Select
                value={selectedAgent}
                label="Select AI Agent"
                onChange={handleAgentSelect}
                disabled={loading}
              >
                <MenuItem value="">
                  <em>Auto-recommend based on task</em>
                </MenuItem>
                {agents.map((agent) => (
                  <MenuItem key={agent.id} value={agent.id}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        size="small"
                        label={agent.status}
                        color={agent.status === 'available' ? 'success' : 'default'}
                      />
                      {agent.name} ({agent.provider})
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Tooltip title="Refresh agents">
                <IconButton onClick={loadAgents} disabled={loading}>
                  <Refresh />
                </IconButton>
              </Tooltip>
              <Tooltip title="Clear chat">
                <IconButton onClick={resetChat} disabled={loading}>
                  <Psychology />
                </IconButton>
              </Tooltip>
            </Box>
          </Grid>
        </Grid>

        {selectedAgent && (
          <Box sx={{ mt: 2 }}>
            <Alert severity="info" icon={<SmartToy />}>
              <strong>Active Agent:</strong> {agents.find((a) => a.id === selectedAgent)?.name} - 
              {agents.find((a) => a.id === selectedAgent)?.description}
            </Alert>
          </Box>
        )}
      </Paper>

      {/* Messages Area */}
      <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          <List sx={{ width: '100%' }}>
            {messages.map((message, index) => (
              <React.Fragment key={message.id}>
                <ListItem sx={{ alignItems: 'flex-start', px: 0 }}>
                  <Avatar sx={{ mr: 2, mt: 1 }}>
                    {getMessageIcon(message)}
                  </Avatar>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                        {message.type === 'user' ? 'You' : 
                         message.type === 'agent' ? message.agent?.name || 'AI Agent' : 'System'}
                      </Typography>
                      {message.agent && (
                        <Chip
                          size="small"
                          label={message.agent.provider}
                          sx={{ ml: 1 }}
                          color="primary"
                        />
                      )}
                      <Typography variant="caption" sx={{ ml: 'auto', color: 'text.secondary' }}>
                        {formatTimestamp(message.timestamp)}
                      </Typography>
                    </Box>
                    
                    <Card variant="outlined" sx={{ bgcolor: 'background.paper' }}>
                      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            whiteSpace: 'pre-line',
                            '& strong': { fontWeight: 600 }
                          }}
                          dangerouslySetInnerHTML={{
                            __html: message.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          }}
                        />
                        
                        {message.taskId && (
                          <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                            <Chip
                              icon={<Speed />}
                              label={`Task ID: ${message.taskId}`}
                              size="small"
                              variant="outlined"
                            />
                            <IconButton
                              size="small"
                              onClick={() => copyToClipboard(message.content)}
                              title="Copy response"
                            >
                              <ContentCopy fontSize="small" />
                            </IconButton>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </Box>
                </ListItem>
                {index < messages.length - 1 && <Divider sx={{ my: 1 }} />}
              </React.Fragment>
            ))}
            {loading && (
              <ListItem sx={{ justifyContent: 'center' }}>
                <CircularProgress size={24} />
                <Typography variant="body2" sx={{ ml: 2 }}>
                  {analysisMode ? 'Analyzing task and selecting agent...' : 'Processing your request...'}
                </Typography>
              </ListItem>
            )}
          </List>
          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <Divider />
        <Box sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              placeholder={
                analysisMode 
                  ? "Describe your task (e.g., 'Analyze this business report', 'Write a marketing email', 'Debug this code')"
                  : selectedAgent 
                    ? "Continue your conversation with the AI agent..."
                    : "Select an agent or describe your task..."
              }
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              variant="outlined"
              size="small"
            />
            <Button
              variant="contained"
              onClick={handleSendMessage}
              disabled={!input.trim() || loading}
              sx={{ minWidth: 'auto', px: 2 }}
            >
              <Send />
            </Button>
          </Box>
          <Typography variant="caption" sx={{ color: 'text.secondary', mt: 1, display: 'block' }}>
            Press Ctrl+Enter for new line • Enter to send
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
}