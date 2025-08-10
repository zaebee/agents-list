// User profile management component

import React, { useState, useEffect } from 'react';
import { useAuth, useSubscription } from '../../contexts/AuthContext';
import { authAPI } from '../../services/authAPI';
import { User, Settings, Mail, AlertCircle, CheckCircle, Shield, Clock } from 'lucide-react';
import { toast } from 'react-toastify';

interface SessionInfo {
  id: number;
  ip_address?: string;
  user_agent?: string;
  is_active: boolean;
  created_at: string;
  last_used: string;
  expires_at: string;
}

interface MonthlyUsage {
  period: string;
  tasks_created: number;
  tasks_limit: number | null;
  subscription_tier: string;
  reset_date: string;
}

export const ProfileForm: React.FC = () => {
  const { user, updateProfile, changePassword } = useAuth();
  const { subscriptionTier, isFreeTier, isProTier, isEnterpriseTier } = useSubscription();
  const [activeTab, setActiveTab] = useState('profile');
  const [isLoading, setIsLoading] = useState(false);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [monthlyUsage, setMonthlyUsage] = useState<MonthlyUsage | null>(null);

  // Profile form state
  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
  });

  // Password form state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (user) {
      setProfileData({
        full_name: user.full_name || '',
        email: user.email,
      });
    }
  }, [user]);

  useEffect(() => {
    if (activeTab === 'sessions') {
      fetchSessions();
    }
    if (activeTab === 'usage') {
      fetchMonthlyUsage();
    }
  }, [activeTab]);

  const fetchSessions = async () => {
    try {
      const sessionsData = await authAPI.getSessions();
      setSessions(sessionsData);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      toast.error('Failed to load sessions');
    }
  };

  const fetchMonthlyUsage = async () => {
    try {
      const usageData = await authAPI.getMonthlyUsage();
      setMonthlyUsage(usageData);
    } catch (error) {
      console.error('Failed to fetch usage:', error);
      toast.error('Failed to load usage data');
    }
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors({});

    try {
      await updateProfile(profileData);
      toast.success('Profile updated successfully');
      
      if (profileData.email !== user?.email) {
        toast.info('Please check your email for verification if you changed your email address');
      }
    } catch (error: any) {
      const message = error.message || 'Profile update failed';
      setErrors({ profile: message });
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrors({});

    // Validate passwords match
    if (passwordData.new_password !== passwordData.confirm_password) {
      setErrors({ password: 'New passwords do not match' });
      setIsLoading(false);
      return;
    }

    try {
      await changePassword(passwordData.current_password, passwordData.new_password);
      toast.success('Password changed successfully');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (error: any) {
      const message = error.message || 'Password change failed';
      setErrors({ password: message });
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId: number) => {
    try {
      await authAPI.revokeSession(sessionId);
      toast.success('Session revoked successfully');
      fetchSessions(); // Refresh sessions list
    } catch (error) {
      toast.error('Failed to revoke session');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getDeviceType = (userAgent?: string) => {
    if (!userAgent) return 'Unknown Device';
    
    if (userAgent.includes('Mobile')) return 'Mobile Device';
    if (userAgent.includes('Chrome')) return 'Chrome Browser';
    if (userAgent.includes('Firefox')) return 'Firefox Browser';
    if (userAgent.includes('Safari')) return 'Safari Browser';
    return 'Desktop Browser';
  };

  const getSubscriptionBadge = () => {
    const badgeClasses = {
      free: 'bg-gray-100 text-gray-800',
      pro: 'bg-blue-100 text-blue-800',
      enterprise: 'bg-purple-100 text-purple-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeClasses[subscriptionTier || 'free']}`}>
        {subscriptionTier?.toUpperCase()}
      </span>
    );
  };

  const getUsageProgress = () => {
    if (!monthlyUsage || monthlyUsage.tasks_limit === null) return 0;
    return (monthlyUsage.tasks_created / monthlyUsage.tasks_limit) * 100;
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="h-12 w-12 bg-indigo-500 rounded-full flex items-center justify-center">
                    <User className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <h1 className="text-2xl font-bold text-gray-900">{user.username}</h1>
                    <div className="flex items-center space-x-2">
                      {getSubscriptionBadge()}
                      <span className="text-sm text-gray-500">{user.role}</span>
                      {user.is_verified ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      )}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Member since</p>
                  <p className="text-sm font-medium text-gray-900">
                    {new Date(user.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8">
                {[
                  { id: 'profile', name: 'Profile', icon: User },
                  { id: 'security', name: 'Security', icon: Shield },
                  { id: 'sessions', name: 'Sessions', icon: Settings },
                  { id: 'usage', name: 'Usage', icon: Clock },
                ].map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`${
                        activeTab === tab.id
                          ? 'border-indigo-500 text-indigo-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center`}
                    >
                      <Icon className="h-4 w-4 mr-2" />
                      {tab.name}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Tab Content */}
          <div className="mt-6 bg-white shadow rounded-lg">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Profile Information</h3>
                
                {errors.profile && (
                  <div className="mb-4 rounded-md bg-red-50 p-4">
                    <div className="flex">
                      <AlertCircle className="h-5 w-5 text-red-400" />
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-800">{errors.profile}</h3>
                      </div>
                    </div>
                  </div>
                )}

                <form onSubmit={handleProfileSubmit} className="space-y-4">
                  <div>
                    <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                      Full Name
                    </label>
                    <input
                      type="text"
                      id="full_name"
                      value={profileData.full_name}
                      onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      placeholder="Enter your full name"
                    />
                  </div>

                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                      Email Address
                    </label>
                    <div className="relative">
                      <input
                        type="email"
                        id="email"
                        value={profileData.email}
                        onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        placeholder="Enter your email address"
                      />
                      {!user.is_verified && (
                        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                          <AlertCircle className="h-5 w-5 text-yellow-500" />
                        </div>
                      )}
                    </div>
                    {!user.is_verified && (
                      <p className="mt-1 text-sm text-yellow-600">
                        Email not verified. Check your inbox for verification link.
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                      Username
                    </label>
                    <input
                      type="text"
                      id="username"
                      value={user.username}
                      disabled
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500 sm:text-sm"
                    />
                    <p className="mt-1 text-sm text-gray-500">Username cannot be changed</p>
                  </div>

                  <div className="pt-4">
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                      {isLoading ? 'Updating...' : 'Update Profile'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
              <div className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Change Password</h3>
                
                {errors.password && (
                  <div className="mb-4 rounded-md bg-red-50 p-4">
                    <div className="flex">
                      <AlertCircle className="h-5 w-5 text-red-400" />
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-800">{errors.password}</h3>
                      </div>
                    </div>
                  </div>
                )}

                <form onSubmit={handlePasswordSubmit} className="space-y-4">
                  <div>
                    <label htmlFor="current_password" className="block text-sm font-medium text-gray-700">
                      Current Password
                    </label>
                    <input
                      type="password"
                      id="current_password"
                      value={passwordData.current_password}
                      onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="new_password" className="block text-sm font-medium text-gray-700">
                      New Password
                    </label>
                    <input
                      type="password"
                      id="new_password"
                      value={passwordData.new_password}
                      onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      required
                    />
                  </div>

                  <div>
                    <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      id="confirm_password"
                      value={passwordData.confirm_password}
                      onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      required
                    />
                  </div>

                  <div className="pt-4">
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                      {isLoading ? 'Changing Password...' : 'Change Password'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Sessions Tab */}
            {activeTab === 'sessions' && (
              <div className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Active Sessions</h3>
                <div className="space-y-4">
                  {sessions.map((session) => (
                    <div
                      key={session.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                    >
                      <div>
                        <p className="font-medium text-gray-900">{getDeviceType(session.user_agent)}</p>
                        <p className="text-sm text-gray-500">IP: {session.ip_address || 'Unknown'}</p>
                        <p className="text-sm text-gray-500">
                          Last used: {formatDate(session.last_used)}
                        </p>
                      </div>
                      <button
                        onClick={() => handleRevokeSession(session.id)}
                        className="px-3 py-1 text-sm font-medium text-red-600 hover:text-red-800"
                      >
                        Revoke
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Usage Tab */}
            {activeTab === 'usage' && (
              <div className="p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Monthly Usage</h3>
                {monthlyUsage && (
                  <div className="space-y-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Tasks Created</span>
                        <span className="text-sm text-gray-500">
                          {monthlyUsage.tasks_created}
                          {monthlyUsage.tasks_limit && ` / ${monthlyUsage.tasks_limit}`}
                        </span>
                      </div>
                      {monthlyUsage.tasks_limit && (
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-indigo-600 h-2 rounded-full"
                            style={{ width: `${Math.min(getUsageProgress(), 100)}%` }}
                          ></div>
                        </div>
                      )}
                    </div>
                    
                    <div className="text-sm text-gray-500">
                      <p>Period: {monthlyUsage.period}</p>
                      <p>Subscription: {monthlyUsage.subscription_tier.toUpperCase()}</p>
                      <p>Next reset: {formatDate(monthlyUsage.reset_date)}</p>
                    </div>

                    {isFreeTier() && monthlyUsage.tasks_created >= 8 && (
                      <div className="rounded-md bg-yellow-50 p-4">
                        <div className="flex">
                          <AlertCircle className="h-5 w-5 text-yellow-400" />
                          <div className="ml-3">
                            <h3 className="text-sm font-medium text-yellow-800">
                              Approaching limit
                            </h3>
                            <p className="mt-2 text-sm text-yellow-700">
                              You're close to your monthly task limit. Consider upgrading to Pro for unlimited tasks.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};