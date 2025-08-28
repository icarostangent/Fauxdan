<template>
  <div class="about">
    <SearchBar 
      :initial-value="route.query.q?.toString() || ''"
      @search="handleSearch" 
    />
    
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
    let searchTimeout: ReturnType<typeof setTimeout> | null = null
    
    // Get the global loading setter from parent
    const setGlobalLoading = inject('setGlobalLoading') as ((loading: boolean) => void) | undefined

    const hosts = computed(() => store.state.hosts)

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
      router.push({
        query: {
          ...route.query,
          page: page.toString()
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

    // Cleanup: Reset global loading when component unmounts
    onUnmounted(() => {
      setGlobalLoading?.(false)
    })

    return {
      hosts,
      loading,
      error,
      handleSearch,
      handlePageChange,
      route // Expose route to template
    }
  }
})
</script>

<style scoped>
.about {
  padding: 20px;
}


</style>
