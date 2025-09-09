<template>
  <div 
    class="host-card"
    @click="navigateToHost"
    @mouseenter="hover = true"
    @mouseleave="hover = false"
    :style="{
      transform: hover ? 'translateY(-2px)' : 'none',
      boxShadow: hover ? '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)' : 'none'
    }"
  >
    <!-- Header -->
    <div class="header">
      <h3 class="ip">{{ host.ip }}</h3>
      <div class="meta" style="justify-content: flex-start;">
        <span class="privacy-badge" :class="{ 'public': !host.private, 'private': host.private }">
          {{ host.private ? 'Private' : 'Public' }}
        </span>
        <span class="last-seen" style="text-align: left;">{{ formatLastSeen(host.last_seen) }}</span>
      </div>
    </div>

    <!-- Quick Stats -->
    <div class="quick-stats">
      <div class="stat-item">
        <span class="stat-label">Ports:</span>
        <span class="stat-value">{{ host.ports?.length || 0 }}</span>
      </div>
      <div class="stat-item" v-if="host.ssl_certificates?.length">
        <span class="stat-label">SSL:</span>
        <span class="stat-value ssl">{{ host.ssl_certificates.length }}</span>
      </div>
      <div class="stat-item" v-if="host.domains?.length">
        <span class="stat-label">Domains:</span>
        <span class="stat-value">{{ host.domains.length }}</span>
      </div>
    </div>

    <!-- Ports with Service Detection -->
    <div v-if="host.ports?.length" class="ports-section">
      <h4 class="section-title">Open Ports</h4>
      <div class="ports-grid">
        <div v-for="port in host.ports.slice(0, 6)" :key="port.id" class="port-item">
          <div class="port-info">
            <span class="port-number">{{ port.port_number }}/{{ port.proto }}</span>
            <span class="port-service">{{ getServiceName(port.port_number, port.banner) }}</span>
          </div>
          <div class="port-meta">
            <span class="port-status" :class="port.status">{{ port.status }}</span>
            <span v-if="isSSLPort(port.port_number, port.banner)" class="ssl-indicator">🔒</span>
          </div>
        </div>
        <div v-if="host.ports.length > 6" class="more-ports">
          +{{ host.ports.length - 6 }} more
        </div>
      </div>
    </div>

    <!-- Domains -->
    <div v-if="host.domains?.length" class="domains-section">
      <h4 class="section-title">Domains</h4>
      <div class="domains-list">
        <div v-for="domain in host.domains.slice(0, 3)" :key="domain.id" class="domain-item">
          <span class="domain-name">{{ domain.name }}</span>
          <span class="domain-source">{{ domain.source }}</span>
        </div>
        <div v-if="host.domains.length > 3" class="more-domains">
          +{{ host.domains.length - 3 }} more domains
        </div>
      </div>
    </div>

    <!-- SSL Certificates Info -->
    <div v-if="host.ssl_certificates?.length" class="ssl-section">
      <h4 class="section-title">SSL Certificates</h4>
      <div class="ssl-info">
        <span class="ssl-count">{{ host.ssl_certificates.length }} certificate(s)</span>
        <span v-if="hasValidCertificates" class="ssl-status valid">Valid</span>
        <span v-else class="ssl-status invalid">Invalid/Expired</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType, ref, computed } from 'vue'
import { Host } from '@/types'
import { formatLastSeen, formatDate, formatPortDate } from '@/utils/date'
import { useRouter } from 'vue-router'
import { analytics } from '@/services/analytics'

export default defineComponent({
  name: 'HostElement',

  props: {
    host: {
      type: Object as PropType<Host>,
      required: true
    }
  },

  setup(props) {
    const hover = ref(false)
    const router = useRouter()

    const navigateToHost = () => {
      if (props.host.id) {
        // Track host card click
        analytics.trackEvent({
          event: 'host_interaction',
          category: 'content',
          action: 'click_host_card',
          label: props.host.ip,
          value: props.host.ports?.length || 0
        })
        
        router.push(`/hosts/${props.host.id}`)
      }
    }

    // Service detection based on banner content only
    const getServiceName = (portNumber: number, banner: string | null) => {
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
    const isSSLPort = (portNumber: number, banner: string | null) => {
      if (banner) {
        const bannerLower = banner.toLowerCase()
        return bannerLower.includes('ssl') || 
               bannerLower.includes('tls') || 
               bannerLower.includes('https') ||
               bannerLower.includes('starttls')
      }
      return false
    }

    // Check if host has valid SSL certificates
    const hasValidCertificates = computed(() => {
      if (!props.host.ssl_certificates?.length) return false
      
      const now = new Date()
      return props.host.ssl_certificates.some(cert => {
        const validUntil = new Date(cert.valid_until)
        return validUntil > now
      })
    })

    return {
      hover,
      navigateToHost,
      formatLastSeen,
      formatPortDate,
      formatDate,
      getServiceName,
      isSSLPort,
      hasValidCertificates
    }
  }
})
</script>

<style scoped>
.host-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.header {
  margin-bottom: 16px;
}

.ip {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 8px 0;
}

.meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.privacy-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.privacy-badge.public {
  background-color: #d1fae5;
  color: #065f46;
}

.privacy-badge.private {
  background-color: #f3f4f6;
  color: #374151;
}

.last-seen {
  font-size: 12px;
  color: #6b7280;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px 0;
}

.ports-section {
  margin-bottom: 16px;
}

.ports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
}

.port-item {
  background-color: #f9fafb;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
}

.port-number {
  font-weight: 500;
  color: #374151;
}

.port-status {
  color: #6b7280;
  margin-left: 4px;
}

.domains-section {
  margin-bottom: 16px;
}

.domains-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.domain-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f9fafb;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  gap: 8px;
  min-width: 0;
}

.domain-name {
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.domain-source {
  color: #6b7280;
  font-size: 11px;
  flex-shrink: 0;
  padding-left: 8px;
}

/* Quick Stats */
.quick-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.stat-label {
  color: #6b7280;
  font-weight: 500;
}

.stat-value {
  color: #374151;
  font-weight: 600;
}

.stat-value.ssl {
  color: #059669;
  background-color: #d1fae5;
  padding: 2px 6px;
  border-radius: 4px;
}

/* Enhanced Ports Section */
.port-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f9fafb;
  border-radius: 6px;
  font-size: 12px;
}

.port-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.port-number {
  font-weight: 600;
  color: #374151;
}

.port-service {
  color: #6b7280;
  font-size: 11px;
}

.port-meta {
  display: flex;
  align-items: center;
  gap: 6px;
}

.port-status {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
}

.port-status.open {
  background-color: #d1fae5;
  color: #065f46;
}

.port-status.closed {
  background-color: #fef2f2;
  color: #dc2626;
}

.port-status.filtered {
  background-color: #fef3c7;
  color: #d97706;
}

.ssl-indicator {
  font-size: 12px;
}

.more-ports,
.more-domains {
  text-align: center;
  color: #6b7280;
  font-size: 11px;
  font-style: italic;
  padding: 8px;
  background-color: #f3f4f6;
  border-radius: 4px;
  margin-top: 4px;
}

/* SSL Section */
.ssl-section {
  margin-bottom: 16px;
}

.ssl-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f0f9ff;
  border-radius: 6px;
  font-size: 12px;
}

.ssl-count {
  color: #0369a1;
  font-weight: 500;
}

.ssl-status {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
}

.ssl-status.valid {
  background-color: #d1fae5;
  color: #065f46;
}

.ssl-status.invalid {
  background-color: #fef2f2;
  color: #dc2626;
}
</style>
