/**
 * Authentication Service
 * Handles JWT token management and authentication state
 */

const TOKEN_KEY = 'ai_pm_token';

export class AuthService {
  /**
   * Get stored JWT token
   */
  static getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  /**
   * Store JWT token
   */
  static setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  }

  /**
   * Remove JWT token (logout)
   */
  static logout(): void {
    localStorage.removeItem(TOKEN_KEY);
  }

  /**
   * Check if user is authenticated
   */
  static isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;

    try {
      // Basic JWT structure check
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      
      // Check if token is expired
      return payload.exp > currentTime;
    } catch {
      return false;
    }
  }

  /**
   * Get user info from JWT token
   */
  static getUserFromToken(): any {
    const token = this.getToken();
    if (!token) return null;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return {
        username: payload.username,
        role: payload.role,
        userId: payload.user_id
      };
    } catch {
      return null;
    }
  }

  /**
   * Get authorization header for API requests
   */
  static getAuthHeader(): { Authorization: string } | {} {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}