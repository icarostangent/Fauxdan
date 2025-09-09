<template>
  <div class="host-detail">
    <!-- Loading and Error States -->
    <div v-if="loading" class="loading-state">Loading...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>
    
    <div v-else-if="host" class="host-container">
      <!-- Header Section -->
      <div class="header">
        <div class="header-content">
          <div class="host-info">
            <h1 class="host-ip">{{ host.ip }}</h1>
            <div class="host-meta">
              <span class="privacy-badge" :class="{ 'public': !host.private, 'private': host.private }">
                {{ host.private ? 'Private' : 'Public' }}
              </span>
              <span class="last-seen">Last seen: {{ formatLastSeen(host.last_seen) }}</span>
            </div>
          </div>
          <button class="back-button" @click="$router.go(-1)">
            ← Back to List
          </button>
        </div>
      </div>

      <!-- Main Content -->
      <div class="main-content">
        <!-- Host Overview Section -->
        <section class="overview-section">
          <h2 class="section-title">Host Overview</h2>
          <div class="overview-grid">
            <div class="stat-card">
              <div class="stat-value">{{ host.ports.length }}</div>
              <div class="stat-label">Open Ports</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ uniqueServices.length }}</div>
              <div class="stat-label">Services</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ host.domains.length }}</div>
              <div class="stat-label">Domains</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ host.ssl_certificates.length }}</div>
              <div class="stat-label">SSL Certificates</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ sslPortsCount }}</div>
              <div class="stat-label">SSL/TLS Ports</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ getSecurityScore() }}</div>
              <div class="stat-label">Security Score</div>
            </div>
          </div>
        </section>

        <!-- Security Analysis Section -->
        <section class="security-section">
          <h2 class="section-title">Security Analysis</h2>
          <div class="security-grid">
            <div class="security-card">
              <div class="security-header">
                <h3 class="security-title">Open Services</h3>
                <span class="security-status" :class="getServiceSecurityClass()">
                  {{ getServiceSecurityStatus() }}
                </span>
              </div>
              <div class="security-details">
                <div class="service-breakdown">
                  <div v-for="service in serviceBreakdown" :key="service.name" class="service-item">
                    <span class="service-name">{{ service.name }}</span>
                    <span class="service-count">{{ service.count }} port{{ (service.count as number) > 1 ? 's' : '' }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="security-card">
              <div class="security-header">
                <h3 class="security-title">SSL/TLS Status</h3>
                <span class="security-status" :class="getSSLSecurityClass()">
                  {{ getSSLSecurityStatus() }}
                </span>
              </div>
              <div class="security-details">
                <div class="ssl-breakdown">
                  <div class="ssl-item">
                    <span class="ssl-label">SSL-enabled ports:</span>
                    <span class="ssl-value">{{ sslPortsCount }}</span>
                  </div>
                  <div class="ssl-item">
                    <span class="ssl-label">Valid certificates:</span>
                    <span class="ssl-value">{{ validCertificatesCount }}</span>
                  </div>
                  <div class="ssl-item">
                    <span class="ssl-label">Expired certificates:</span>
                    <span class="ssl-value">{{ expiredCertificatesCount }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="security-card">
              <div class="security-header">
                <h3 class="security-title">Network Exposure</h3>
                <span class="security-status" :class="getExposureClass()">
                  {{ getExposureStatus() }}
                </span>
              </div>
              <div class="security-details">
                <div class="exposure-breakdown">
                  <div class="exposure-item">
                    <span class="exposure-label">Host type:</span>
                    <span class="exposure-value">{{ host.private ? 'Private' : 'Public' }}</span>
                  </div>
                  <div class="exposure-item">
                    <span class="exposure-label">High-risk ports:</span>
                    <span class="exposure-value">{{ highRiskPorts.length }}</span>
                  </div>
                  <div class="exposure-item">
                    <span class="exposure-label">Common services:</span>
                    <span class="exposure-value">{{ commonServicePorts.length }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Scan Information Section -->
        <section v-if="host.scan" class="scan-section">
          <h2 class="section-title">Scan Information</h2>
          <div class="scan-info-grid">
            <div class="scan-info-card">
              <div class="scan-info-item">
                <span class="scan-label">Discovery Date:</span>
                <span class="scan-value">{{ formatDate(host.last_seen) }}</span>
              </div>
              <div class="scan-info-item">
                <span class="scan-label">Host Status:</span>
                <span class="scan-value" :class="getHostStatusClass()">{{ getHostStatus() }}</span>
              </div>
              <div class="scan-info-item">
                <span class="scan-label">Last Activity:</span>
                <span class="scan-value">{{ formatLastSeen(host.last_seen) }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Ports Section -->
        <section class="ports-section">
          <h2 class="section-title">Open Ports</h2>
          <div class="ports-grid">
            <div v-for="port in host.ports" :key="port.id || `port-${port.port_number}`" class="port-card">
              <div class="port-header">
                <div class="port-info">
                  <span class="port-number">{{ port.port_number }}/{{ port.proto }}</span>
                  <span class="service-badge">{{ getServiceName(port.port_number, port.banner) }}</span>
                  <span class="status-badge">{{ port.status }}</span>
                  <span v-if="isSSLPort(port.port_number, port.banner)" class="ssl-indicator">🔒</span>
                </div>
                <span class="port-timestamp">{{ formatPortDate(port.last_seen) }}</span>
              </div>
              
              <div v-if="port.banner" class="banner-container">
                <div class="banner-header">Banner</div>
                <pre class="banner-content">{{ port.banner }}</pre>
              </div>
              
              <div v-else class="no-banner">
                <span class="no-banner-text">No banner information available</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Domains Section -->
        <section v-if="host.domains.length" class="domains-section">
          <h2 class="section-title">Domains</h2>
          <div class="domains-grid">
            <div v-for="domain in host.domains" :key="domain.id" class="domain-card">
              <div class="domain-name">{{ domain.name }}</div>
              <div class="domain-source">{{ domain.source }}</div>
            </div>
          </div>
        </section>

        <!-- SSL Certificates Section -->
        <section v-if="host.ssl_certificates && host.ssl_certificates.length > 0" class="ssl-section">
          <h2 class="section-title">SSL Certificates</h2>
          <div class="ssl-grid">
            <div v-for="cert in host.ssl_certificates" :key="cert.id" class="cert-card">
              <div class="cert-header">
                <div class="cert-subject">{{ cert.subject_cn || 'Unknown Subject' }}</div>
                <span class="cert-status" :class="getCertificateStatusClass(cert)">
                  {{ getCertificateStatus(cert) }}
                </span>
              </div>
              
              <div class="cert-details">
                <div class="cert-issuer">
                  <span class="label">Issuer:</span>
                  <span class="value">{{ cert.issuer_cn || 'Unknown Issuer' }}</span>
                </div>
                
                <div class="cert-validity">
                  <div class="validity-item">
                    <span class="label">Valid From:</span>
                    <span class="value">{{ formatDate(cert.valid_from) }}</span>
                  </div>
                  <div class="validity-item">
                    <span class="label">Valid Until:</span>
                    <span class="value">{{ formatDate(cert.valid_until) }}</span>
                  </div>
                </div>
                
                <div class="cert-fingerprint">
                  <span class="label">Fingerprint:</span>
                  <code class="fingerprint">{{ cert.fingerprint }}</code>
                </div>
              </div>
              
              <div v-if="(cert as any).extensions?.subjectAltName && (cert as any).extensions.subjectAltName.length > 0" class="cert-sans">
                <div class="sans-label">Subject Alternative Names:</div>
                <div class="sans-list">
                  <span v-for="(name, index) in (cert as any).extensions.subjectAltName" :key="index" class="san-item">
                    {{ name }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Host } from '@/types'
import { formatLastSeen, formatDate, formatPortDate } from '@/utils/date'
import { analytics } from '@/services/analytics'

export default defineComponent({
  name: 'HostDetailView',

  setup() {
    const route = useRoute()
    const router = useRouter()
    const host = ref<Host | null>(null)
    const loading = ref(true)
    const error = ref('')

    const loadHost = async () => {
      try {
        const response = await fetch(`/api/hosts/${route.params.id}/`)
        if (!response.ok) {
          throw new Error('Failed to load host details')
        }
        host.value = await response.json()
      } catch (err) {
        error.value = 'Failed to load host details. Please try again.'
        console.error('Error loading host:', err)
      } finally {
        loading.value = false
      }
    }

    // Helper function to get service name from banner content (intelligent detection)
    const getServiceName = (portNumber: number | null, banner: string | null): string => {
      // Only detect service from banner content, not port number
      if (banner) {
        const bannerLower = banner.toLowerCase()
        
        // Web servers
        if (bannerLower.includes('apache')) return 'Apache'
        if (bannerLower.includes('nginx')) return 'Nginx'
        if (bannerLower.includes('iis')) return 'IIS'
        if (bannerLower.includes('lighttpd')) return 'Lighttpd'
        if (bannerLower.includes('caddy')) return 'Caddy'
        
        // SSH services
        if (bannerLower.includes('ssh')) return 'SSH'
        if (bannerLower.includes('openssh')) return 'OpenSSH'
        
        // FTP services
        if (bannerLower.includes('ftp')) return 'FTP'
        if (bannerLower.includes('vsftpd')) return 'vsftpd'
        if (bannerLower.includes('proftpd')) return 'ProFTPD'
        
        // Mail services
        if (bannerLower.includes('smtp')) return 'SMTP'
        if (bannerLower.includes('postfix')) return 'Postfix'
        if (bannerLower.includes('sendmail')) return 'Sendmail'
        if (bannerLower.includes('exim')) return 'Exim'
        
        // HTTP/HTTPS services
        if (bannerLower.includes('http')) return 'HTTP'
        if (bannerLower.includes('https')) return 'HTTPS'
        
        // Database services
        if (bannerLower.includes('mysql')) return 'MySQL'
        if (bannerLower.includes('postgresql')) return 'PostgreSQL'
        if (bannerLower.includes('mssql')) return 'MSSQL'
        if (bannerLower.includes('redis')) return 'Redis'
        if (bannerLower.includes('mongodb')) return 'MongoDB'
        
        // Other services
        if (bannerLower.includes('telnet')) return 'Telnet'
        if (bannerLower.includes('dns')) return 'DNS'
        if (bannerLower.includes('rdp')) return 'RDP'
        if (bannerLower.includes('vnc')) return 'VNC'
        if (bannerLower.includes('imap')) return 'IMAP'
        if (bannerLower.includes('pop3')) return 'POP3'
      }
      
      return 'Unknown'
    }

    // Check if port has SSL/TLS based on banner content
    const isSSLPort = (portNumber: number | null, banner: string | null): boolean => {
      if (banner) {
        const bannerLower = banner.toLowerCase()
        return bannerLower.includes('ssl') || 
               bannerLower.includes('tls') || 
               bannerLower.includes('https') ||
               bannerLower.includes('starttls')
      }
      return false
    }

    // Helper function to get certificate status
    const getCertificateStatus = (cert: any): string => {
      const now = new Date()
      const validUntil = new Date(cert.valid_until)
      const validFrom = new Date(cert.valid_from)
      
      if (now < validFrom) return 'Not Yet Valid'
      if (now > validUntil) return 'Expired'
      
      const daysUntilExpiry = Math.ceil((validUntil.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
      if (daysUntilExpiry <= 30) return 'Expires Soon'
      if (daysUntilExpiry <= 7) return 'Critical'
      
      return 'Valid'
    }

    // Helper function to get certificate status class
    const getCertificateStatusClass = (cert: any): string => {
      const status = getCertificateStatus(cert)
      
      switch (status) {
        case 'Valid':
          return 'status-valid'
        case 'Expires Soon':
          return 'status-warning'
        case 'Critical':
          return 'status-critical'
        case 'Expired':
          return 'status-expired'
        case 'Not Yet Valid':
          return 'status-pending'
        default:
          return 'status-unknown'
      }
    }

    onMounted(() => {
      // Track page view when component mounts
      analytics.trackPageView(`/hosts/${route.params.id}`)
      loadHost()
    })

    // Computed properties for the new sections
    const uniqueServices = computed(() => {
      if (!host.value) return []
      const services = new Set()
      host.value.ports.forEach(port => {
        const service = getServiceName(port.port_number, port.banner)
        if (service !== 'Unknown') {
          services.add(service)
        }
      })
      return Array.from(services)
    })

    const sslPortsCount = computed(() => {
      if (!host.value) return 0
      return host.value.ports.filter(port => isSSLPort(port.port_number, port.banner)).length
    })

    const validCertificatesCount = computed(() => {
      if (!host.value) return 0
      return host.value.ssl_certificates.filter(cert => getCertificateStatus(cert) === 'Valid').length
    })

    const expiredCertificatesCount = computed(() => {
      if (!host.value) return 0
      return host.value.ssl_certificates.filter(cert => getCertificateStatus(cert) === 'Expired').length
    })

    const serviceBreakdown = computed(() => {
      if (!host.value) return []
      const services: Record<string, number> = {}
      host.value.ports.forEach(port => {
        const service = getServiceName(port.port_number, port.banner)
        services[service] = (services[service] || 0) + 1
      })
      return Object.entries(services)
        .map(([name, count]) => ({ name, count: count as number }))
        .sort((a, b) => b.count - a.count)
    })

    const highRiskPorts = computed(() => {
      if (!host.value) return []
      const riskPorts = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 1433, 3306, 3389, 5432, 5900]
      return host.value.ports.filter(port => port.port_number && riskPorts.includes(port.port_number))
    })

    const commonServicePorts = computed(() => {
      if (!host.value) return []
      const commonPorts = [80, 443, 22, 21, 25, 53, 110, 143, 993, 995]
      return host.value.ports.filter(port => port.port_number && commonPorts.includes(port.port_number))
    })

    // Security analysis methods
    const getSecurityScore = () => {
      if (!host.value) return 'N/A'
      let score = 100
      
      // Deduct points for high-risk ports
      score -= highRiskPorts.value.length * 10
      
      // Deduct points for expired certificates
      score -= expiredCertificatesCount.value * 15
      
      // Add points for SSL usage
      score += sslPortsCount.value * 5
      
      // Add points for valid certificates
      score += validCertificatesCount.value * 10
      
      return Math.max(0, Math.min(100, score))
    }

    const getServiceSecurityStatus = () => {
      const riskCount = highRiskPorts.value.length
      if (riskCount === 0) return 'Good'
      if (riskCount <= 2) return 'Moderate'
      return 'High Risk'
    }

    const getServiceSecurityClass = () => {
      const status = getServiceSecurityStatus()
      if (status === 'Good') return 'status-valid'
      if (status === 'Moderate') return 'status-warning'
      return 'status-critical'
    }

    const getSSLSecurityStatus = () => {
      const sslCount = sslPortsCount.value
      const validCount = validCertificatesCount.value
      const expiredCount = expiredCertificatesCount.value
      
      if (sslCount === 0) return 'No SSL'
      if (expiredCount > 0) return 'Issues Found'
      if (validCount > 0) return 'Good'
      return 'Unknown'
    }

    const getSSLSecurityClass = () => {
      const status = getSSLSecurityStatus()
      if (status === 'Good') return 'status-valid'
      if (status === 'Issues Found') return 'status-critical'
      if (status === 'No SSL') return 'status-warning'
      return 'status-unknown'
    }

    const getExposureStatus = () => {
      if (!host.value) return 'Unknown'
      if (host.value.private) return 'Private'
      const riskCount = highRiskPorts.value.length
      if (riskCount === 0) return 'Low'
      if (riskCount <= 3) return 'Moderate'
      return 'High'
    }

    const getExposureClass = () => {
      const status = getExposureStatus()
      if (status === 'Low' || status === 'Private') return 'status-valid'
      if (status === 'Moderate') return 'status-warning'
      if (status === 'High') return 'status-critical'
      return 'status-unknown'
    }

    const getHostStatus = () => {
      if (!host.value || !host.value.last_seen) return 'Unknown'
      const now = new Date()
      const lastSeen = new Date(host.value.last_seen)
      const daysSinceLastSeen = (now.getTime() - lastSeen.getTime()) / (1000 * 60 * 60 * 24)
      
      if (daysSinceLastSeen <= 1) return 'Active'
      if (daysSinceLastSeen <= 7) return 'Recent'
      if (daysSinceLastSeen <= 30) return 'Stale'
      return 'Inactive'
    }

    const getHostStatusClass = () => {
      const status = getHostStatus()
      if (status === 'Active') return 'status-valid'
      if (status === 'Recent') return 'status-warning'
      return 'status-critical'
    }

    return {
      host,
      loading,
      error,
      formatLastSeen,
      formatPortDate,
      formatDate,
      getServiceName,
      isSSLPort,
      getCertificateStatus,
      getCertificateStatusClass,
      uniqueServices,
      sslPortsCount,
      validCertificatesCount,
      expiredCertificatesCount,
      serviceBreakdown,
      highRiskPorts,
      commonServicePorts,
      getSecurityScore,
      getServiceSecurityStatus,
      getServiceSecurityClass,
      getSSLSecurityStatus,
      getSSLSecurityClass,
      getExposureStatus,
      getExposureClass,
      getHostStatus,
      getHostStatusClass
    }
  }
})
</script>

<style scoped>
.host-detail {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.loading-state, .error-state {
  text-align: center;
  padding: 40px 20px;
  font-size: 18px;
}

.error-state {
  color: #ef4444;
}

.host-container {
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
}

.header {
  background: #2d2d2d;
  padding: 24px;
  border-bottom: 1px solid #404040;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.host-info {
  flex: 1;
}

.host-ip {
  font-size: 32px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 12px 0;
}

.host-meta {
  display: flex;
  gap: 16px;
  align-items: center;
}

.privacy-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.privacy-badge.public {
  background: #10b981;
  color: white;
}

.privacy-badge.private {
  background: #6b7280;
  color: white;
}

.last-seen {
  font-size: 14px;
  color: #9ca3af;
}

.back-button {
  padding: 12px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.back-button:hover {
  background: #2563eb;
}

.main-content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 20px 0;
}

/* Ports Section */
.ports-section {
  background: #2d2d2d;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #404040;
}

.ports-grid {
  display: grid;
  gap: 20px;
}

.port-card {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #404040;
}

.port-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.port-info {
  display: flex;
  gap: 12px;
  align-items: center;
}

.port-number {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
}

.service-badge {
  padding: 4px 12px;
  background: #3b82f6;
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge {
  padding: 4px 12px;
  background: #10b981;
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.port-timestamp {
  font-size: 12px;
  color: #9ca3af;
}

.banner-container {
  background: #0f0f0f;
  border-radius: 6px;
  padding: 16px;
  border: 1px solid #404040;
}

.banner-header {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.banner-content {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: #10b981;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.no-banner {
  text-align: center;
  padding: 20px;
  color: #6b7280;
  font-style: italic;
}

.no-banner-text {
  font-size: 14px;
}

/* Domains Section */
.domains-section {
  background: #2d2d2d;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #404040;
}

.domains-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.domain-card {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #404040;
  transition: border-color 0.2s;
}

.domain-card:hover {
  border-color: #3b82f6;
}

.domain-name {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 8px;
  word-break: break-all;
}

.domain-source {
  font-size: 12px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* SSL Section */
.ssl-section {
  background: #2d2d2d;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #404040;
}

.ssl-grid {
  display: grid;
  gap: 20px;
}

.cert-card {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #404040;
}

.cert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.cert-subject {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
}

.cert-status {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-valid {
  background: #10b981;
  color: white;
}

.status-warning {
  background: #f59e0b;
  color: white;
}

.status-critical {
  background: #ef4444;
  color: white;
}

.status-expired {
  background: #6b7280;
  color: white;
}

.status-pending {
  background: #3b82f6;
  color: white;
}

.status-unknown {
  background: #6b7280;
  color: white;
}

.cert-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cert-issuer, .cert-validity, .cert-fingerprint {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.value {
  font-size: 14px;
  color: #ffffff;
  font-weight: 500;
}

.validity-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #404040;
}

.validity-item:last-child {
  border-bottom: none;
}

.fingerprint {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: #10b981;
  background: #0f0f0f;
  padding: 8px;
  border-radius: 4px;
  word-break: break-all;
}

.cert-sans {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #404040;
}

.sans-label {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.sans-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.san-item {
  padding: 4px 12px;
  background: #3b82f6;
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

/* Overview Section */
.overview-section {
  background: #2d2d2d;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #404040;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
}

.stat-card {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  border: 1px solid #404040;
  transition: border-color 0.2s, transform 0.2s;
}

.stat-card:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 12px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

/* Security Analysis Section */
.security-section {
  background: #2d2d2d;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #404040;
}

.security-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.security-card {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #404040;
}

.security-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.security-title {
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.security-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.security-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.service-breakdown, .ssl-breakdown, .exposure-breakdown {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.service-item, .ssl-item, .exposure-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #404040;
}

.service-item:last-child, .ssl-item:last-child, .exposure-item:last-child {
  border-bottom: none;
}

.service-name, .ssl-label, .exposure-label {
  font-size: 14px;
  color: #9ca3af;
}

.service-count, .ssl-value, .exposure-value {
  font-size: 14px;
  color: #ffffff;
  font-weight: 500;
}

/* Scan Information Section */
.scan-section {
  background: #2d2d2d;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #404040;
}

.scan-info-grid {
  display: grid;
  gap: 20px;
}

.scan-info-card {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #404040;
}

.scan-info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #404040;
}

.scan-info-item:last-child {
  border-bottom: none;
}

.scan-label {
  font-size: 14px;
  color: #9ca3af;
  font-weight: 600;
}

.scan-value {
  font-size: 14px;
  color: #ffffff;
  font-weight: 500;
}
</style>
