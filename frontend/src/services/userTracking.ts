/**
 * Device Fingerprinting and User Tracking Utilities
 * Handles anonymous user identification without requiring accounts
 */

export interface DeviceInfo {
  screen: string;
  timezone: string;
  language: string;
  platform: string;
  cookieEnabled: boolean;
  onlineStatus: boolean;
  touchSupport: boolean;
  colorDepth: number;
  pixelRatio: number;
  hardwareConcurrency: number;
}

export interface UserIdentity {
  fingerprint: string;
  sessionId: string;
  deviceInfo: DeviceInfo;
}

class UserTrackingService {
  private static instance: UserTrackingService;
  private userIdentity: UserIdentity | null = null;

  static getInstance(): UserTrackingService {
    if (!UserTrackingService.instance) {
      UserTrackingService.instance = new UserTrackingService();
    }
    return UserTrackingService.instance;
  }

  /**
   * Generate device fingerprint based on browser characteristics
   */
  private async generateFingerprint(): Promise<string> {
    const components = [];

    // Screen information
    components.push(`screen:${screen.width}x${screen.height}x${screen.colorDepth}`);
    
    // Timezone
    components.push(`tz:${Intl.DateTimeFormat().resolvedOptions().timeZone}`);
    
    // Language
    components.push(`lang:${navigator.language}`);
    
    // Platform
    components.push(`platform:${navigator.platform}`);
    
    // Hardware
    components.push(`cores:${navigator.hardwareConcurrency || 'unknown'}`);
    
    // Browser features
    components.push(`cookie:${navigator.cookieEnabled}`);
    components.push(`touch:${'ontouchstart' in window}`);
    components.push(`pixelRatio:${window.devicePixelRatio || 1}`);
    
    // Canvas fingerprinting (lightweight version)
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Device fingerprint', 2, 2);
        components.push(`canvas:${canvas.toDataURL().slice(-50)}`);
      }
    } catch (e) {
      components.push('canvas:blocked');
    }

    // WebGL information (if available)
    try {
      const gl = document.createElement('canvas').getContext('webgl');
      if (gl) {
        const renderer = gl.getParameter(gl.RENDERER);
        const vendor = gl.getParameter(gl.VENDOR);
        components.push(`webgl:${vendor}-${renderer}`.slice(0, 50));
      }
    } catch (e) {
      components.push('webgl:blocked');
    }

    // Create hash from components
    const fingerprintString = components.join('|');
    return await this.hashString(fingerprintString);
  }

  /**
   * Create SHA-256 hash of string
   */
  private async hashString(str: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 32);
  }

  /**
   * Get device information
   */
  private getDeviceInfo(): DeviceInfo {
    return {
      screen: `${screen.width}x${screen.height}`,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: navigator.language,
      platform: navigator.platform,
      cookieEnabled: navigator.cookieEnabled,
      onlineStatus: navigator.onLine,
      touchSupport: 'ontouchstart' in window,
      colorDepth: screen.colorDepth,
      pixelRatio: window.devicePixelRatio || 1,
      hardwareConcurrency: navigator.hardwareConcurrency || 0
    };
  }

  /**
   * Get or create session ID
   */
  private getSessionId(): string {
    let sessionId = localStorage.getItem('session_id');
    if (!sessionId) {
      sessionId = this.generateUUID();
      localStorage.setItem('session_id', sessionId);
    }
    return sessionId;
  }

  /**
   * Generate UUID v4
   */
  private generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  /**
   * Initialize user identity
   */
  async initializeUserIdentity(): Promise<UserIdentity> {
    if (this.userIdentity) {
      return this.userIdentity;
    }

    const deviceInfo = this.getDeviceInfo();
    const fingerprint = await this.generateFingerprint();
    const sessionId = this.getSessionId();

    this.userIdentity = {
      fingerprint,
      sessionId,
      deviceInfo
    };

    // Store in session storage for this session
    sessionStorage.setItem('user_fingerprint', fingerprint);

    return this.userIdentity;
  }

  /**
   * Get current user identity
   */
  getUserIdentity(): UserIdentity | null {
    return this.userIdentity;
  }

  /**
   * Track job interaction
   */
  async trackJobInteraction(
    jobId: string, 
    interactionType: 'view' | 'click' | 'apply' | 'save',
    additionalData?: Record<string, any>
  ): Promise<void> {
    if (!this.userIdentity) {
      await this.initializeUserIdentity();
    }

    const trackingData = {
      job_id: jobId,
      interaction_type: interactionType,
      user_fingerprint: this.userIdentity!.fingerprint,
      session_id: this.userIdentity!.sessionId,
      device_info: this.userIdentity!.deviceInfo,
      interaction_data: additionalData || {},
      timestamp: new Date().toISOString()
    };

    try {
      // Send to backend
      const response = await fetch(`/api/jobs/${jobId}/interactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Device-Fingerprint': this.userIdentity!.fingerprint,
          'X-Session-ID': this.userIdentity!.sessionId
        },
        body: JSON.stringify(trackingData)
      });

      if (!response.ok) {
        console.warn('Failed to track job interaction:', response.statusText);
      }
    } catch (error) {
      console.warn('Error tracking job interaction:', error);
      // Store locally for retry later
      this.storeInteractionLocally(trackingData);
    }
  }

  /**
   * Store interaction locally for retry later
   */
  private storeInteractionLocally(trackingData: any): void {
    const key = 'pending_interactions';
    const stored = localStorage.getItem(key);
    const interactions = stored ? JSON.parse(stored) : [];
    interactions.push(trackingData);
    
    // Keep only last 100 interactions to avoid storage bloat
    if (interactions.length > 100) {
      interactions.splice(0, interactions.length - 100);
    }
    
    localStorage.setItem(key, JSON.stringify(interactions));
  }

  /**
   * Retry pending interactions
   */
  async retryPendingInteractions(): Promise<void> {
    const key = 'pending_interactions';
    const stored = localStorage.getItem(key);
    if (!stored) return;

    const interactions = JSON.parse(stored);
    const successful: number[] = [];

    for (let i = 0; i < interactions.length; i++) {
      try {
        const interaction = interactions[i];
        const response = await fetch(`/api/jobs/${interaction.job_id}/interactions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Device-Fingerprint': interaction.user_fingerprint,
            'X-Session-ID': interaction.session_id
          },
          body: JSON.stringify(interaction)
        });

        if (response.ok) {
          successful.push(i);
        }
      } catch (error) {
        // Keep for next retry
        console.warn('Retry failed for interaction:', error);
      }
    }

    // Remove successful interactions
    const remaining = interactions.filter((_: any, index: number) => !successful.includes(index));
    if (remaining.length === 0) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, JSON.stringify(remaining));
    }
  }

  /**
   * Get user's job interaction history
   */
  async getUserJobHistory(): Promise<any[]> {
    if (!this.userIdentity) {
      await this.initializeUserIdentity();
    }

    try {
      const response = await fetch('/api/user/job-history', {
        headers: {
          'X-Device-Fingerprint': this.userIdentity!.fingerprint,
          'X-Session-ID': this.userIdentity!.sessionId
        }
      });

      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.warn('Error fetching job history:', error);
    }

    return [];
  }

  /**
   * Check if jobs have been interacted with by user
   */
  async getJobInteractionStatus(jobIds: string[]): Promise<Record<string, any>> {
    if (!this.userIdentity || jobIds.length === 0) {
      return {};
    }

    try {
      const params = new URLSearchParams();
      jobIds.forEach(id => params.append('job_ids', id));

      const response = await fetch(`/api/user/job-interactions?${params}`, {
        headers: {
          'X-Device-Fingerprint': this.userIdentity!.fingerprint,
          'X-Session-ID': this.userIdentity!.sessionId
        }
      });

      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.warn('Error fetching job interaction status:', error);
    }

    return {};
  }

  /**
   * Start background sync of pending interactions
   */
  startBackgroundSync(): void {
    // Retry pending interactions every 5 minutes
    setInterval(() => {
      if (navigator.onLine) {
        this.retryPendingInteractions();
      }
    }, 5 * 60 * 1000);

    // Retry when coming back online
    window.addEventListener('online', () => {
      this.retryPendingInteractions();
    });
  }
}

// Export singleton instance
export const userTracker = UserTrackingService.getInstance();

// Auto-initialize when module loads
userTracker.initializeUserIdentity().catch(console.error);

// Start background sync
userTracker.startBackgroundSync();
