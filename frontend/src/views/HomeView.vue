<template>
  <div class="home">
    <div class="content-container">
      <div class="about-header">
        <h1>Fauxdan</h1>
        <p class="subtitle">Internet Intelligence & Network Discovery</p>
      </div>

      <div class="about-content">
        <section class="about-section">
          <h2>What We Do</h2>
          <p>
            Fauxdan is a comprehensive internet intelligence platform that provides real-time 
            insights into network infrastructure, open ports, domain associations, and SSL certificate 
            information. Our platform helps security researchers, network administrators, and 
            cybersecurity professionals understand the digital landscape.
          </p>
        </section>

        <section class="about-section">
          <h2>Our Mission</h2>
          <p>
            To provide accurate, comprehensive, and accessible internet intelligence data that 
            empowers organizations to make informed decisions about their network security and 
            infrastructure management.
          </p>
        </section>

        <section class="about-section">
          <h2>Key Features</h2>
          <div class="features-grid">
            <div class="feature-card">
              <h3>Host Discovery</h3>
              <p>Comprehensive scanning and identification of network hosts with detailed port information.</p>
            </div>
            <div class="feature-card">
              <h3>Port Analysis</h3>
              <p>Detailed port scanning with protocol detection and service banner extraction.</p>
            </div>
            <div class="feature-card">
              <h3>Domain Intelligence</h3>
              <p>Domain-to-host mapping and source tracking for comprehensive network visibility.</p>
            </div>
            <div class="feature-card">
              <h3>SSL Certificate Data</h3>
              <p>Complete SSL certificate information including validity, issuer details, and fingerprints.</p>
            </div>
          </div>
        </section>

        <section class="about-section">
          <h2>API Access</h2>
          <p>
            All our data is available through our RESTful API, allowing developers and researchers 
            to integrate Fauxdan's intelligence into their own applications and workflows.
          </p>
          <div class="api-example">
            <code>GET /api/hosts/?page=1&size=50</code>
          </div>
        </section>

        <section class="about-section">
          <h2>Contact</h2>
          <p>
            For questions, support, or partnership inquiries, please reach out to our team. 
            We're committed to helping you leverage internet intelligence for better security outcomes.
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'HomeView'
})
</script>

<style scoped>
.home {
  padding: 20px;
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
}

.about-header {
  text-align: center;
  margin-bottom: 48px;
  padding: 40px 0;
  border-bottom: 2px solid #e9ecef;
}

.about-header h1 {
  font-size: 36px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 16px 0;
}

.subtitle {
  font-size: 18px;
  color: #6c757d;
  margin: 0;
  font-weight: 400;
}

.about-content {
  display: grid;
  gap: 32px;
}

.about-section {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 24px;
}

.about-section h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 16px 0;
  border-bottom: 2px solid #007bff;
  padding-bottom: 8px;
}

.about-section p {
  font-size: 16px;
  line-height: 1.6;
  color: #495057;
  margin: 0 0 16px 0;
}

.about-section p:last-child {
  margin-bottom: 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.feature-card {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 20px;
  transition: all 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: #007bff;
  margin: 0 0 12px 0;
}

.feature-card p {
  font-size: 14px;
  line-height: 1.5;
  color: #6c757d;
  margin: 0;
}

.api-example {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 16px;
  margin-top: 16px;
}

.api-example code {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #e83e8c;
  background-color: #e9ecef;
  padding: 4px 8px;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .about-header h1 {
    font-size: 28px;
  }
  
  .subtitle {
    font-size: 16px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
}
</style>
