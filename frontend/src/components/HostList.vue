<template>
  <div>
    <div style="margin-bottom: 16px;">
      <h2>Hosts</h2>
      <p>Showing {{ hosts?.results?.length || 0 }} of {{ hosts?.count || 0 }} hosts</p>
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

    <div v-if="hosts?.results?.length" style="margin-top: 16px;">
      <span>
        Page {{ hosts?.page || 1 }} of {{ Math.ceil((hosts?.count || 0) / (hosts?.page_size || 50)) }}
      </span>
      
      <div>
        <button 
          :disabled="!hosts?.previous" 
          @click="$emit('page-change', (hosts?.page || 1) - 1)"
        >
          Previous
        </button>
        
        <button 
          :disabled="!hosts?.next" 
          @click="$emit('page-change', (hosts?.page || 1) + 1)"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue'
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

  emits: ['page-change']
})
</script>
