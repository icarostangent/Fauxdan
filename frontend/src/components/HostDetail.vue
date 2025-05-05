<template>
  <div 
    @click="$router.push(`/hosts/${host.id}`)"
    style="
      border: 1px solid #ddd; 
      border-radius: 4px; 
      padding: 12px; 
      margin-bottom: 12px; 
      background: white;
      cursor: pointer;
      transition: all 0.2s;
    "
    :style="{
      'box-shadow': hover ? '0 2px 4px rgba(0,0,0,0.1)' : 'none',
      'transform': hover ? 'translateY(-1px)' : 'none'
    }"
    @mouseenter="hover = true"
    @mouseleave="hover = false"
  >
    <!-- Header -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
      <div style="display: flex; align-items: center; gap: 8px;">
        <h3 style="margin: 0; font-size: 16px; font-weight: 600;">{{ host.ip }}</h3>
        <span style="
          padding: 2px 8px; 
          border-radius: 12px; 
          font-size: 12px;
          background-color: #f3f4f6;
          color: #374151;
        ">
          {{ host.private ? 'Private' : 'Public' }}
        </span>
      </div>
      <span style="font-size: 12px; color: #6b7280;">{{ formatLastSeen }}</span>
    </div>

    <!-- Ports Section -->
    <div style="margin-bottom: 8px;">
      <div style="display: flex; flex-wrap: wrap; gap: 6px;">
        <div v-for="port in host.ports" :key="port.id" 
          style="
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            background-color: #f3f4f6;
            border-radius: 4px;
            font-size: 12px;
          "
        >
          <span style="font-weight: 500;">{{ port.port_number }}/{{ port.proto }}</span>
          <span style="color: #6b7280;">{{ port.status }}</span>
          <span style="color: #9ca3af; font-size: 11px;">{{ formatPortDate(port.last_seen) }}</span>
        </div>
      </div>
    </div>

    <!-- Domains Section -->
    <div v-if="host.domains.length" style="border-top: 1px solid #f3f4f6; padding-top: 8px;">
      <div style="display: flex; flex-wrap: wrap; gap: 6px; max-width: 100%; overflow: hidden;">
        <div v-for="domain in host.domains" :key="domain.id"
          style="
            display: inline-flex;
            align-items: center;
            padding: 2px 8px;
            background-color: #f3f4f6;
            border-radius: 4px;
            font-size: 12px;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          "
        >
          <span style="overflow: hidden; text-overflow: ellipsis;">{{ domain.name }}</span>
          <span style="
            margin-left: 4px;
            padding: 0 4px;
            background-color: #e5e7eb;
            border-radius: 4px;
            font-size: 11px;
            color: #6b7280;
            flex-shrink: 0;
          ">
            {{ domain.source }}
          </span>
        </div>
      </div>
    </div>

    <!-- SSL Certificates Section -->
    <div v-if="host.ssl_certificates && host.ssl_certificates.length > 0" class="ssl-section">
      <h3 class="section-title">SSL Certificates</h3>
      <div v-for="cert in host.ssl_certificates" :key="cert.id" class="cert-info">
        <div v-if="cert.subject?.CN" class="cert-detail">
          <span class="label">Subject:</span>
          <span class="value">{{ cert.subject.CN }}</span>
        </div>
        <div v-if="cert.issuer?.O" class="cert-detail">
          <span class="label">Issuer:</span>
          <span class="value">{{ cert.issuer.O }}</span>
        </div>
        <div class="cert-detail">
          <span class="label">Valid Until:</span>
          <span class="value">{{ formatDate(cert.not_after) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType, computed, ref } from 'vue'
import { useRouter } from 'vue-router'

interface Port {
  id: number | null
  host: string
  port_number: number | null
  proto: string
  status: string
  banner: string | null
  last_seen: string  // Format: "2024-12-08T02:47:00.650710Z"
  scan: number | null
}

interface Domain {
  id: number
  host: string
  name: string
  source: string
}

interface Host {
  id: number | null
  ports: Port[]
  domains: Domain[]
  ssl_certificates: any[]
  ip: string
  private: boolean | null
  last_seen: string | null
  public_host: boolean | null
  scan: number | null
}

export default defineComponent({
  name: 'Host',
  
  props: {
    host: {
      type: Object as PropType<Host>,
      required: true
    }
  },

  setup(props) {
    const router = useRouter()
    const hover = ref(false)

    const formatLastSeen = computed(() => {
      if (!props.host.last_seen) return 'Never seen'
      return formatPortDate(props.host.last_seen)
    })

    const formatPortDate = (dateStr: string) => {
      const date = new Date(dateStr)
      const now = new Date()
      const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
      
      if (diffInHours < 24) {
        return `${Math.round(diffInHours)} hours ago`
      } else {
        const days = Math.floor(diffInHours / 24)
        return `${days} days ago`
      }
    }

    const formatDate = (dateStr: string) => {
      const date = new Date(dateStr)
      return date.toLocaleDateString()
    }

    return {
      formatLastSeen,
      formatPortDate,
      formatDate,
      hover
    }
  }
})
</script>

<style scoped>
.ssl-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.cert-info {
  background-color: #f9fafb;
  border-radius: 4px;
  padding: 8px;
  margin-bottom: 8px;
}

.cert-detail {
  display: flex;
  font-size: 12px;
  margin-bottom: 4px;
}

.cert-detail:last-child {
  margin-bottom: 0;
}

.label {
  color: #6b7280;
  width: 80px;
  flex-shrink: 0;
}

.value {
  color: #374151;
  word-break: break-all;
}
</style>
