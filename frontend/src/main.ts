import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

// Initialize GA4 if available
if (typeof window !== 'undefined' && (window as any).gtag) {
  (window as any).gtag('config', 'GA_MEASUREMENT_ID', {
    page_title: document.title,
    page_location: window.location.href,
  })
}

createApp(App).use(store).use(router).mount('#app')
