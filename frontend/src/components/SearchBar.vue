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
}

.search-input {
  width: 100%;
  max-width: 500px;
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: #666;
}
</style>
