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
          @click="handleFirstPage"
          title="Go to first page"
        >
          ««
        </button>
        
        <!-- Previous Page -->
        <button 
          class="pagination-btn"
          :disabled="!hosts?.previous" 
          @click="handlePreviousPage"
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
            @click="handlePageChange(pageNum)"
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
          @click="handleNextPage"
          title="Go to next page"
        >
          »
        </button>
        
        <!-- Last Page -->
        <button 
          class="pagination-btn"
          :disabled="!hosts?.next || hosts?.page === totalPages" 
          @click="handleLastPage"
          title="Go to last page"
        >
          »»
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'
import HostElement from './HostElement.vue'
import { analytics } from '@/services/analytics'

export default defineComponent({
  name: 'HostList',
  
  components: {
    HostElement
  },

  props: {
    hosts: {
      type: Object,
      required: true
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

  setup(props, { emit }) {
    // Track pagination clicks
    const handlePageChange = (page: number) => {
      analytics.trackEvent({
        event: 'pagination',
        category: 'user_interaction',
        action: 'change_page',
        label: `hosts_page_${page}`,
        value: page
      })
      
      emit('page-change', page)
    }

    // Track first page navigation
    const handleFirstPage = () => {
      analytics.trackEvent({
        event: 'pagination',
        category: 'user_interaction',
        action: 'go_to_first_page',
        label: 'hosts_list'
      })
      
      emit('page-change', 1)
    }

    // Track last page navigation
    const handleLastPage = () => {
      const lastPage = props.hosts?.total_pages || 1
      analytics.trackEvent({
        event: 'pagination',
        category: 'user_interaction',
        action: 'go_to_last_page',
        label: `hosts_page_${lastPage}`,
        value: lastPage
      })
      
      emit('page-change', lastPage)
    }

    // Track previous page navigation
    const handlePreviousPage = () => {
      const currentPage = props.hosts?.page || 1
      const prevPage = currentPage - 1
      analytics.trackEvent({
        event: 'pagination',
        category: 'user_interaction',
        action: 'go_to_previous_page',
        label: `hosts_page_${prevPage}`,
        value: prevPage
      })
      
      emit('page-change', prevPage)
    }

    // Track next page navigation
    const handleNextPage = () => {
      const currentPage = props.hosts?.page || 1
      const nextPage = currentPage + 1
      analytics.trackEvent({
        event: 'pagination',
        category: 'user_interaction',
        action: 'go_to_next_page',
        label: `hosts_page_${nextPage}`,
        value: nextPage
      })
      
      emit('page-change', nextPage)
    }

    // Computed properties for pagination
    const totalPages = computed(() => props.hosts?.total_pages || 1)
    const startResult = computed(() => {
      if (!props.hosts?.results?.length) return 0
      return ((props.hosts.page || 1) - 1) * (props.hosts.page_size || 10) + 1
    })
    const endResult = computed(() => {
      if (!props.hosts?.results?.length) return 0
      return startResult.value + props.hosts.results.length - 1
    })

    // Pagination display logic
    const visiblePageNumbers = computed(() => {
      const currentPage = props.hosts?.page || 1
      const total = totalPages.value
      const delta = 2
      
      const range = []
      const rangeWithDots = []
      
      for (let i = Math.max(2, currentPage - delta); i <= Math.min(total - 1, currentPage + delta); i++) {
        range.push(i)
      }
      
      if (currentPage - delta > 2) {
        rangeWithDots.push(1, '...')
      } else {
        rangeWithDots.push(1)
      }
      
      rangeWithDots.push(...range)
      
      if (currentPage + delta < total - 1) {
        rangeWithDots.push('...', total)
      } else {
        rangeWithDots.push(total)
      }
      
      return rangeWithDots.filter(item => item !== 1 || total === 1)
    })

    const showLeftEllipsis = computed(() => {
      const currentPage = props.hosts?.page || 1
      return currentPage - 2 > 1
    })

    const showRightEllipsis = computed(() => {
      const currentPage = props.hosts?.page || 1
      const total = totalPages.value
      return currentPage + 2 < total
    })

    return {
      totalPages,
      startResult,
      endResult,
      visiblePageNumbers,
      showLeftEllipsis,
      showRightEllipsis,
      handlePageChange,
      handleFirstPage,
      handleLastPage,
      handlePreviousPage,
      handleNextPage
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

/* Skeleton loading styles */
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
</style>
