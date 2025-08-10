// Notification settings component for managing user preferences

import React, { useState, useEffect } from 'react';
import { Bell, BellOff, Volume2, VolumeX, TestTube, X, Settings, Check } from 'lucide-react';
import notificationService from '../services/notifications';
import { NotificationPreferences } from '../types';

interface NotificationSettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

const NotificationSettings: React.FC<NotificationSettingsProps> = ({ isOpen, onClose }) => {
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    enabled: true,
    taskAssigned: true,
    taskCompleted: true,
    taskMoved: false,
    taskCreated: false,
    soundEnabled: true,
  });
  
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [isLoading, setIsLoading] = useState(false);
  const [testingNotification, setTestingNotification] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Load current preferences
      const currentPrefs = notificationService.getPreferences();
      setPreferences(currentPrefs);
      
      // Get current permission status
      if (notificationService.isSupported()) {
        setPermission(Notification.permission);
      }
    }
  }, [isOpen]);

  const handlePreferenceChange = (key: keyof NotificationPreferences, value: boolean) => {
    const newPreferences = { ...preferences, [key]: value };
    setPreferences(newPreferences);
    notificationService.updatePreferences({ [key]: value });
  };

  const handleRequestPermission = async () => {
    setIsLoading(true);
    try {
      const newPermission = await notificationService.requestPermission();
      setPermission(newPermission);
      
      if (newPermission === 'granted') {
        handlePreferenceChange('enabled', true);
        await handleTestNotification();
      }
    } catch (error) {
      console.error('Failed to request notification permission:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestNotification = async () => {
    if (!notificationService.isEnabled()) return;
    
    setTestingNotification(true);
    try {
      await notificationService.testNotification();
      setTimeout(() => setTestingNotification(false), 2000);
    } catch (error) {
      console.error('Failed to send test notification:', error);
      setTestingNotification(false);
    }
  };

  if (!isOpen) return null;

  const isNotificationSupported = notificationService.isSupported();
  const isPermissionGranted = permission === 'granted';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <Settings className="text-blue-600" size={24} />
            <h2 className="text-lg font-semibold text-gray-900">Notification Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Browser Support Check */}
          {!isNotificationSupported && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <BellOff className="text-yellow-600" size={20} />
                <div>
                  <h3 className="font-medium text-yellow-800">
                    Notifications Not Supported
                  </h3>
                  <p className="text-sm text-yellow-700 mt-1">
                    Your browser doesn't support notifications. Please use a modern browser for the best experience.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Permission Request */}
          {isNotificationSupported && !isPermissionGranted && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Bell className="text-blue-600" size={20} />
                  <div>
                    <h3 className="font-medium text-blue-800">
                      Enable Browser Notifications
                    </h3>
                    <p className="text-sm text-blue-700 mt-1">
                      {permission === 'denied' 
                        ? 'Notifications are blocked. Please enable them in your browser settings.'
                        : 'Allow notifications to receive real-time updates about your tasks.'
                      }
                    </p>
                  </div>
                </div>
                {permission !== 'denied' && (
                  <button
                    onClick={handleRequestPermission}
                    disabled={isLoading}
                    className="px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {isLoading ? 'Requesting...' : 'Enable'}
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Permission Granted */}
          {isPermissionGranted && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <Check className="text-green-600" size={20} />
                <div>
                  <h3 className="font-medium text-green-800">
                    Notifications Enabled
                  </h3>
                  <p className="text-sm text-green-700 mt-1">
                    You'll receive browser notifications for task updates.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Main Settings */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">Notification Preferences</h3>
            
            {/* Master Toggle */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {preferences.enabled ? (
                  <Bell className="text-blue-600" size={20} />
                ) : (
                  <BellOff className="text-gray-400" size={20} />
                )}
                <div>
                  <div className="font-medium text-gray-900">
                    Enable Notifications
                  </div>
                  <div className="text-sm text-gray-600">
                    Master switch for all notifications
                  </div>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={preferences.enabled}
                  onChange={(e) => handlePreferenceChange('enabled', e.target.checked)}
                  disabled={!isPermissionGranted}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {/* Individual Settings */}
            <div className="space-y-3">
              {[
                { key: 'taskAssigned' as const, label: 'Task Assignments', desc: 'When a task is assigned to you or someone else' },
                { key: 'taskCompleted' as const, label: 'Task Completions', desc: 'When tasks are marked as completed' },
                { key: 'taskMoved' as const, label: 'Task Movements', desc: 'When tasks are moved between columns' },
                { key: 'taskCreated' as const, label: 'New Tasks', desc: 'When new tasks are created' }
              ].map((setting) => (
                <div key={setting.key} className="flex items-center justify-between py-2">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">
                      {setting.label}
                    </div>
                    <div className="text-sm text-gray-600">
                      {setting.desc}
                    </div>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer ml-4">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={preferences[setting.key]}
                      onChange={(e) => handlePreferenceChange(setting.key, e.target.checked)}
                      disabled={!preferences.enabled || !isPermissionGranted}
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50"></div>
                  </label>
                </div>
              ))}
            </div>

            {/* Sound Settings */}
            <div className="flex items-center justify-between py-2 border-t pt-4">
              <div className="flex items-center space-x-3">
                {preferences.soundEnabled ? (
                  <Volume2 className="text-blue-600" size={20} />
                ) : (
                  <VolumeX className="text-gray-400" size={20} />
                )}
                <div>
                  <div className="font-medium text-gray-900">
                    Sound Alerts
                  </div>
                  <div className="text-sm text-gray-600">
                    Play sound when notifications appear
                  </div>
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={preferences.soundEnabled}
                  onChange={(e) => handlePreferenceChange('soundEnabled', e.target.checked)}
                  disabled={!preferences.enabled || !isPermissionGranted}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50"></div>
              </label>
            </div>

            {/* Test Notification */}
            {isPermissionGranted && preferences.enabled && (
              <div className="pt-4 border-t">
                <button
                  onClick={handleTestNotification}
                  disabled={testingNotification}
                  className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50"
                >
                  {testingNotification ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-400 border-t-transparent"></div>
                      <span>Sending Test...</span>
                    </>
                  ) : (
                    <>
                      <TestTube size={16} />
                      <span>Send Test Notification</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationSettings;