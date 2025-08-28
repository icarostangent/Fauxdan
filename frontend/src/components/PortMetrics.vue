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

      <!-- Security Overview -->
      <div class="metric-card security">
        <div class="metric-header">
          <h4>🛡️ Security Overview</h4>
        </div>
        <div class="metric-content">
          <div class="metric-item">
            <span class="metric-label">Risk Score:</span>
            <span class="metric-value risk-score" :class="getRiskClass(securityMetrics.riskScore)">
              {{ securityMetrics.riskScore }}/10
            </span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Vulnerable Hosts:</span>
            <span class="metric-value">{{ securityMetrics.vulnerableHosts }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Exposed Services:</span>
            <span class="metric-value">{{ securityMetrics.exposedServices }}</span>
          </div>
        </div>
      </div>

      <!-- Geographic Distribution -->
      <div class="metric-card geographic">
        <div class="metric-header">
          <h4>🌍 Geographic Distribution</h4>
        </div>
        <div class="metric-content">
          <div class="metric-item">
            <span class="metric-label">Countries:</span>
            <span class="metric-value">{{ geographicMetrics.countries.length }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Top Region:</span>
            <span class="metric-value">{{ geographicMetrics.topRegion }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Cloud Providers:</span>
            <span class="metric-value">{{ geographicMetrics.cloudProviders.join(', ') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, PropType } from 'vue'
import { Host, Port } from '@/types'

export default defineComponent({
  name: 'PortMetrics',
  
  props: {
    hosts: {
      type: Array as PropType<Host[]>,
      required: true
    },
    searchQuery: {
      type: String,
      default: ''
    }
  },

  setup(props) {
    // Port categorization system
    const PORT_CATEGORIES = {
      web: [80, 443, 8080, 8443, 3000, 8000, 9000, 4000, 5000, 6000],
      database: [3306, 5432, 6379, 27017, 1433, 1521, 5984, 9200, 11211, 2181],
      proxy: [3128, 8080, 8118, 1080, 9050, 9150, 4145, 1080, 1081],
      dns: [53, 5353, 853, 8600],
      mail: [25, 587, 465, 110, 143, 993, 995, 4190],
      ssh: [22, 2222, 2200],
      ftp: [21, 990, 989, 2121],
      rdp: [3389, 3388],
      vnc: [5900, 5901, 5902, 5903],
      telnet: [23, 2323]
    }

    // Detect port categories from search query and hosts data
    const detectedCategories = computed(() => {
      const categories = new Set<string>()
      
      // Check search query for port numbers or keywords
      const query = props.searchQuery.toLowerCase()
      
      // Check for port numbers in search
      Object.entries(PORT_CATEGORIES).forEach(([category, ports]) => {
        if (ports.some(port => query.includes(port.toString()))) {
          categories.add(category)
        }
      })
      
      // Check for keywords in search
      if (query.includes('web') || query.includes('http') || query.includes('https')) {
        categories.add('web')
      }
      if (query.includes('db') || query.includes('database') || query.includes('mysql') || query.includes('postgres')) {
        categories.add('database')
      }
      if (query.includes('proxy') || query.includes('socks')) {
        categories.add('proxy')
      }
      if (query.includes('dns') || query.includes('domain')) {
        categories.add('dns')
      }
      
      // If no specific categories detected, analyze host data
      if (categories.size === 0) {
        props.hosts.forEach(host => {
          host.ports.forEach(port => {
            Object.entries(PORT_CATEGORIES).forEach(([category, ports]) => {
              if (port.port_number && ports.includes(port.port_number)) {
                categories.add(category)
              }
            })
          })
        })
      }
      
      return Array.from(categories)
    })

    // Generate metrics based on detected categories
    const webMetrics = computed(() => {
      const webHosts = props.hosts.filter(host => 
        host.ports.some(port => 
          port.port_number && PORT_CATEGORIES.web.includes(port.port_number)
        )
      )
      
      const sslHosts = webHosts.filter(host => 
        host.ssl_certificates.length > 0
      )
      
      const technologies = new Set<string>()
      webHosts.forEach(host => {
        host.ports.forEach(port => {
          if (port.banner) {
            const banner = port.banner.toLowerCase()
            if (banner.includes('nginx')) technologies.add('Nginx')
            if (banner.includes('apache')) technologies.add('Apache')
            if (banner.includes('iis')) technologies.add('IIS')
            if (banner.includes('node')) technologies.add('Node.js')
            if (banner.includes('python')) technologies.add('Python')
            if (banner.includes('php')) technologies.add('PHP')
          }
        })
      })
      
      return {
        totalHosts: webHosts.length,
        sslEnabled: sslHosts.length,
        sslPercentage: webHosts.length > 0 ? Math.round((sslHosts.length / webHosts.length) * 100) : 0,
        commonTechnologies: Array.from(technologies).slice(0, 3)
      }
    })

    const databaseMetrics = computed(() => {
      const dbHosts = props.hosts.filter(host => 
        host.ports.some(port => 
          port.port_number && PORT_CATEGORIES.database.includes(port.port_number)
        )
      )
      
      const dbTypes = new Set<string>()
      dbHosts.forEach(host => {
        host.ports.forEach(port => {
          if (port.banner) {
            const banner = port.banner.toLowerCase()
            if (banner.includes('mysql')) dbTypes.add('MySQL')
            if (banner.includes('postgresql')) dbTypes.add('PostgreSQL')
            if (banner.includes('redis')) dbTypes.add('Redis')
            if (banner.includes('mongodb')) dbTypes.add('MongoDB')
            if (banner.includes('elasticsearch')) dbTypes.add('Elasticsearch')
          }
        })
      })
      
      return {
        totalHosts: dbHosts.length,
        databaseTypes: Array.from(dbTypes).slice(0, 3),
        anonymousAccess: dbHosts.filter(host => 
          host.ports.some(port => 
            port.banner && port.banner.toLowerCase().includes('anonymous')
          )
        ).length
      }
    })

    const proxyMetrics = computed(() => {
      const proxyHosts = props.hosts.filter(host => 
        host.ports.some(port => 
          port.port_number && PORT_CATEGORIES.proxy.includes(port.port_number)
        )
      )
      
      const proxyTypes = new Set<string>()
      proxyHosts.forEach(host => {
        host.ports.forEach(port => {
          if (port.banner) {
            const banner = port.banner.toLowerCase()
            if (banner.includes('socks')) proxyTypes.add('SOCKS')
            if (banner.includes('http')) proxyTypes.add('HTTP')
            if (banner.includes('transparent')) proxyTypes.add('Transparent')
          }
        })
      })
      
      return {
        totalHosts: proxyHosts.length,
        proxyTypes: Array.from(proxyTypes).slice(0, 3),
        highAnonymity: proxyHosts.filter(host => 
          host.ports.some(port => 
            port.banner && port.banner.toLowerCase().includes('anonymous')
          )
        ).length
      }
    })

    const dnsMetrics = computed(() => {
      const dnsHosts = props.hosts.filter(host => 
        host.ports.some(port => 
          port.port_number && PORT_CATEGORIES.dns.includes(port.port_number)
        )
      )
      
      const serverTypes = new Set<string>()
      dnsHosts.forEach(host => {
        host.ports.forEach(port => {
          if (port.banner) {
            const banner = port.banner.toLowerCase()
            if (banner.includes('bind')) serverTypes.add('BIND')
            if (banner.includes('dnsmasq')) serverTypes.add('dnsmasq')
            if (banner.includes('unbound')) serverTypes.add('Unbound')
          }
        })
      })
      
      return {
        totalHosts: dnsHosts.length,
        serverTypes: Array.from(serverTypes).slice(0, 3),
        dnssecEnabled: dnsHosts.filter(host => 
          host.ports.some(port => 
            port.banner && port.banner.toLowerCase().includes('dnssec')
          )
        ).length
      }
    })

    const securityMetrics = computed(() => {
      const totalHosts = props.hosts.length
      const vulnerableHosts = props.hosts.filter(host => 
        host.score && host.score > 7
      ).length
      
      const exposedServices = props.hosts.filter(host => 
        host.ports.some(port => 
          port.status === 'open' && !host.private
        )
      ).length
      
      const riskScore = Math.round((vulnerableHosts / totalHosts) * 10) || 0
      
      return {
        riskScore,
        vulnerableHosts,
        exposedServices
      }
    })

    const geographicMetrics = computed(() => {
      const countries = new Set<string>()
      const regions = new Map<string, number>()
      const cloudProviders = new Set<string>()
      
      props.hosts.forEach(host => {
        // This would need to be enhanced with actual geographic data
        // For now, we'll simulate with IP-based logic
        if (host.ip) {
          // Simple IP-based country detection (would need real geoip service)
          if (host.ip.startsWith('8.8.')) countries.add('US')
          if (host.ip.startsWith('1.1.')) countries.add('US')
          if (host.ip.startsWith('208.67.')) countries.add('US')
        }
      })
      
      return {
        countries: Array.from(countries),
        topRegion: 'North America',
        cloudProviders: ['AWS', 'Google Cloud', 'Azure']
      }
    })

    const hasMetrics = computed(() => props.hosts.length > 0)
    
    const portContextTitle = computed(() => {
      if (detectedCategories.value.length === 0) return 'All Services Overview'
      if (detectedCategories.value.length === 1) {
        return `${getCategoryLabel(detectedCategories.value[0])} Services`
      }
      return 'Multi-Service Overview'
    })

    const getCategoryLabel = (category: string): string => {
      const labels: Record<string, string> = {
        web: 'Web',
        database: 'Database',
        proxy: 'Proxy',
        dns: 'DNS',
        mail: 'Mail',
        ssh: 'SSH',
        ftp: 'FTP',
        rdp: 'RDP',
        vnc: 'VNC',
        telnet: 'Telnet'
      }
      return labels[category] || category
    }

    const getRiskClass = (score: number): string => {
      if (score <= 3) return 'low-risk'
      if (score <= 6) return 'medium-risk'
      return 'high-risk'
    }

    return {
      detectedCategories,
      webMetrics,
      databaseMetrics,
      proxyMetrics,
      dnsMetrics,
      securityMetrics,
      geographicMetrics,
      hasMetrics,
      portContextTitle,
      getCategoryLabel,
      getRiskClass
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
