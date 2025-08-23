<template>
  <div>
    <div style="margin-bottom: 16px;">
      <h2>Hosts</h2>
      <p>Showing {{ startResult }}-{{ endResult }} of {{ hosts?.count || 0 }} hosts</p>
    </div>

    <div>
      <div v-if="loading">Loading...</div>
      
      <div v-else-if="error">Error: {{ error }}</div>
      
      <div v-else-if="hosts?.results" 
        style="
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 16px;
          margin-bottom: 16px;
        "
      >
        <HostElement v-for="host in hosts.results" 
          :key="host.ip" 
          :host="host" 
        />
      </div>
    </div>

    <div v-if="hosts?.results?.length" class="pagination-container">
      <div class="pagination-info">
        <span class="page-info">
          Page {{ hosts?.page || 1 }} of {{ totalPages }}
        </span>
        <span class="results-info">
          {{ startResult }}-{{ endResult }} of {{ hosts?.count || 0 }} results
        </span>
      </div>
      
      <div class="pagination-controls">
        <!-- First Page -->
        <button 
          class="pagination-btn"
          :disabled="!hosts?.previous || hosts?.page === 1" 
          @click="$emit('page-change', 1)"
          title="Go to first page"
        >
          ««
        </button>
        
        <!-- Previous Page -->
        <button 
          class="pagination-btn"
          :disabled="!hosts?.previous" 
          @click="$emit('page-change', (hosts?.page || 1) - 1)"
          title="Go to previous page"
        >
          «
        </button>
        
        <!-- Page Numbers -->
        <div class="page-numbers">
          <button 
            v-for="pageNum in visiblePageNumbers" 
            :key="pageNum"
            class="pagination-btn page-number"
            :class="{ active: pageNum === (hosts?.page || 1) }"
            @click="$emit('page-change', pageNum)"
          >
            {{ pageNum }}
          </button>
          
          <!-- Ellipsis for skipped pages -->
          <span v-if="showLeftEllipsis" class="ellipsis">...</span>
          <span v-if="showRightEllipsis" class="ellipsis">...</span>
        </div>
        
        <!-- Next Page -->
        <button 
          class="pagination-btn"
          :disabled="!hosts?.next" 
          @click="$emit('page-change', (hosts?.page || 1) + 1)"
          title="Go to next page"
        >
          »
        </button>
        
        <!-- Last Page -->
        <button 
          class="pagination-btn"
          :disabled="!hosts?.next || hosts?.page === totalPages" 
          @click="$emit('page-change', totalPages)"
          title="Go to last page"
        >
          »»
        </button>
      </div>
      
      <!-- Page Size Selector -->
      <div class="page-size-controls">
        <label for="page-size">Results per page:</label>
        <select 
          id="page-size" 
          v-model="selectedPageSize" 
          @change="handlePageSizeChange"
          class="page-size-select"
        >
          <option value="10">10</option>
          <option value="25">25</option>
          <option value="50">50</option>
          <option value="100">100</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType, computed, ref, watch } from 'vue'
import HostElement from '@/components/HostElement.vue'
import { PaginatedHosts } from '@/types'

export default defineComponent({
  name: 'HostList',
  
  components: {
    HostElement
  },

  props: {
    hosts: {
      type: Object as PropType<PaginatedHosts>,
      required: true,
      default: () => ({
        count: 0,
        next: null,
        previous: null,
        page: 1,
        page_size: 50,
        results: []
      })
    },
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: ''
    }
  },

  emits: ['page-change', 'page-size-change'],

  setup(props, { emit }) {
    const selectedPageSize = ref(props.hosts.page_size || 50)

    // Computed properties for pagination
    const totalPages = computed(() => Math.ceil((props.hosts?.count || 0) / (props.hosts?.page_size || 50)))
    const startResult = computed(() => {
      if (!props.hosts?.results?.length) return 0
      return ((props.hosts.page || 1) - 1) * (props.hosts.page_size || 50) + 1
    })
    const endResult = computed(() => {
      if (!props.hosts?.results?.length) return 0
      return Math.min((props.hosts.page || 1) * (props.hosts.page_size || 50), props.hosts.count || 0)
    })

    // Smart page number display (show current page ± 2, with ellipsis)
    const visiblePageNumbers = computed(() => {
      const currentPage = props.hosts?.page || 1
      const total = totalPages.value
      
      if (total <= 7) {
        return Array.from({ length: total }, (_, i) => i + 1)
      }
      
      if (currentPage <= 4) {
        return [1, 2, 3, 4, 5, '...', total]
      }
      
      if (currentPage >= total - 3) {
        return [1, '...', total - 4, total - 3, total - 2, total - 1, total]
      }
      
      return [1, '...', currentPage - 1, currentPage, currentPage + 1, '...', total]
    })

    const showLeftEllipsis = computed(() => {
      const currentPage = props.hosts?.page || 1
      return currentPage > 4
    })

    const showRightEllipsis = computed(() => {
      const currentPage = props.hosts?.page || 1
      const total = totalPages.value
      return currentPage < total - 3
    })

    const handlePageSizeChange = () => {
      emit('page-size-change', parseInt(selectedPageSize.value.toString()))
    }

    // Watch for changes in hosts.page_size and update selectedPageSize
    watch(() => props.hosts?.page_size, (newSize) => {
      if (newSize) {
        selectedPageSize.value = newSize
      }
    })

    return {
      selectedPageSize,
      totalPages,
      startResult,
      endResult,
      visiblePageNumbers,
      showLeftEllipsis,
      showRightEllipsis,
      handlePageSizeChange
    }
  }
})
</script>

<style scoped>
.pagination-container {
  margin-top: 24px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.pagination-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 14px;
  color: #6c757d;
}

.page-info {
  font-weight: 500;
  color: #495057;
}

.results-info {
  color: #6c757d;
}

.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.pagination-btn {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  background-color: white;
  color: #495057;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  min-width: 40px;
}

.pagination-btn:hover:not(:disabled) {
  background-color: #e9ecef;
  border-color: #adb5bd;
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-btn.active {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
}

.page-numbers {
  display: flex;
  align-items: center;
  gap: 4px;
}

.ellipsis {
  padding: 8px 4px;
  color: #6c757d;
  font-weight: 500;
}

.page-size-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #6c757d;
}

.page-size-select {
  padding: 4px 8px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background-color: white;
  font-size: 14px;
}
</style>
