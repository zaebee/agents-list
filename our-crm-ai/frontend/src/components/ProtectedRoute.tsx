import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: string;
}

export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const location = useLocation();
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center gradient-primary">
        <div className="text-center text-white">
          <div className="loading-spinner w-12 h-12 mx-auto mb-4"></div>
          <p className="text-lg font-medium">Loading AI Project Manager...</p>
        </div>
      </div>
    );
  }
  
  if (!user) {
    // Redirect to login with return url
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    // Redirect to unauthorized page or dashboard
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}