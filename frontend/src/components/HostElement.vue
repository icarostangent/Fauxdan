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
        <span class="privacy-badge" style="text-align: left;">{{ host.private ? 'Private' : 'Public' }}</span>
        <span class="last-seen" style="text-align: left;">Last seen: {{ formatLastSeen(host.last_seen) }}</span>
      </div>
    </div>

    <!-- Ports -->
    <div v-if="host.ports.length" class="ports-section">
      <h4 class="section-title" style="text-align: left;">Open Ports</h4>
      <div class="ports-grid">
        <div v-for="port in host.ports" :key="port.id" class="port-item" style="text-align: left;">
          <span class="port-number" style="text-align: left;">{{ port.port_number }}/{{ port.proto }}</span>
          <span class="port-status" style="text-align: left;">{{ port.status }}</span>
        </div>
      </div>
    </div>

    <!-- Domains -->
    <div v-if="host.domains.length" class="domains-section">
      <h4 class="section-title" style="text-align: left;">Domains</h4>
      <div class="domains-list">
        <div v-for="domain in host.domains" :key="domain.id" class="domain-item" style="justify-content: flex-start;">
          <span class="domain-name" style="text-align: left;">{{ domain.name }}</span>
          <span class="domain-source" style="text-align: left; margin-left: auto;">{{ domain.source }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType, ref } from 'vue'
import { Host } from '@/types'
import { formatLastSeen, formatDate, formatPortDate } from '@/utils/date'
import { useRouter } from 'vue-router'

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
        router.push(`/hosts/${props.host.id}`)
      }
    }

    return {
      hover,
      navigateToHost,
      formatLastSeen,
      formatPortDate,
      formatDate
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
  background-color: #f3f4f6;
  border-radius: 12px;
  font-size: 12px;
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
</style>
