<template>
  <nav>
    <div class="nav-container">
      <div class="brand">
        <h1 class="brand-name">Fauxdan</h1>
        <span class="brand-tagline">Not Shodan</span>
      </div>
      <div class="nav-links">
        <router-link to="/" exact>Home</router-link>
        <router-link to="/hosts">Hosts</router-link>
        <router-link to="/blog" class="nav-link">Blog</router-link>
        <router-link to="/api">API</router-link>
      </div>
    </div>
    <!-- Animated Loading Bar -->
    <div class="loading-bar" :class="{ 'loading': isLoading }">
      <div class="loading-progress"></div>
    </div>
  </nav>
  <div class="nav-spacer"></div>
  <router-view/>
</template>

<script>
import { ref, provide, onMounted } from 'vue'

export default {
  name: 'App',
  setup() {
    const isLoading = ref(false)
    
    // Provide loading state to child components
    provide('setGlobalLoading', (loading) => {
      isLoading.value = loading
    })
    
    return {
      isLoading
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background-color: #1a1a1a;
  border-bottom: 2px solid #007bff;
  padding: 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.brand {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 12px 0;
}

.brand-name {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #007bff;
  letter-spacing: -0.5px;
}

.brand-tagline {
  font-size: 12px;
  color: #6c757d;
  font-weight: 400;
  margin-top: -2px;
}

.nav-links {
  display: flex;
  align-items: center;
}

.nav-links a {
  font-weight: 500;
  color: #ffffff;
  text-decoration: none;
  padding: 12px 20px;
  border-radius: 6px;
  transition: all 0.2s ease;
  font-size: 16px;
}

.nav-links a:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.nav-links a.router-link-active {
  background-color: #007bff;
  color: white;
}

.nav-spacer {
  height: 80px; /* Adjust this value based on your navbar height */
}

/* Loading Bar Styles */
.loading-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background-color: transparent;
  overflow: hidden;
  transition: background-color 0.3s ease;
}

.loading-bar.loading {
  background-color: rgba(0, 123, 255, 0.2);
}

.loading-progress {
  height: 100%;
  background: linear-gradient(90deg, #007bff, #0056b3, #007bff);
  background-size: 200% 100%;
  width: 100%;
  transform: translateX(-100%);
  transition: transform 0.3s ease;
}

.loading-bar.loading .loading-progress {
  animation: loading-slide 1.5s ease-in-out infinite;
}

@keyframes loading-slide {
  0% {
    transform: translateX(-100%);
  }
  50% {
    transform: translateX(0%);
  }
  100% {
    transform: translateX(100%);
  }
}
</style>
