interface AnalyticsEvent {
  event_type: string
  category: string
  action: string
  label?: string
  value?: number
  userId?: string
  sessionId: string
  timestamp: number
  page_url: string
  userAgent: string
  ip?: string
}

class AnalyticsService {
  private sessionId: string
  private userId?: string
  private pendingEvents: Set<string> = new Set() // Track pending events

  constructor() {
    this.sessionId = this.generateSessionId()
    this.userId = this.getUserId()
  }

  private generateSessionId(): string {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  }

  private getUserId(): string | undefined {
    return localStorage.getItem('userId') || undefined
  }

  private generateEventKey(event: AnalyticsEvent): string {
    // Create a unique key for this event to prevent duplicates
    return `${event.event_type}_${event.category}_${event.action}_${event.page_url}_${Date.now()}`
  }

  trackPageView(page: string) {
    const event: AnalyticsEvent = {
      event_type: 'page_view',
      category: 'engagement',
      action: 'page_view',
      label: undefined,
      value: undefined,
      userId: this.userId,
      sessionId: this.sessionId,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      page_url: page
    }

    this.sendToBackend(event)
    
    // Send to GA4 if configured
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'page_view', {
        event_category: 'engagement',
        event_action: 'page_view',
        page_title: page
      })
    }
  }

  trackEvent(eventData: {
    event: string
    category: string
    action: string
    label?: string
    value?: number
    userId?: string
  }) {
    const event: AnalyticsEvent = {
      event_type: eventData.event,
      category: eventData.category,
      action: eventData.action,
      label: eventData.label,
      value: eventData.value,
      userId: eventData.userId,
      sessionId: this.sessionId,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      page_url: window.location.pathname
    }

    this.sendToBackend(event)
    
    // Also send to GA4 if configured
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', event.event_type, {
        event_category: event.category,
        event_action: event.action,
        event_label: event.label,
        value: event.value
      })
    }
  }

  private async sendToBackend(event: AnalyticsEvent) {
    const eventKey = this.generateEventKey(event)
    
    // Prevent duplicate events
    if (this.pendingEvents.has(eventKey)) {
      console.log('Event already pending, skipping:', eventKey)
      return
    }
    
    this.pendingEvents.add(eventKey)
    
    try {
      const response = await fetch('/analytics/events/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(event)
      })
      
      if (!response.ok) {
        console.error('Analytics request failed:', response.status, response.statusText)
        const errorText = await response.text()
        console.error('Error details:', errorText)
      }
      
    } catch (error) {
      console.error('Analytics error:', error)
    } finally {
      // Remove from pending events after a delay
      setTimeout(() => {
        this.pendingEvents.delete(eventKey)
      }, 1000)
    }
  }
}

export const analytics = new AnalyticsService()
