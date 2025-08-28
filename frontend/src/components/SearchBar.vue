<template>
  <div class="search-bar">
    <div class="search-input-container">
      <input 
        type="text" 
        v-model="searchQuery" 
        placeholder="Search ports, IP addresses, or host names..."
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
    
    <!-- Search Examples -->
    <div class="search-examples" v-if="showExamples">
      <div class="examples-header">
        <span class="examples-title">💡 Search Examples:</span>
        <button @click="toggleExamples" class="toggle-examples">Hide</button>
      </div>
      <div class="examples-grid">
        <div class="example-category">
          <h4>🔌 Port Numbers</h4>
          <div class="example-tags">
            <span @click="setSearchQuery('80')" class="example-tag">80</span>
            <span @click="setSearchQuery('443')" class="example-tag">443</span>
            <span @click="setSearchQuery('3306')" class="example-tag">3306</span>
            <span @click="setSearchQuery('22')" class="example-tag">22</span>
            <span @click="setSearchQuery('53')" class="example-tag">53</span>
            <span @click="setSearchQuery('3128')" class="example-tag">3128</span>
          </div>
        </div>
        
        <div class="example-category">
          <h4>🌐 IP Addresses</h4>
          <div class="example-tags">
            <span @click="setSearchQuery('192.168.1.1')" class="example-tag">192.168.1.1</span>
            <span @click="setSearchQuery('10.0.0.1')" class="example-tag">10.0.0.1</span>
            <span @click="setSearchQuery('172.16.0.1')" class="example-tag">172.16.0.1</span>
            <span @click="setSearchQuery('8.8.8.8')" class="example-tag">8.8.8.8</span>
          </div>
        </div>
        
        <div class="example-category">
          <h4>🏷️ Host Names</h4>
          <div class="example-tags">
            <span @click="setSearchQuery('example.com')" class="example-tag">example.com</span>
            <span @click="setSearchQuery('mail.example.com')" class="example-tag">mail.example.com</span>
            <span @click="setSearchQuery('db.example.com')" class="example-tag">db.example.com</span>
            <span @click="setSearchQuery('web.example.com')" class="example-tag">web.example.com</span>
          </div>
        </div>
        
        <div class="example-category">
          <h4>🔍 Common Searches</h4>
          <div class="example-tags">
            <span @click="setSearchQuery('nginx')" class="example-tag">nginx</span>
            <span @click="setSearchQuery('mysql')" class="example-tag">mysql</span>
            <span @click="setSearchQuery('apache')" class="example-tag">apache</span>
            <span @click="setSearchQuery('ssh')" class="example-tag">ssh</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Show Examples Button -->
    <div v-if="!showExamples" class="show-examples-container">
      <button @click="toggleExamples" class="show-examples-btn">
        💡 Show search examples
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
    const showExamples = ref(false)

    const onSearch = () => {
      emit('search', searchQuery.value)
    }

    const toggleExamples = () => {
      showExamples.value = !showExamples.value
    }

    const setSearchQuery = (query: string) => {
      searchQuery.value = query
      emit('search', query)
    }

    // Update searchQuery when initialValue changes
    watch(() => props.initialValue, (newValue) => {
      searchQuery.value = newValue
    })

    return {
      searchQuery,
      showExamples,
      onSearch,
      toggleExamples,
      setSearchQuery
    }
  }
})
</script>

<style scoped>
  .search-bar {
    margin: 1rem 0;
    width: 100%;
  }

  /* Search Examples Styles */
  .search-examples {
    margin-top: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    border: 1px solid #e9ecef;
  }

  .examples-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .examples-title {
    font-weight: 600;
    color: #2c3e50;
    font-size: 14px;
  }

  .toggle-examples {
    background: none;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 4px 12px;
    font-size: 12px;
    color: #6c757d;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .toggle-examples:hover {
    background: #e9ecef;
    border-color: #adb5bd;
  }

  .examples-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }

  .example-category h4 {
    margin: 0 0 8px 0;
    font-size: 13px;
    color: #495057;
    font-weight: 600;
  }

  .example-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .example-tag {
    background: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 16px;
    padding: 4px 12px;
    font-size: 12px;
    color: #495057;
    cursor: pointer;
    transition: all 0.2s ease;
    user-select: none;
  }

  .example-tag:hover {
    background: #007bff;
    color: white;
    border-color: #007bff;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
  }

  .show-examples-container {
    margin-top: 12px;
    text-align: center;
  }

  .show-examples-btn {
    background: none;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    color: #6c757d;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .show-examples-btn:hover {
    background: #f8f9fa;
    border-color: #adb5bd;
    color: #495057;
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
