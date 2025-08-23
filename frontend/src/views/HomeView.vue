<template>
  <div class="home">
    <div class="api-info">
      <h3>API Access</h3>
      <p>You can also access this data directly via our API:</p>
      <ul>
        <li><strong>All Hosts:</strong> <code>GET /api/hosts/?page=1&size=50</code></li>
        <li><strong>Search Hosts:</strong> <code>GET /api/search/?q=YOUR_QUERY&page=1&size=50</code></li>
        <li><strong>Host Details:</strong> <code>GET /api/hosts/HOST_ID/</code></li>
      </ul>
      <p><small>Replace <code>YOUR_QUERY</code> with your search term and <code>HOST_ID</code> with the actual host ID.</small></p>
    </div>
    
    <SearchBar 
      :initial-value="route.query.q?.toString() || ''"
      @search="handleSearch" 
    />
    <HostList 
      :hosts="hosts"
      :loading="loading"
      :error="error"
      @page-change="handlePageChange"
      @page-size-change="handlePageSizeChange"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { useStore } from 'vuex'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HostList from '@/components/HostList.vue'
import SearchBar from '@/components/SearchBar.vue'

export default defineComponent({
  name: 'HomeView',
  
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
    let searchTimeout: ReturnType<typeof setTimeout> | null = null

    const hosts = computed(() => store.state.hosts)

    const loadHosts = async (page?: number) => {
      loading.value = true
      error.value = ''
      try {
        await store.dispatch('fetchHosts', { page })
      } catch (err) {
        error.value = 'Failed to load hosts. Please try again.'
      } finally {
        loading.value = false
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

    const handlePageSizeChange = (newPageSize: number) => {
      // Reset to first page when changing page size
      router.push({
        query: {
          ...route.query,
          page: '1',
          size: newPageSize.toString()
        }
      })
    }

    // Watch for URL parameter changes
    watch(
      () => route.query,
      async (query) => {
        loading.value = true
        error.value = ''
        try {
          const page = query.page ? parseInt(query.page as string) : 1
          const pageSize = query.size ? parseInt(query.size as string) : 50
          const searchQuery = query.q as string | undefined

          if (searchQuery) {
            await store.dispatch('searchHosts', { query: searchQuery, page: page, size: pageSize })
          } else {
            await store.dispatch('fetchHosts', { page, size: pageSize })
          }
        } catch (err) {
          error.value = 'Failed to load hosts. Please try again.'
          console.error('Error loading hosts:', err)
        } finally {
          loading.value = false
        }
      },
      { immediate: true }
    )

    return {
      hosts,
      loading,
      error,
      handleSearch,
      handlePageChange,
      handlePageSizeChange,
      route // Expose route to template
    }
  }
})
</script>

<style scoped>
.home {
  padding: 20px;
}

.api-info {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
  text-align: left;
}

.api-info h3 {
  margin: 0 0 12px 0;
  color: #495057;
  font-size: 18px;
}

.api-info p {
  margin: 0 0 12px 0;
  color: #6c757d;
  line-height: 1.5;
}

.api-info ul {
  margin: 0 0 12px 0;
  padding-left: 20px;
}

.api-info li {
  margin-bottom: 8px;
  color: #495057;
  line-height: 1.4;
}

.api-info code {
  background-color: #e9ecef;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #e83e8c;
}

.api-info small {
  color: #6c757d;
  font-size: 14px;
}
</style>
