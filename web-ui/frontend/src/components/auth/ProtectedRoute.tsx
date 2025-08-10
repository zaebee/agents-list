// Protected route components for role-based and subscription-based access control

import React from 'react';
import { useAuth, useSubscription, useRole } from '../../contexts/AuthContext';
import { Navigate, useLocation } from 'react-router-dom';
import { AlertCircle, Lock, Crown } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requiredRole?: 'user' | 'manager' | 'admin';
  requiredSubscription?: 'free' | 'pro' | 'enterprise';
  requireVerification?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAuth = true,
  requiredRole,
  requiredSubscription,
  requireVerification = false,
}) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const { subscriptionTier, hasProOrHigher, hasEnterpriseOnly } = useSubscription();
  const { role, hasManagerAccess, hasAdminAccess } = useRole();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Check authentication requirement
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check email verification requirement
  if (requireVerification && user && !user.is_verified) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-yellow-500" />
            <h2 className="mt-4 text-xl font-semibold text-gray-900">
              Email Verification Required
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Please check your email and click the verification link to access this page.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 w-full bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors"
            >
              I've verified my email
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Check role requirement
  if (requiredRole) {
    let hasRequiredRole = false;
    
    switch (requiredRole) {
      case 'admin':
        hasRequiredRole = hasAdminAccess();
        break;
      case 'manager':
        hasRequiredRole = hasManagerAccess();
        break;
      case 'user':
        hasRequiredRole = true; // All authenticated users have user role or higher
        break;
    }

    if (!hasRequiredRole) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="text-center">
              <Lock className="mx-auto h-12 w-12 text-red-500" />
              <h2 className="mt-4 text-xl font-semibold text-gray-900">
                Access Denied
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                You need {requiredRole} privileges to access this page.
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Your current role: {role}
              </p>
            </div>
          </div>
        </div>
      );
    }
  }

  // Check subscription requirement
  if (requiredSubscription) {
    let hasRequiredSubscription = false;
    
    switch (requiredSubscription) {
      case 'enterprise':
        hasRequiredSubscription = hasEnterpriseOnly();
        break;
      case 'pro':
        hasRequiredSubscription = hasProOrHigher();
        break;
      case 'free':
        hasRequiredSubscription = true; // All users have free or higher
        break;
    }

    if (!hasRequiredSubscription) {
      return <SubscriptionUpgradePrompt requiredTier={requiredSubscription} currentTier={subscriptionTier} />;
    }
  }

  // All checks passed, render the protected content
  return <>{children}</>;
};

// Component for subscription upgrade prompts
interface SubscriptionUpgradePromptProps {
  requiredTier: string;
  currentTier?: string;
}

const SubscriptionUpgradePrompt: React.FC<SubscriptionUpgradePromptProps> = ({
  requiredTier,
  currentTier = 'free',
}) => {
  const getPricingInfo = (tier: string) => {
    switch (tier) {
      case 'pro':
        return { price: '$49', features: ['Unlimited tasks', 'Advanced AI agents', 'Analytics dashboard', 'API access'] };
      case 'enterprise':
        return { price: 'Custom', features: ['All Pro features', 'Custom agents', 'SSO integration', 'Dedicated support'] };
      default:
        return { price: '$0', features: [] };
    }
  };

  const pricing = getPricingInfo(requiredTier);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-lg w-full bg-white shadow-xl rounded-lg p-8">
        <div className="text-center">
          <Crown className="mx-auto h-16 w-16 text-yellow-500" />
          <h2 className="mt-6 text-2xl font-bold text-gray-900">
            Upgrade Required
          </h2>
          <p className="mt-4 text-gray-600">
            You need a <span className="font-semibold text-indigo-600">{requiredTier.toUpperCase()}</span> subscription 
            to access this feature.
          </p>
          
          <div className="mt-6 bg-gray-50 rounded-lg p-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-indigo-600">{pricing.price}</div>
              <div className="text-sm text-gray-500">per user/month</div>
            </div>
            
            {pricing.features.length > 0 && (
              <ul className="mt-4 space-y-2 text-sm text-gray-600">
                {pricing.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <svg className="h-4 w-4 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="mt-6 space-y-3">
            <button
              onClick={() => window.open('/pricing', '_blank')}
              className="w-full bg-indigo-600 text-white px-6 py-3 rounded-md font-medium hover:bg-indigo-700 transition-colors"
            >
              Upgrade to {requiredTier.toUpperCase()}
            </button>
            
            <button
              onClick={() => window.history.back()}
              className="w-full bg-gray-200 text-gray-800 px-6 py-3 rounded-md font-medium hover:bg-gray-300 transition-colors"
            >
              Go Back
            </button>
          </div>

          <p className="mt-4 text-xs text-gray-500">
            Current plan: {currentTier.toUpperCase()}
          </p>
        </div>
      </div>
    </div>
  );
};

// Specific protected route components for common use cases
export const AdminOnlyRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requiredRole="admin" requireVerification>
    {children}
  </ProtectedRoute>
);

export const ManagerRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requiredRole="manager" requireVerification>
    {children}
  </ProtectedRoute>
);

export const ProRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requiredSubscription="pro" requireVerification>
    {children}
  </ProtectedRoute>
);

export const EnterpriseRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requiredSubscription="enterprise" requireVerification>
    {children}
  </ProtectedRoute>
);

export const VerifiedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requireVerification>
    {children}
  </ProtectedRoute>
);

// Hook for checking permissions in components
export const usePermissions = () => {
  const { user } = useAuth();
  const { subscriptionTier, hasProOrHigher, hasEnterpriseOnly } = useSubscription();
  const { role, hasManagerAccess, hasAdminAccess } = useRole();

  const canAccessFeature = (feature: {
    requireRole?: 'user' | 'manager' | 'admin';
    requireSubscription?: 'free' | 'pro' | 'enterprise';
    requireVerification?: boolean;
  }) => {
    // Check verification
    if (feature.requireVerification && (!user || !user.is_verified)) {
      return false;
    }

    // Check role
    if (feature.requireRole) {
      switch (feature.requireRole) {
        case 'admin':
          if (!hasAdminAccess()) return false;
          break;
        case 'manager':
          if (!hasManagerAccess()) return false;
          break;
      }
    }

    // Check subscription
    if (feature.requireSubscription) {
      switch (feature.requireSubscription) {
        case 'enterprise':
          if (!hasEnterpriseOnly()) return false;
          break;
        case 'pro':
          if (!hasProOrHigher()) return false;
          break;
      }
    }

    return true;
  };

  return {
    canAccessFeature,
    user,
    role,
    subscriptionTier,
    hasManagerAccess,
    hasAdminAccess,
    hasProOrHigher,
    hasEnterpriseOnly,
  };
};