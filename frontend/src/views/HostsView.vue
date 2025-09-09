<template>
  <div class="hosts-view">
    <!-- Search -->
    <div class="search-section">
      <SearchBar 
        :initial-value="route.query.q?.toString() || ''"
        @search="handleSearch" 
      />
    </div>
    
    <!-- Summary Statistics removed -->
    
    <!-- Port-Specific Metrics Dashboard removed -->
    
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
import { analytics } from '@/services/analytics'
import { Host } from '@/types'

export default defineComponent({
  name: 'AboutView',
  
  components: {
    HostList,
    SearchBar
  },

  setup() {
    const store = useStore()
    const route = useRoute()
    const router = useRouter()
    const loading = ref(false)
    const error = ref('')
    // quick filters removed
    let searchTimeout: ReturnType<typeof setTimeout> | null = null
    
    // Get the global loading setter from parent
    const setGlobalLoading = inject('setGlobalLoading') as ((loading: boolean) => void) | undefined

    const hosts = computed(() => store.state.hosts)
    
    // Computed statistics
    // Summary stats removed

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
    
    // quick filter handler removed

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
      // summary stats removed
      handleSearch,
      handlePageChange,
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

/* quick filters removed */

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
  
  /* quick filters removed */
  
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
