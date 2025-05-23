<template>
  <div>
    <SearchBar 
      :initial-value="route.query.q?.toString() || ''"
      @search="handleSearch" 
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
import { defineComponent } from 'vue'
import { useStore } from 'vuex'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HostList from '@/components/HostList.vue'
import SearchBar from '@/components/SearchBar.vue'

export default defineComponent({
  name: 'HostListView',
  
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

    // Watch for URL parameter changes
    watch(
      () => route.query,
      async (query) => {
        loading.value = true
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
      route // Expose route to template
    }
  }
})
</script>