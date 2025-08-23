<template>
  <div>
    <div style="margin-bottom: 16px;">
      <h2>Hosts</h2>
      <p>Showing {{ startResult }}-{{ endResult }} of {{ hosts?.count || 0 }} hosts</p>
    </div>

    <div>
      <div v-if="loading" class="skeleton-loading">
        <div class="skeleton-item" v-for="n in 6" :key="n">
          <div class="skeleton-header">
            <div class="skeleton-ip"></div>
            <div class="skeleton-badge"></div>
          </div>
          <div class="skeleton-ports">
            <div class="skeleton-port" v-for="p in 3" :key="p"></div>
          </div>
          <div class="skeleton-domains">
            <div class="skeleton-domain" v-for="d in 2" :key="d"></div>
          </div>
        </div>
      </div>
      
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
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType, computed } from 'vue'
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

  emits: ['page-change'],

  setup(props) {
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

    return {
      totalPages,
      startResult,
      endResult,
      visiblePageNumbers,
      showLeftEllipsis,
      showRightEllipsis
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
  flex-wrap: wrap;
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
  flex-wrap: wrap;
  justify-content: center;
}

.ellipsis {
  padding: 8px 4px;
  color: #6c757d;
  font-weight: 500;
}

/* Responsive adjustments for small screens */
@media (max-width: 768px) {
  .pagination-container {
    padding: 16px;
    margin-top: 16px;
  }
  
  .pagination-info {
    flex-direction: column;
    gap: 8px;
    text-align: center;
    margin-bottom: 12px;
  }
  
  .pagination-controls {
    gap: 6px;
    margin-bottom: 12px;
  }
  
  .pagination-btn {
    padding: 10px 8px;
    min-width: 36px;
    font-size: 13px;
  }
  
  .page-numbers {
    gap: 3px;
  }
}

@media (max-width: 480px) {
  .pagination-container {
    padding: 12px;
    margin-top: 12px;
  }
  
  .pagination-controls {
    gap: 4px;
    margin-bottom: 8px;
  }
  
  .pagination-btn {
    padding: 8px 6px;
    min-width: 32px;
    font-size: 12px;
  }
  
  /* Hide some pagination buttons on very small screens */
  .pagination-btn:not(.page-number):not(.active) {
    display: none;
  }
  
  /* Show essential navigation buttons */
  .pagination-btn:first-child,
  .pagination-btn:nth-child(2),
  .pagination-btn:nth-last-child(2),
  .pagination-btn:last-child {
    display: flex !important;
  }
  
  .page-numbers {
    gap: 2px;
  }
  
  .ellipsis {
    padding: 6px 2px;
    font-size: 12px;
  }
}

@media (max-width: 360px) {
  .pagination-container {
    padding: 8px;
  }
  
  .pagination-info {
    font-size: 12px;
  }
  
  .pagination-btn {
    padding: 6px 4px;
    min-width: 28px;
    font-size: 11px;
  }
  
  .page-numbers {
    gap: 1px;
  }
}

/* Ensure skeleton loading styles are preserved */
.skeleton-loading {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.skeleton-item {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.skeleton-ip {
  width: 120px;
  height: 20px;
  background: #f3f4f6;
  border-radius: 4px;
}

.skeleton-badge {
  width: 60px;
  height: 16px;
  background: #f3f4f6;
  border-radius: 12px;
}

.skeleton-ports {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.skeleton-port {
  width: 80px;
  height: 24px;
  background: #f3f4f6;
  border-radius: 4px;
}

.skeleton-domains {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-domain {
  width: 100%;
  height: 16px;
  background: #f3f4f6;
  border-radius: 4px;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
