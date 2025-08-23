<template>
  <div class="search-bar">
    <input 
      type="text" 
      v-model="searchQuery" 
      placeholder="Search..."
      @input="onSearch"
      class="search-input"
    >
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch } from 'vue'

export default defineComponent({
  name: 'SearchBar',

  props: {
    initialValue: {
      type: String,
      default: ''
    }
  },

  setup(props, { emit }) {
    const searchQuery = ref(props.initialValue)

    const onSearch = () => {
      emit('search', searchQuery.value)
    }

    // Update searchQuery when initialValue changes
    watch(() => props.initialValue, (newValue) => {
      searchQuery.value = newValue
    })

    return {
      searchQuery,
      onSearch
    }
  }
})
</script>

<style scoped>
.search-bar {
  margin: 1rem 0;
  width: 100%;
}

.search-input {
  width: 100%;
  max-width: 500px;
  padding: 0.75rem 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

/* Responsive adjustments for small screens */
@media (max-width: 768px) {
  .search-input {
    max-width: 100%;
    font-size: 16px; /* Prevents zoom on iOS */
    padding: 0.875rem 1rem;
  }
  
  .search-bar {
    margin: 0.75rem 0;
  }
}

@media (max-width: 480px) {
  .search-input {
    padding: 1rem;
    font-size: 16px;
  }
}
</style>
