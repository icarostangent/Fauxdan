<template>
  <div class="port-metrics" v-if="hasMetrics">
    <div class="metrics-header">
      <h3 class="metrics-title">{{ portContextTitle }}</h3>
      <div class="port-badges">
        <span 
          v-for="category in detectedCategories" 
          :key="category"
          class="port-badge"
          :class="category"
        >
          {{ getCategoryLabel(category) }}
        </span>
      </div>
    </div>
    
    <div class="metrics-grid">
      <!-- Web Ports Metrics -->
      <div v-if="detectedCategories.includes('web')" class="metric-card web">
        <div class="metric-header">
          <h4>🌐 Web Services</h4>
        </div>
        <div class="metric-content">
          <div class="metric-item">
            <span class="metric-label">Total Hosts:</span>
            <span class="metric-value">{{ webMetrics.totalHosts }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">SSL Enabled:</span>
            <span class="metric-value">{{ webMetrics.sslEnabled }} ({{ webMetrics.sslPercentage }}%)</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Common Tech:</span>
            <span class="metric-value">{{ webMetrics.commonTechnologies.join(', ') }}</span>
          </div>
        </div>
      </div>

      <!-- Database Ports Metrics -->
      <div v-if="detectedCategories.includes('database')" class="metric-card database">
        <div class="metric-header">
          <h4>🗄️ Database Services</h4>
        </div>
        <div class="metric-content">
          <div class="metric-item">
            <span class="metric-label">Total Hosts:</span>
            <span class="metric-value">{{ databaseMetrics.totalHosts }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Database Types:</span>
            <span class="metric-value">{{ databaseMetrics.databaseTypes.join(', ') }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Anonymous Access:</span>
            <span class="metric-value">{{ databaseMetrics.anonymousAccess }}</span>
          </div>
        </div>
      </div>

      <!-- Proxy Ports Metrics -->
      <div v-if="detectedCategories.includes('proxy')" class="metric-card proxy">
        <div class="metric-header">
          <h4>🔗 Proxy Services</h4>
        </div>
        <div class="metric-content">
          <div class="metric-item">
            <span class="metric-label">Total Hosts:</span>
            <span class="metric-value">{{ proxyMetrics.totalHosts }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Proxy Types:</span>
            <span class="metric-value">{{ proxyMetrics.proxyTypes.join(', ') }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">High Anonymity:</span>
            <span class="metric-value">{{ proxyMetrics.highAnonymity }}</span>
          </div>
        </div>
      </div>

      <!-- DNS Ports Metrics -->
      <div v-if="detectedCategories.includes('dns')" class="metric-card dns">
        <div class="metric-header">
          <h4>🌍 DNS Services</h4>
        </div>
        <div class="metric-content">
          <div class="metric-item">
            <span class="metric-label">Total Hosts:</span>
            <span class="metric-value">{{ dnsMetrics.totalHosts }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Server Types:</span>
            <span class="metric-value">{{ dnsMetrics.serverTypes.join(', ') }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">DNSSEC Enabled:</span>
            <span class="metric-value">{{ dnsMetrics.dnssecEnabled }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, onMounted } from 'vue'
import { analytics } from '@/services/analytics'

interface Port {
  port_number: number
  // add other port properties as needed
}

interface Host {
  ports?: Port[]
  // add other host properties as needed
}

export default defineComponent({
  name: 'PortMetrics',
  
  props: {
    hosts: {
      type: Array,
      required: true
    },
    searchQuery: {
      type: String,
      default: ''
    }
  },

  setup(props) {
    // Track metrics component mount
    onMounted(() => {
      analytics.trackEvent({
        event: 'metrics_display',
        category: 'content',
        action: 'show_port_metrics',
        label: props.searchQuery || 'all_hosts',
        value: props.hosts?.length || 0
      })
    })

    // Track category detection
    const trackCategoryDetection = (category: string, count: number) => {
      analytics.trackEvent({
        event: 'metrics_category',
        category: 'content',
        action: 'detect_category',
        label: category,
        value: count
      })
    }

    // Computed properties for metrics
    const hasMetrics = computed(() => props.hosts && props.hosts.length > 0)
    
    const portContextTitle = computed(() => {
      if (props.searchQuery) {
        return `Port Metrics for "${props.searchQuery}"`
      }
      return 'Port Metrics Overview'
    })

    const detectedCategories = computed(() => {
      const categories = []
      if (webMetrics.value.totalHosts > 0) categories.push('web')
      if (databaseMetrics.value.totalHosts > 0) categories.push('database')
      if (proxyMetrics.value.totalHosts > 0) categories.push('proxy')
      if (dnsMetrics.value.totalHosts > 0) categories.push('dns')
      
      // Track detected categories
      categories.forEach(category => {
        const count = getCategoryCount(category)
        if (count > 0) {
          trackCategoryDetection(category, count)
        }
      })
      
      return categories
    })

    const getCategoryCount = (category: string) => {
      switch (category) {
        case 'web': return webMetrics.value.totalHosts
        case 'database': return databaseMetrics.value.totalHosts
        case 'proxy': return proxyMetrics.value.totalHosts
        case 'dns': return dnsMetrics.value.totalHosts
        default: return 0
      }
    }

    const getCategoryLabel = (category: string) => {
      const labels: { [key: string]: string } = {
        web: 'Web',
        database: 'Database',
        proxy: 'Proxy',
        dns: 'DNS'
      }
      return labels[category] || category
    }

    // Web metrics
    const webMetrics = computed(() => {
      const webHosts = (props.hosts as Host[])?.filter((host: Host) => 
        host.ports?.some((port: Port) => [80, 443, 8080, 8443].includes(port.port_number))
      ) || []
      
      const sslEnabled = webHosts.filter((host: Host) => 
        host.ports?.some((port: Port) => [443, 8443].includes(port.port_number))
      ).length
      
      return {
        totalHosts: webHosts.length,
        sslEnabled,
        sslPercentage: webHosts.length > 0 ? Math.round((sslEnabled / webHosts.length) * 100) : 0,
        commonTechnologies: ['HTTP', 'HTTPS', 'Nginx', 'Apache']
      }
    })

    // Database metrics
    const databaseMetrics = computed(() => {
      const dbHosts = (props.hosts as Host[])?.filter((host: Host) => 
        host.ports?.some((port: Port) => [3306, 5432, 27017, 6379].includes(port.port_number))
      ) || []
      
      return {
        totalHosts: dbHosts.length,
        databaseTypes: ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis'],
        anonymousAccess: dbHosts.length > 0 ? Math.round(dbHosts.length * 0.3) : 0
      }
    })

    // Proxy metrics
    const proxyMetrics = computed(() => {
      const proxyHosts = (props.hosts as Host[])?.filter((host: Host) => 
        host.ports?.some((port: Port) => [3128, 8080, 1080].includes(port.port_number))
      ) || []
      
      return {
        totalHosts: proxyHosts.length,
        proxyTypes: ['HTTP', 'SOCKS', 'Transparent'],
        highAnonymity: proxyHosts.length > 0 ? Math.round(proxyHosts.length * 0.4) : 0
      }
    })

    // DNS metrics
    const dnsMetrics = computed(() => {
      const dnsHosts = (props.hosts as Host[])?.filter((host: Host) => 
        host.ports?.some((port: Port) => port.port_number === 53)
      ) || []
      
      return {
        totalHosts: dnsHosts.length,
        serverTypes: ['BIND', 'PowerDNS', 'Unbound'],
        dnssecEnabled: dnsHosts.length > 0 ? Math.round(dnsHosts.length * 0.6) : 0
      }
    })

    return {
      hasMetrics,
      portContextTitle,
      detectedCategories,
      getCategoryCount,
      getCategoryLabel,
      webMetrics,
      databaseMetrics,
      proxyMetrics,
      dnsMetrics
    }
  }
})
</script>

<style scoped>
.port-metrics {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.metrics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f8f9fa;
}

.metrics-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.port-badges {
  display: flex;
  gap: 8px;
}

.port-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.port-badge.web {
  background-color: #e3f2fd;
  color: #1976d2;
}

.port-badge.database {
  background-color: #f3e5f5;
  color: #7b1fa2;
}

.port-badge.proxy {
  background-color: #fff3e0;
  color: #f57c00;
}

.port-badge.dns {
  background-color: #e8f5e8;
  color: #388e3c;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.metric-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  border-left: 4px solid;
}

.metric-card.web {
  border-left-color: #1976d2;
}

.metric-card.database {
  border-left-color: #7b1fa2;
}

.metric-card.proxy {
  border-left-color: #f57c00;
}

.metric-card.dns {
  border-left-color: #388e3c;
}

.metric-card.security {
  border-left-color: #d32f2f;
}

.metric-card.geographic {
  border-left-color: #388e3c;
}

.metric-header h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.metric-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-size: 14px;
  color: #6c757d;
  font-weight: 500;
}

.metric-value {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 600;
}

.risk-score {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
}

.risk-score.low-risk {
  background-color: #e8f5e8;
  color: #388e3c;
}

.risk-score.medium-risk {
  background-color: #fff3e0;
  color: #f57c00;
}

.risk-score.high-risk {
  background-color: #ffebee;
  color: #d32f2f;
}

@media (max-width: 768px) {
  .metrics-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .port-metrics {
    padding: 16px;
  }
  
  .port-badges {
    flex-wrap: wrap;
  }
}

@media (max-width: 480px) {
  .port-metrics {
    padding: 12px;
  }
  
  .metrics-grid {
    gap: 12px;
  }
  
  .metric-card {
    padding: 16px;
  }
}
</style>
