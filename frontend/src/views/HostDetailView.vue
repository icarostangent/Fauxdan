<template>
  <div style="padding: 20px;">
    <!-- Loading and Error States -->
    <div v-if="loading" style="text-align: center; padding: 20px;">Loading...</div>
    <div v-else-if="error" style="text-align: center; padding: 20px; color: #ef4444;">{{ error }}</div>
    
    <div v-else-if="host" style="max-width: 1200px; margin: 0 auto;">
      <!-- Header Section -->
      <div style="margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
          <div>
            <h1 style="font-size: 24px; font-weight: 600; margin: 0;">{{ host.ip }}</h1>
            <div style="display: flex; gap: 12px; margin-top: 8px;">
              <span style="
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 14px;
                background-color: #f3f4f6;
                color: #374151;
              ">
                {{ host.private ? 'Private' : 'Public' }}
              </span>
              <span style="font-size: 14px; color: #6b7280;">Last seen: {{ formatLastSeen(host.last_seen) }}</span>
            </div>
          </div>
          <button 
            style="
              padding: 8px 16px;
              background-color: #f3f4f6;
              border: 1px solid #e5e7eb;
              border-radius: 6px;
              font-size: 14px;
              color: #374151;
            "
            @click="$router.go(-1)"
          >
            Back to List
          </button>
        </div>
      </div>

      <!-- Main Content -->
      <div style="display: grid; gap: 24px;">
        <!-- Ports Section -->
        <section style="background: white; border: 1px solid #ddd; border-radius: 8px; padding: 16px;">
          <h2 style="font-size: 18px; font-weight: 600; margin: 0 0 16px 0;">Open Ports</h2>
          <div style="display: grid; gap: 12px;">
            <div v-for="port in host.ports" :key="port.id" 
              style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px;
                background-color: #f9fafb;
                border-radius: 6px;
              "
            >
              <div style="display: flex; gap: 16px; align-items: center;">
                <span style="font-size: 16px; font-weight: 500;">{{ port.port_number }}/{{ port.proto }}</span>
                <span style="
                  padding: 2px 8px;
                  background-color: #e5e7eb;
                  border-radius: 4px;
                  font-size: 14px;
                  color: #374151;
                ">{{ port.status }}</span>
              </div>
              <div style="display: flex; flex-direction: column; align-items: flex-end;">
                <span style="font-size: 12px; color: #6b7280;">Last seen: {{ formatPortDate(port.last_seen) }}</span>
                <span v-if="port.banner" style="font-size: 12px; color: #6b7280; margin-top: 4px;">{{ port.banner }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Domains Section -->
        <section v-if="host.domains.length" style="background: white; border: 1px solid #ddd; border-radius: 8px; padding: 16px;">
          <h2 style="font-size: 18px; font-weight: 600; margin: 0 0 16px 0;">Domains</h2>
          <div style="display: grid; gap: 12px;">
            <div v-for="domain in host.domains" :key="domain.id"
              style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px;
                background-color: #f9fafb;
                border-radius: 6px;
              "
            >
              <span style="font-size: 14px;">{{ domain.name }}</span>
              <span style="
                padding: 2px 8px;
                background-color: #e5e7eb;
                border-radius: 4px;
                font-size: 12px;
                color: #6b7280;
              ">{{ domain.source }}</span>
            </div>
          </div>
        </section>

        <!-- SSL Certificates Section -->
        <section v-if="host.ssl_certificates && host.ssl_certificates.length > 0" style="background: white; border: 1px solid #ddd; border-radius: 8px; padding: 16px; text-align: left;">
          <h2 style="font-size: 18px; font-weight: 600; margin: 0 0 16px 0; text-align: left;">SSL Certificates</h2>
          <div style="display: grid; gap: 12px;">
            <div v-for="cert in host.ssl_certificates" :key="cert.id"
              style="
                padding: 16px;
                background-color: #f9fafb;
                border-radius: 6px;
                border: 1px solid #e5e7eb;
                text-align: left;
              "
            >
              <!-- Subject Info -->
              <div style="margin-bottom: 16px; text-align: left;">
                <h3 style="font-size: 14px; font-weight: 600; color: #374151; margin: 0 0 8px 0; text-align: left;">Subject</h3>
                <div style="display: grid; grid-template-columns: 120px 1fr; gap: 8px; text-align: left;">
                  <div style="font-size: 12px; color: #6b7280; text-align: left;">Common Name</div>
                  <div style="font-size: 12px; text-align: left;">{{ cert.subject_cn || 'N/A' }}</div>
                </div>
              </div>

              <!-- Issuer Info -->
              <div style="margin-bottom: 16px; text-align: left;">
                <h3 style="font-size: 14px; font-weight: 600; color: #374151; margin: 0 0 8px 0; text-align: left;">Issuer</h3>
                <div style="display: grid; grid-template-columns: 120px 1fr; gap: 8px; text-align: left;">
                  <div style="font-size: 12px; color: #6b7280; text-align: left;">Common Name</div>
                  <div style="font-size: 12px; text-align: left;">{{ cert.issuer_cn || 'N/A' }}</div>
                </div>
              </div>

              <!-- Validity -->
              <div style="margin-bottom: 16px; text-align: left;">
                <h3 style="font-size: 14px; font-weight: 600; color: #374151; margin: 0 0 8px 0; text-align: left;">Validity</h3>
                <div style="display: grid; grid-template-columns: 120px 1fr; gap: 8px; text-align: left;">
                  <div style="font-size: 12px; color: #6b7280; text-align: left;">Not Before</div>
                  <div style="font-size: 12px; text-align: left;">{{ formatDate(cert.valid_from) }}</div>
                  <div style="font-size: 12px; color: #6b7280; text-align: left;">Not After</div>
                  <div style="font-size: 12px; text-align: left;">{{ formatDate(cert.valid_until) }}</div>
                </div>
              </div>

              <!-- Certificate Details -->
              <div style="margin-bottom: 16px; text-align: left;">
                <h3 style="font-size: 14px; font-weight: 600; color: #374151; margin: 0 0 8px 0; text-align: left;">Certificate Details</h3>
                <div style="display: grid; grid-template-columns: 120px 1fr; gap: 8px; text-align: left;">
                  <div style="font-size: 12px; color: #6b7280; text-align: left;">Fingerprint</div>
                  <div style="font-size: 12px; font-family: monospace; text-align: left;">{{ cert.fingerprint }}</div>
                  <div style="font-size: 12px; color: #6b7280; text-align: left;">Created</div>
                  <div style="font-size: 12px; text-align: left;">{{ formatDate(cert.created_at) }}</div>
                  <div style="font-size: 12px; color: #6b7280; text-align: left;">Updated</div>
                  <div style="font-size: 12px; text-align: left;">{{ formatDate(cert.updated_at) }}</div>
                </div>
              </div>

              <!-- Serial Number -->
              <div v-if="cert.extensions?.subjectAltName && cert.extensions.subjectAltName.length > 0">
                <h3 style="font-size: 14px; font-weight: 600; color: #374151; margin: 0 0 8px 0;">Alternative Names</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                  <span v-for="(name, index) in cert.extensions.subjectAltName" :key="index"
                    style="
                      font-size: 12px;
                      padding: 2px 8px;
                      background-color: #e5e7eb;
                      border-radius: 4px;
                      color: #374151;
                    "
                  >
                    {{ name }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Additional Info Section -->
        <section style="background: white; border: 1px solid #ddd; border-radius: 8px; padding: 16px;">
          <h2 style="font-size: 18px; font-weight: 600; margin: 0 0 16px 0;">Additional Information</h2>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
            <div style="padding: 12px; background-color: #f9fafb; border-radius: 6px;">
              <div style="font-size: 12px; color: #6b7280; margin-bottom: 4px;">Host ID</div>
              <div style="font-size: 14px;">{{ host.id || 'N/A' }}</div>
            </div>
            <div style="padding: 12px; background-color: #f9fafb; border-radius: 6px;">
              <div style="font-size: 12px; color: #6b7280; margin-bottom: 4px;">Public Host</div>
              <div style="font-size: 14px;">{{ host.public_host ? 'Yes' : 'No' }}</div>
            </div>
            <div style="padding: 12px; background-color: #f9fafb; border-radius: 6px;">
              <div style="font-size: 12px; color: #6b7280; margin-bottom: 4px;">Scan ID</div>
              <div style="font-size: 14px;">{{ host.scan || 'N/A' }}</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
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

    onMounted(() => {
      // Track page view when component mounts
      analytics.trackPageView(`/hosts/${route.params.id}`)
      loadHost()
    })

    return {
      host,
      loading,
      error,
      formatLastSeen,
      formatPortDate,
      formatDate
    }
  }
})
</script>
