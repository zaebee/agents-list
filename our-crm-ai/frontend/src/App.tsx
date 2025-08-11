import React, { useEffect, useState } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Container,
  Box,
  Typography,
  Paper,
  Alert,
  CircularProgress
} from '@mui/material';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Components
import LoginForm from './components/LoginForm';
import Dashboard from './components/Dashboard';
import AgentChat from './components/AgentChat';
import AgentDashboard from './components/AgentDashboard';
import TaskManager from './components/TaskManager';

// Services
import { AuthService } from './services/AuthService';
import { ApiService } from './services/ApiService';

// Types
interface User {
  username: string;
  email: string;
  role: string;
  id: string;
}

// Theme configuration
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#667eea',
      light: '#8fa5f3',
      dark: '#4c63d2',
    },
    secondary: {
      main: '#764ba2',
      light: '#9575cd',
      dark: '#512e5f',
    },
    background: {
      default: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      paper: 'rgba(255, 255, 255, 0.95)',
    },
  },
  typography: {
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem',
    },
    h2: {
      fontWeight: 600,
      fontSize: '2rem',
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.5rem',
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          borderRadius: '15px',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
  },
});

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = AuthService.getToken();
      if (token) {
        // Verify token is still valid
        const response = await ApiService.get('/api/auth/verify');
        if (response.data) {
          setUser(response.data.user);
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      AuthService.logout();
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (username: string, password: string) => {
    try {
      setError(null);
      setLoading(true);
      
      const response = await ApiService.post('/api/auth/login', {
        username,
        password
      });

      const { token, user: userData } = response.data;
      AuthService.setToken(token);
      setUser(userData);
    } catch (error: any) {
      setError(error.response?.data?.error || 'Login failed');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    AuthService.logout();
    setUser(null);
  };

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          display=\"flex\"
          justifyContent=\"center\"
          alignItems=\"center\"
          minHeight=\"100vh\"
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          }}
        >
          <Box textAlign=\"center\" color=\"white\">
            <CircularProgress size={60} color=\"inherit\" sx={{ mb: 2 }} />
            <Typography variant=\"h6\">Loading AI Project Manager...</Typography>
          </Box>
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        <Router>
          <Container maxWidth=\"xl\" sx={{ py: 3 }}>
            {error && (
              <Alert severity=\"error\" sx={{ mb: 2 }} onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            {!user ? (
              <Paper
                elevation={0}
                sx={{
                  p: 4,
                  maxWidth: 400,
                  mx: 'auto',
                  mt: 8,
                  background: 'rgba(255, 255, 255, 0.95)',
                }}
              >
                <Box textAlign=\"center\" mb={3}>
                  <Typography variant=\"h1\" component=\"h1\" gutterBottom>
                    🤖 AI PM
                  </Typography>
                  <Typography variant=\"h6\" color=\"textSecondary\">
                    AI Project Manager
                  </Typography>
                </Box>
                <LoginForm onLogin={handleLogin} loading={loading} />
              </Paper>
            ) : (
              <Routes>
                <Route path=\"/\" element={<Dashboard user={user} onLogout={handleLogout} />} />
                <Route path=\"/agents\" element={<AgentDashboard user={user} />} />
                <Route path=\"/chat\" element={<AgentChat user={user} />} />
                <Route path=\"/tasks\" element={<TaskManager user={user} />} />
                <Route path=\"*\" element={<Navigate to=\"/\" replace />} />
              </Routes>
            )}
          </Container>
        </Router>
      </Box>
    </ThemeProvider>
  );
}

export default App;