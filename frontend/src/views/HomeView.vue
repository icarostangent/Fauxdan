<template>
  <div class="home">
    <div class="hero-section">
      <div class="hero-content">
        <div class="brand-mark">
          <div class="logo-symbol">F</div>
        </div>
        <h1 class="hero-title">FAUXDAN</h1>
        <p class="hero-subtitle">Elite Internet Intelligence</p>
        <div class="hero-divider"></div>
        <p class="hero-description">
          Access to the most comprehensive network reconnaissance data available. 
          Not for the uninitiated.
        </p>
        <div class="access-indicator">
          <span class="status-dot"></span>
          <span class="status-text">ACCESS GRANTED</span>
        </div>
      </div>
    </div>

    <div class="content-container">
      <section class="exclusive-section">
        <h2>Exclusive Intelligence</h2>
        <p class="section-intro">
          While others scrape the surface, we penetrate the depths. 
          Our platform provides unprecedented access to the hidden infrastructure 
          that powers the digital world.
        </p>
        
        <div class="capabilities-grid">
          <div class="capability-card">
            <div class="capability-icon">🔍</div>
            <h3>Host Enumeration</h3>
            <p>Comprehensive discovery of network assets with surgical precision. 
               Every port, every service, every vulnerability exposed.</p>
          </div>
          
          <div class="capability-card">
            <div class="capability-icon">🌐</div>
            <h3>Domain Intelligence</h3>
            <p>Uncover the hidden connections between domains and infrastructure. 
               See what others cannot see.</p>
          </div>
          
          <div class="capability-card">
            <div class="capability-icon">🔐</div>
            <h3>SSL Certificate Analysis</h3>
            <p>Decrypt the security posture of every endpoint. 
               Validity, issuer chains, and cryptographic fingerprints.</p>
          </div>
          
          <div class="capability-card">
            <div class="capability-icon">⚡</div>
            <h3>Real-time Scanning</h3>
            <p>Live intelligence that never sleeps. 
               Continuous monitoring of the digital battlefield.</p>
          </div>
        </div>
      </section>

      <section class="api-section">
        <h2>API Access</h2>
        <p class="api-intro">
          Raw data for those who demand it. Our RESTful API provides direct access 
          to the intelligence that powers elite security operations.
        </p>
        
        <div class="api-examples">
          <div class="api-example">
            <span class="method">GET</span>
            <code>/api/hosts/?page=1&size=50</code>
            <span class="description">Retrieve host intelligence</span>
          </div>
          
          <div class="api-example">
            <span class="method">GET</span>
            <code>/api/search/?q=YOUR_QUERY&page=1</code>
            <span class="description">Advanced host discovery</span>
          </div>
          
          <div class="api-example">
            <span class="method">GET</span>
            <code>/api/hosts/HOST_ID/</code>
            <span class="description">Detailed host analysis</span>
          </div>
        </div>
      </section>

      <section class="exclusivity-section">
        <h2>Why Fauxdan?</h2>
        <div class="exclusivity-grid">
          <div class="exclusivity-item">
            <h3>Unparalleled Depth</h3>
            <p>We don't just scan ports—we map entire attack surfaces. 
               Every piece of intelligence is curated for maximum operational value.</p>
          </div>
          
          <div class="exclusivity-item">
            <h3>Elite Performance</h3>
            <p>Built for professionals who cannot afford delays. 
               Sub-second response times, even with millions of data points.</p>
          </div>
          
          <div class="exclusivity-item">
            <h3>Continuous Intelligence</h3>
            <p>Our scanners never rest. Real-time updates ensure you're always 
               working with the most current intelligence available.</p>
          </div>
        </div>
      </section>

      <section class="cta-section">
        <h2>Ready to Access Elite Intelligence?</h2>
        <p>Begin your reconnaissance operations now.</p>
        <div class="cta-buttons">
          <button class="cta-primary" @click="navigateToSearch">Start Searching</button>
          <button class="cta-secondary" @click="navigateToAPI">API Documentation</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { analytics } from '@/services/analytics'

export default defineComponent({
  name: 'HomeView',
  
  setup() {
    const router = useRouter()
    const hasTracked = ref(false) // Prevent multiple tracking calls
    
    onMounted(() => {
      // Only track once per component mount
      if (!hasTracked.value) {
        analytics.trackPageView('/home')
        analytics.trackEvent({
          event: 'hero_view',
          category: 'engagement',
          action: 'hero_section_view'
        })
        hasTracked.value = true
      }
    })
    
    const navigateToSearch = () => {
      analytics.trackEvent({
        event: 'cta_click',
        category: 'conversion',
        action: 'search_button_click',
        label: 'Start Searching'
      })
      router.push('/hosts')
    }
    
    const navigateToAPI = () => {
      analytics.trackEvent({
        event: 'cta_click',
        category: 'conversion',
        action: 'api_button_click',
        label: 'API Documentation'
      })
      router.push('/hosts')
    }
    
    return {
      navigateToSearch,
      navigateToAPI
    }
  }
})
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0f0f0f 100%);
  color: #ffffff;
}

.hero-section {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 80%, rgba(0, 123, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(138, 43, 226, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.hero-content {
  z-index: 2;
  max-width: 800px;
  padding: 0 20px;
}

.brand-mark {
  margin-bottom: 30px;
}

.logo-symbol {
  width: 80px;
  height: 80px;
  margin: 0 auto;
  background: linear-gradient(135deg, #007bff, #8a2be2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 900;
  color: white;
  box-shadow: 0 0 30px rgba(0, 123, 255, 0.5);
}

.hero-title {
  font-size: 64px;
  font-weight: 900;
  letter-spacing: 8px;
  margin: 0 0 20px 0;
  background: linear-gradient(135deg, #ffffff, #007bff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 24px;
  font-weight: 300;
  color: #8a8a8a;
  margin: 0 0 30px 0;
  letter-spacing: 3px;
}

.hero-divider {
  width: 100px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #007bff, transparent);
  margin: 0 auto 30px auto;
}

.hero-description {
  font-size: 18px;
  line-height: 1.6;
  color: #cccccc;
  margin: 0 0 40px 0;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.access-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px 32px;
  background: rgba(0, 123, 255, 0.1);
  border: 1px solid rgba(0, 123, 255, 0.3);
  border-radius: 50px;
  width: fit-content;
  margin: 0 auto;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #00ff00;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-text {
  font-size: 14px;
  font-weight: 600;
  color: #00ff00;
  letter-spacing: 1px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.content-container {
  width: 100%;
  margin: 0;
  padding: 80px 0;
}

.exclusive-section,
.api-section,
.exclusivity-section,
.cta-section {
  max-width: 1200px;
  margin: 0 auto 100px auto;
  padding: 0 20px;
}

.exclusive-section h2 {
  font-size: 36px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 20px 0;
  background: linear-gradient(135deg, #ffffff, #007bff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.section-intro {
  font-size: 18px;
  line-height: 1.6;
  color: #cccccc;
  text-align: center;
  max-width: 800px;
  margin: 0 auto 60px auto;
}

.capabilities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 30px;
}

.capability-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.capability-card:hover {
  transform: translateY(-5px);
  border-color: rgba(0, 123, 255, 0.5);
  box-shadow: 0 20px 40px rgba(0, 123, 255, 0.2);
}

.capability-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.capability-card h3 {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 15px 0;
  color: #ffffff;
}

.capability-card p {
  font-size: 14px;
  line-height: 1.6;
  color: #aaaaaa;
  margin: 0;
}

.api-section h2 {
  font-size: 36px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 20px 0;
  background: linear-gradient(135deg, #ffffff, #007bff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.api-intro {
  font-size: 18px;
  line-height: 1.6;
  color: #cccccc;
  text-align: center;
  max-width: 800px;
  margin: 0 auto 60px auto;
}

.api-examples {
  display: grid;
  gap: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.api-example {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.api-example:hover {
  border-color: rgba(0, 123, 255, 0.5);
  background: rgba(0, 123, 255, 0.05);
}

.method {
  background: #007bff;
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  min-width: 60px;
  text-align: center;
}

.api-example code {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #00ff00;
  background: rgba(0, 0, 0, 0.3);
  padding: 8px 12px;
  border-radius: 4px;
  flex: 1;
}

.description {
  font-size: 14px;
  color: #aaaaaa;
  min-width: 120px;
}

.exclusivity-section h2 {
  font-size: 36px;
  font-weight: 700;
  text-align: center;
  margin: 0 0 20px 0;
  background: linear-gradient(135deg, #ffffff, #007bff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.exclusivity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 40px;
}

.exclusivity-item {
  text-align: center;
}

.exclusivity-item h3 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 20px 0;
  color: #ffffff;
}

.exclusivity-item p {
  font-size: 16px;
  line-height: 1.6;
  color: #cccccc;
  margin: 0;
}

.cta-section {
  text-align: center;
  padding: 80px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.cta-section h2 {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 20px 0;
  background: linear-gradient(135deg, #ffffff, #007bff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.cta-section p {
  font-size: 18px;
  color: #cccccc;
  margin: 0 0 40px 0;
}

.cta-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.cta-primary, .cta-secondary {
  padding: 16px 32px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 180px;
}

.cta-primary {
  background: linear-gradient(135deg, #007bff, #8a2be2);
  color: white;
}

.cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0, 123, 255, 0.3);
}

.cta-secondary {
  background: transparent;
  color: #007bff;
  border: 2px solid #007bff;
}

.cta-secondary:hover {
  background: rgba(0, 123, 255, 0.1);
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 48px;
    letter-spacing: 6px;
  }
  
  .hero-subtitle {
    font-size: 20px;
  }
  
  .capabilities-grid {
    grid-template-columns: 1fr;
  }
  
  .exclusivity-grid {
    grid-template-columns: 1fr;
  }
  
  .cta-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .api-example {
    flex-direction: column;
    text-align: center;
    gap: 15px;
  }
}
</style>
