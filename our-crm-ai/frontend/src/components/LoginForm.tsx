import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  InputAdornment,
  IconButton,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Login as LoginIcon,
} from '@mui/icons-material';

interface LoginFormProps {
  onLogin: (username: string, password: string) => Promise<void>;
  loading: boolean;
}

export default function LoginForm({ onLogin, loading }: LoginFormProps) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!username || !password) {
      setError('Please enter both username and password');
      return;
    }

    try {
      await onLogin(username, password);
    } catch (error: any) {
      setError(error.response?.data?.error || 'Login failed');
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Box component=\"form\" onSubmit={handleSubmit} noValidate>
      {error && (
        <Alert severity=\"error\" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TextField
        margin=\"normal\"
        required
        fullWidth
        id=\"username\"
        label=\"Username\"
        name=\"username\"
        autoComplete=\"username\"
        autoFocus
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        disabled={loading}
        variant=\"outlined\"
        sx={{ mb: 2 }}
      />

      <TextField
        margin=\"normal\"
        required
        fullWidth
        name=\"password\"
        label=\"Password\"
        type={showPassword ? 'text' : 'password'}
        id=\"password\"
        autoComplete=\"current-password\"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        disabled={loading}
        variant=\"outlined\"
        sx={{ mb: 3 }}
        InputProps={{
          endAdornment: (
            <InputAdornment position=\"end\">
              <IconButton
                aria-label=\"toggle password visibility\"
                onClick={togglePasswordVisibility}
                edge=\"end\"
              >
                {showPassword ? <VisibilityOff /> : <Visibility />}
              </IconButton>
            </InputAdornment>
          ),
        }}
      />

      <Button
        type=\"submit\"
        fullWidth
        variant=\"contained\"
        size=\"large\"
        disabled={loading}
        sx={{ py: 1.5, mb: 2 }}
        startIcon={<LoginIcon />}
      >
        {loading ? 'Signing In...' : 'Sign In'}
      </Button>

      <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(0,0,0,0.05)', borderRadius: 1 }}>
        <Typography variant=\"caption\" display=\"block\" gutterBottom>
          <strong>Demo Credentials:</strong>
        </Typography>
        <Typography variant=\"caption\" color=\"textSecondary\">
          Username: admin<br />
          Password: admin123
        </Typography>
      </Box>

      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant=\"caption\" color=\"textSecondary\">
          🔐 Secure JWT Authentication<br />
          🤖 Real AI Agents Ready<br />
          📊 Production Dashboard
        </Typography>
      </Box>
    </Box>
  );
}