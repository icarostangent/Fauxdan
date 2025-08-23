<template>
  <div class="search-bar">
    <div class="search-input-container">
      <input 
        type="text" 
        v-model="searchQuery" 
        placeholder="Search..."
        @input="onSearch"
        @keyup.enter="onSearch"
        class="search-input"
      >
      <button 
        @click="onSearch"
        class="search-button"
        type="button"
        title="Search"
      >
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 21L16.514 16.506L21 21ZM19 10.5C19 15.194 15.194 19 10.5 19C5.806 19 2 15.194 2 10.5C2 5.806 5.806 2 10.5 2C15.194 2 19 5.806 19 10.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
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

.search-input-container {
  position: relative;
  display: flex;
  align-items: center;
  max-width: 500px;
  margin: 0 auto;
}

.search-input {
  width: 100%;
  padding: 0.75rem 3rem 0.75rem 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  box-sizing: border-box;
  border-right: none;
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.search-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

.search-button {
  background-color: #007bff;
  color: white;
  border: 1px solid #007bff;
  border-left: none;
  padding: 0.75rem 1rem;
  border-radius: 0 6px 6px 0;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 3rem;
}

.search-button:hover {
  background-color: #0056b3;
  border-color: #0056b3;
}

.search-button:active {
  background-color: #004085;
  border-color: #004085;
}

.search-icon {
  width: 18px;
  height: 18px;
}

/* Responsive adjustments for small screens */
@media (max-width: 768px) {
  .search-input-container {
    max-width: 100%;
  }
  
  .search-input {
    font-size: 16px; /* Prevents zoom on iOS */
    padding: 0.875rem 3rem 0.875rem 1rem;
  }
  
  .search-button {
    padding: 0.875rem 1rem;
  }
  
  .search-bar {
    margin: 0.75rem 0;
  }
}

@media (max-width: 480px) {
  .search-input {
    padding: 1rem 3rem 1rem 1rem;
    font-size: 16px;
  }
  
  .search-button {
    padding: 1rem;
  }
}
</style>
