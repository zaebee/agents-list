// Browser notification service for task updates

import { Task, ColumnName } from '../types';

export interface NotificationOptions {
  title: string;
  body: string;
  icon?: string;
  tag?: string;
  requireInteraction?: boolean;
  actions?: NotificationAction[];
}

export interface NotificationPreferences {
  enabled: boolean;
  taskAssigned: boolean;
  taskCompleted: boolean;
  taskMoved: boolean;
  taskCreated: boolean;
  soundEnabled: boolean;
}

const DEFAULT_PREFERENCES: NotificationPreferences = {
  enabled: true,
  taskAssigned: true,
  taskCompleted: true,
  taskMoved: false,
  taskCreated: false,
  soundEnabled: true,
};

class NotificationService {
  private permission: NotificationPermission = 'default';
  private preferences: NotificationPreferences;
  private activeNotifications: Map<string, Notification> = new Map();

  constructor() {
    this.permission = this.getPermission();
    this.preferences = this.loadPreferences();
    
    // Listen for permission changes
    if ('permissions' in navigator) {
      navigator.permissions.query({ name: 'notifications' }).then(permission => {
        permission.addEventListener('change', () => {
          this.permission = this.getPermission();
        });
      });
    }
  }

  // Get current notification permission
  private getPermission(): NotificationPermission {
    return Notification?.permission || 'default';
  }

  // Request notification permission
  async requestPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      console.warn('Browser does not support notifications');
      return 'denied';
    }

    if (this.permission === 'granted') {
      return 'granted';
    }

    try {
      this.permission = await Notification.requestPermission();
      return this.permission;
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return 'denied';
    }
  }

  // Check if notifications are supported and permitted
  isSupported(): boolean {
    return 'Notification' in window;
  }

  isEnabled(): boolean {
    return this.isSupported() && 
           this.permission === 'granted' && 
           this.preferences.enabled;
  }

  // Load user preferences from localStorage
  private loadPreferences(): NotificationPreferences {
    try {
      const stored = localStorage.getItem('notification_preferences');
      if (stored) {
        return { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) };
      }
    } catch (error) {
      console.error('Error loading notification preferences:', error);
    }
    return { ...DEFAULT_PREFERENCES };
  }

  // Save user preferences to localStorage
  private savePreferences(): void {
    try {
      localStorage.setItem('notification_preferences', JSON.stringify(this.preferences));
    } catch (error) {
      console.error('Error saving notification preferences:', error);
    }
  }

  // Update preferences
  updatePreferences(updates: Partial<NotificationPreferences>): void {
    this.preferences = { ...this.preferences, ...updates };
    this.savePreferences();
  }

  // Get current preferences
  getPreferences(): NotificationPreferences {
    return { ...this.preferences };
  }

  // Show a notification
  private async showNotification(options: NotificationOptions): Promise<Notification | null> {
    if (!this.isEnabled()) {
      return null;
    }

    try {
      // Close existing notification with same tag
      if (options.tag && this.activeNotifications.has(options.tag)) {
        this.activeNotifications.get(options.tag)?.close();
      }

      const notification = new Notification(options.title, {
        body: options.body,
        icon: options.icon || '/favicon.ico',
        tag: options.tag,
        requireInteraction: options.requireInteraction || false,
        badge: '/favicon.ico',
        timestamp: Date.now()
      });

      // Store active notification
      if (options.tag) {
        this.activeNotifications.set(options.tag, notification);
      }

      // Auto-close after 5 seconds unless requireInteraction is true
      if (!options.requireInteraction) {
        setTimeout(() => {
          notification.close();
          if (options.tag) {
            this.activeNotifications.delete(options.tag);
          }
        }, 5000);
      }

      // Handle notification click
      notification.onclick = () => {
        window.focus();
        notification.close();
        if (options.tag) {
          this.activeNotifications.delete(options.tag);
        }
      };

      // Handle notification close
      notification.onclose = () => {
        if (options.tag) {
          this.activeNotifications.delete(options.tag);
        }
      };

      // Play sound if enabled
      if (this.preferences.soundEnabled) {
        this.playNotificationSound();
      }

      return notification;
    } catch (error) {
      console.error('Error showing notification:', error);
      return null;
    }
  }

  // Play notification sound
  private playNotificationSound(): void {
    try {
      // Create and play a subtle notification sound
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
      
      gainNode.gain.setValueAtTime(0, audioContext.currentTime);
      gainNode.gain.linearRampToValueAtTime(0.1, audioContext.currentTime + 0.05);
      gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.2);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch (error) {
      // Silently fail if sound cannot be played
      console.debug('Could not play notification sound:', error);
    }
  }

  // Task-specific notification methods
  async notifyTaskAssigned(task: Task, assignedTo: string): Promise<void> {
    if (!this.preferences.taskAssigned) return;

    await this.showNotification({
      title: 'Task Assigned',
      body: `"${task.title}" has been assigned to ${assignedTo}`,
      tag: `task-assigned-${task.id}`,
      icon: '/favicon.ico'
    });
  }

  async notifyTaskCompleted(task: Task): Promise<void> {
    if (!this.preferences.taskCompleted) return;

    await this.showNotification({
      title: 'Task Completed!',
      body: `"${task.title}" has been completed`,
      tag: `task-completed-${task.id}`,
      icon: '/favicon.ico'
    });
  }

  async notifyTaskMoved(task: Task, fromColumn: ColumnName, toColumn: ColumnName): Promise<void> {
    if (!this.preferences.taskMoved) return;

    await this.showNotification({
      title: 'Task Moved',
      body: `"${task.title}" moved from ${fromColumn} to ${toColumn}`,
      tag: `task-moved-${task.id}`,
      icon: '/favicon.ico'
    });
  }

  async notifyTaskCreated(task: Task): Promise<void> {
    if (!this.preferences.taskCreated) return;

    await this.showNotification({
      title: 'New Task Created',
      body: `"${task.title}" has been added to your board`,
      tag: `task-created-${task.id}`,
      icon: '/favicon.ico'
    });
  }

  // Clear all active notifications
  clearAll(): void {
    this.activeNotifications.forEach(notification => {
      notification.close();
    });
    this.activeNotifications.clear();
  }

  // Clear notifications for specific task
  clearTaskNotifications(taskId: string): void {
    const tagsToRemove = Array.from(this.activeNotifications.keys())
      .filter(tag => tag.includes(taskId));
    
    tagsToRemove.forEach(tag => {
      this.activeNotifications.get(tag)?.close();
      this.activeNotifications.delete(tag);
    });
  }

  // Test notification (for settings)
  async testNotification(): Promise<void> {
    await this.showNotification({
      title: 'Test Notification',
      body: 'This is a test notification from AI-CRM',
      tag: 'test-notification',
      requireInteraction: false
    });
  }
}

// Create singleton instance
export const notificationService = new NotificationService();

export default notificationService;