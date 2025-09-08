<template>
  <div class="hosts-view">
    <!-- Search and Filters -->
    <div class="search-section">
      <SearchBar 
        :initial-value="route.query.q?.toString() || ''"
        @search="handleSearch" 
      />
      
      <!-- Quick Filters -->
      <div class="quick-filters">
        <button 
          class="filter-btn" 
          :class="{ active: activeFilter === 'all' }"
          @click="setFilter('all')"
        >
          All ({{ hosts.count }})
        </button>
        <button 
          class="filter-btn" 
          :class="{ active: activeFilter === 'public' }"
          @click="setFilter('public')"
        >
          Public ({{ publicHostsCount }})
        </button>
        <button 
          class="filter-btn" 
          :class="{ active: activeFilter === 'private' }"
          @click="setFilter('private')"
        >
          Private ({{ privateHostsCount }})
        </button>
        <button 
          class="filter-btn" 
          :class="{ active: activeFilter === 'with-ssl' }"
          @click="setFilter('with-ssl')"
        >
          With SSL ({{ sslHostsCount }})
        </button>
        <button 
          class="filter-btn" 
          :class="{ active: activeFilter === 'with-domains' }"
          @click="setFilter('with-domains')"
        >
          With Domains ({{ domainHostsCount }})
        </button>
      </div>
    </div>
    
    <!-- Summary Statistics -->
    <div class="summary-stats" v-if="hosts.results?.length">
      <div class="stat-card">
        <div class="stat-icon">🌐</div>
        <div class="stat-content">
          <div class="stat-number">{{ hosts.count.toLocaleString() }}</div>
          <div class="stat-label">Total Hosts</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔓</div>
        <div class="stat-content">
          <div class="stat-number">{{ publicHostsCount.toLocaleString() }}</div>
          <div class="stat-label">Public</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔒</div>
        <div class="stat-content">
          <div class="stat-number">{{ privateHostsCount.toLocaleString() }}</div>
          <div class="stat-label">Private</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔐</div>
        <div class="stat-content">
          <div class="stat-number">{{ sslHostsCount.toLocaleString() }}</div>
          <div class="stat-label">With SSL</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🌍</div>
        <div class="stat-content">
          <div class="stat-number">{{ domainHostsCount.toLocaleString() }}</div>
          <div class="stat-label">With Domains</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔌</div>
        <div class="stat-content">
          <div class="stat-number">{{ totalPorts.toLocaleString() }}</div>
          <div class="stat-label">Total Ports</div>
        </div>
      </div>
    </div>
    
    <!-- Port-Specific Metrics Dashboard -->
    <PortMetrics 
      :hosts="hosts.results"
      :search-query="route.query.q?.toString() || ''"
    />
    
    <HostList 
      :hosts="hosts"
      :loading="loading"
      :error="error"
      @page-change="handlePageChange"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, inject } from 'vue'
import { useStore } from 'vuex'
import { computed, ref, watch, onUnmounted, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HostList from '@/components/HostList.vue'
import SearchBar from '@/components/SearchBar.vue'
import PortMetrics from '@/components/PortMetrics.vue'
import { analytics } from '@/services/analytics'
import { Host } from '@/types'

export default defineComponent({
  name: 'AboutView',
  
  components: {
    HostList,
    SearchBar,
    PortMetrics
  },

  setup() {
    const store = useStore()
    const route = useRoute()
    const router = useRouter()
    const loading = ref(false)
    const error = ref('')
    const activeFilter = ref('all')
    let searchTimeout: ReturnType<typeof setTimeout> | null = null
    
    // Get the global loading setter from parent
    const setGlobalLoading = inject('setGlobalLoading') as ((loading: boolean) => void) | undefined

    const hosts = computed(() => store.state.hosts)
    
    // Computed statistics
    const publicHostsCount = computed(() => {
      return hosts.value.results?.filter((host: Host) => !host.private).length || 0
    })
    
    const privateHostsCount = computed(() => {
      return hosts.value.results?.filter((host: Host) => host.private).length || 0
    })
    
    const sslHostsCount = computed(() => {
      return hosts.value.results?.filter((host: Host) => host.ssl_certificates?.length).length || 0
    })
    
    const domainHostsCount = computed(() => {
      return hosts.value.results?.filter((host: Host) => host.domains?.length).length || 0
    })
    
    const totalPorts = computed(() => {
      return hosts.value.results?.reduce((total: number, host: Host) => total + (host.ports?.length || 0), 0) || 0
    })

    const loadHosts = async (page?: number) => {
      loading.value = true
      setGlobalLoading?.(true)
      error.value = ''
      try {
        await store.dispatch('fetchHosts', { page })
      } catch (err) {
        error.value = 'Failed to load hosts. Please try again.'
      } finally {
        loading.value = false
        setGlobalLoading?.(false)
      }
    }

    const handleSearch = (query: string) => {
      if (searchTimeout) {
        clearTimeout(searchTimeout)
      }

      searchTimeout = setTimeout(() => {
        // Track search event
        analytics.trackEvent({
          event: 'search',
          category: 'user_interaction',
          action: 'search_hosts',
          label: query || 'empty_search'
        })

        // Update URL with search query
        router.push({
          query: {
            ...route.query,
            q: query || undefined,
            page: undefined // Reset to first page on new search
          }
        })
      }, 300) // Debounce search for 300ms
    }

    const handlePageChange = (page: number) => {
      // Track pagination event
      analytics.trackEvent({
        event: 'pagination',
        category: 'user_interaction',
        action: 'change_page',
        label: `page_${page}`,
        value: page
      })

      router.push({
        query: {
          ...route.query,
          page: page.toString()
        }
      })
    }
    
    const setFilter = (filter: string) => {
      activeFilter.value = filter
      
      // Track filter event
      analytics.trackEvent({
        event: 'filter',
        category: 'user_interaction',
        action: 'set_filter',
        label: filter
      })
      
      // Update URL with filter
      router.push({
        query: {
          ...route.query,
          filter: filter === 'all' ? undefined : filter,
          page: undefined // Reset to first page
        }
      })
    }

    // Watch for URL parameter changes
    watch(
      () => route.query,
      async (query: Record<string, any>) => {
        loading.value = true
        setGlobalLoading?.(true)
        error.value = ''
        try {
          const page = query.page ? parseInt(query.page as string) : 1
          const searchQuery = query.q as string | undefined

          if (searchQuery) {
            await store.dispatch('searchHosts', { query: searchQuery, page: page })
          } else {
            await store.dispatch('fetchHosts', { page })
          }
        } catch (err) {
          error.value = 'Failed to load hosts. Please try again.'
          console.error('Error loading hosts:', err)
        } finally {
          loading.value = false
          setGlobalLoading?.(false)
        }
      },
      { immediate: true }
    )

    // Track page view when component mounts
    onMounted(() => {
      analytics.trackPageView('/hosts')
    })

    // Cleanup: Reset global loading when component unmounts
    onUnmounted(() => {
      setGlobalLoading?.(false)
    })

    return {
      hosts,
      loading,
      error,
      activeFilter,
      publicHostsCount,
      privateHostsCount,
      sslHostsCount,
      domainHostsCount,
      totalPorts,
      handleSearch,
      handlePageChange,
      setFilter,
      route // Expose route to template
    }
  }
})
</script>

<style scoped>
.hosts-view {
  padding: 20px;
}

.search-section {
  margin-bottom: 24px;
}

.quick-filters {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  background: white;
  color: #374151;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.filter-btn.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  border-radius: 8px;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

@media (max-width: 768px) {
  .hosts-view {
    padding: 16px;
  }
  
  .quick-filters {
    flex-direction: column;
  }
  
  .filter-btn {
    width: 100%;
    text-align: center;
  }
  
  .summary-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    padding: 16px;
  }
  
  .stat-card {
    padding: 12px;
  }
  
  .stat-icon {
    font-size: 20px;
    width: 32px;
    height: 32px;
  }
  
  .stat-number {
    font-size: 18px;
  }
}

@media (max-width: 480px) {
  .summary-stats {
    grid-template-columns: 1fr;
  }
}
</style>
