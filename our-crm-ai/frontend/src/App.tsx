import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';

// Context Providers
import { AuthProvider } from './contexts/AuthContext';
import { AgentProvider } from './contexts/AgentContext';

// Components
import LoginForm from './components/LoginForm';
import Dashboard from './components/Dashboard';
import AgentChat from './components/AgentChat';
import AgentDashboard from './components/AgentDashboard';
import TaskManager from './components/TaskManager';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

// Styles
import './index.css';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  return (
    <AuthProvider>
      <AgentProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginForm />} />
            <Route path="/" element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/agents" element={
              <ProtectedRoute>
                <Layout>
                  <AgentDashboard />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/chat" element={
              <ProtectedRoute>
                <Layout>
                  <AgentChat />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/tasks" element={
              <ProtectedRoute>
                <Layout>
                  <TaskManager />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            className="font-sans"
          />
        </Router>
      </AgentProvider>
    </AuthProvider>
  );
}

export default App;
