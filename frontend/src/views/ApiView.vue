<template>
  <div class="api-view">
    <div class="container">
      <h1 class="page-title">API Documentation</h1>
      


      <!-- Internet API Section -->
      <section class="api-section">
        <h2 class="section-title">Internet API Endpoints</h2>
        <div class="section-content">
          <p class="section-description">
            All API endpoints are read-only and provide access to discovered network intelligence data.
          </p>
        </div>
        
        <!-- Scans -->
        <div class="endpoint-group">
          <h3 class="endpoint-group-title">Scans</h3>
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="endpoint-url">/api/scans/</span>
              <div class="http-methods">
                <span class="method get">GET</span>
              </div>
            </div>
            <div class="endpoint-body">
              <p class="endpoint-description">Manage network scans and their results.</p>
              <div class="endpoint-details-grid">
                <div class="detail-column">
                  <h4 class="detail-title">Fields:</h4>
                  <ul class="field-list">
                    <li><span class="field-name">scan_uuid</span> - Unique identifier</li>
                    <li><span class="field-name">scan_command</span> - Command executed</li>
                    <li><span class="field-name">start_time</span> - Scan start timestamp</li>
                    <li><span class="field-name">end_time</span> - Scan completion timestamp</li>
                    <li><span class="field-name">status</span> - Current scan status</li>
                    <li><span class="field-name">scan_type</span> - Type of scan performed</li>
                    <li><span class="field-name">user</span> - User who initiated the scan</li>
                  </ul>
                </div>
                <div class="detail-column">
                  <h4 class="detail-title">Example Response:</h4>
                  <pre class="code-example">{
  "scan_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "scan_command": "masscan --target=192.168.1.0/24",
  "start_time": "2024-01-01T00:00:00Z",
  "status": "completed",
  "scan_type": "port_scan"
}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Hosts -->
        <div class="endpoint-group">
          <h3 class="endpoint-group-title">Hosts</h3>
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="endpoint-url">/api/hosts/</span>
              <div class="http-methods">
                <span class="method get">GET</span>
              </div>
            </div>
            <div class="endpoint-body">
              <p class="endpoint-description">Manage discovered hosts and their details.</p>
              <div class="endpoint-details-grid">
                <div class="detail-column">
                  <h4 class="detail-title">Fields:</h4>
                  <ul class="field-list">
                    <li><span class="field-name">ip</span> - IP address</li>
                    <li><span class="field-name">public_host</span> - Related public host</li>
                    <li><span class="field-name">private</span> - Private network flag</li>
                    <li><span class="field-name">scan</span> - Associated scan</li>
                    <li><span class="field-name">last_seen</span> - Last activity timestamp</li>
                    <li><span class="field-name">ports</span> - Associated ports</li>
                    <li><span class="field-name">domains</span> - Associated domains</li>
                    <li><span class="field-name">ssl_certificates</span> - SSL certificate info</li>
                  </ul>
                </div>
                <div class="detail-column">
                  <h4 class="detail-title">Filters:</h4>
                  <ul class="field-list">
                    <li><span class="field-name">ip</span> - Filter by IP address</li>
                    <li><span class="field-name">domains__name</span> - Filter by domain name</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Ports -->
        <div class="endpoint-group">
          <h3 class="endpoint-group-title">Ports</h3>
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="endpoint-url">/api/ports/</span>
              <div class="http-methods">
                <span class="method get">GET</span>
              </div>
            </div>
            <div class="endpoint-body">
              <p class="endpoint-description">Manage discovered ports and their services.</p>
              <div class="endpoint-details-grid">
                <div class="detail-column">
                  <h4 class="detail-title">Fields:</h4>
                  <ul class="field-list">
                    <li><span class="field-name">port_number</span> - Port number (1-65535)</li>
                    <li><span class="field-name">proto</span> - Protocol (TCP/UDP)</li>
                    <li><span class="field-name">status</span> - Port status</li>
                    <li><span class="field-name">last_seen</span> - Last activity timestamp</li>
                    <li><span class="field-name">banner</span> - Service banner information</li>
                    <li><span class="field-name">scan</span> - Associated scan</li>
                    <li><span class="field-name">host</span> - Associated host</li>
                  </ul>
                </div>
                <div class="detail-column">
                  <h4 class="detail-title">Filters:</h4>
                  <ul class="field-list">
                    <li><span class="field-name">port_number</span> - Filter by port number</li>
                    <li><span class="field-name">proto</span> - Filter by protocol</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Domains -->
        <div class="endpoint-group">
          <h3 class="endpoint-group-title">Domains</h3>
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="endpoint-url">/api/domains/</span>
              <div class="http-methods">
                <span class="method get">GET</span>
              </div>
            </div>
            <div class="endpoint-body">
              <p class="endpoint-description">Manage discovered domain names.</p>
              <div class="endpoint-details-grid">
                <div class="detail-column">
                  <h4 class="detail-title">Fields:</h4>
                  <ul class="field-list">
                    <li><span class="field-name">name</span> - Domain name</li>
                    <li><span class="field-name">source</span> - Discovery source</li>
                    <li><span class="field-name">host</span> - Associated host</li>
                  </ul>
                </div>
                <div class="detail-column">
                  <h4 class="detail-title">Filters:</h4>
                  <ul class="field-list">
                    <li><span class="field-name">name</span> - Filter by domain name</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Proxies -->
        <div class="endpoint-group">
          <h3 class="endpoint-group-title">Proxies</h3>
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="endpoint-url">/api/proxies/</span>
              <div class="http-methods">
                <span class="method get">GET</span>
              </div>
            </div>
            <div class="endpoint-body">
              <p class="endpoint-description">Manage discovered proxy servers.</p>
              <div class="endpoint-details-grid">
                <div class="detail-column">
                  <h4 class="detail-title">Fields:</h4>
                  <ul class="field-list">
                    <li><span class="field-name">host_name</span> - Proxy hostname/IP</li>
                    <li><span class="field-name">port_number</span> - Proxy port</li>
                    <li><span class="field-name">proxy_type</span> - Type (S4, S5, HP, HS)</li>
                    <li><span class="field-name">username</span> - Authentication username</li>
                    <li><span class="field-name">password</span> - Authentication password</li>
                    <li><span class="field-name">enabled</span> - Proxy status</li>
                    <li><span class="field-name">dead</span> - Dead proxy flag</li>
                  </ul>
                </div>
                <div class="detail-column">
                  <h4 class="detail-title">Filters:</h4>
                  <ul class="field-list">
                    <li><span class="field-name">host_name</span> - Filter by hostname</li>
                    <li><span class="field-name">port_number</span> - Filter by port</li>
                    <li><span class="field-name">proxy_type</span> - Filter by type</li>
                    <li><span class="field-name">enabled</span> - Filter by status</li>
                    <li><span class="field-name">dead</span> - Filter by dead status</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- DNS Relays -->
        <div class="endpoint-group">
          <h3 class="endpoint-group-title">DNS Relays</h3>
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="endpoint-url">/api/dnsrelays/</span>
              <div class="http-methods">
                <span class="method get">GET</span>
              </div>
            </div>
            <div class="endpoint-body">
              <p class="endpoint-description">Manage discovered DNS relay servers.</p>
              <div class="endpoint-details-grid">
                <div class="detail-column">
                  <h4 class="detail-title">Fields:</h4>
                  <ul class="field-list">
                    <li><span class="field-name">port</span> - Associated port</li>
                  </ul>
                </div>
                <div class="detail-column">
                  <h4 class="detail-title">Note:</h4>
                  <p class="note-text">DNS relays are associated with specific ports and inherit their properties.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Custom Endpoints -->
        <div class="endpoint-group">
          <h3 class="endpoint-group-title">Custom Endpoints</h3>
          


          <!-- Universal Search -->
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="endpoint-url">/api/search/</span>
              <span class="method get">GET</span>
            </div>
            <div class="endpoint-body">
              <p class="endpoint-description">Search across hosts, domains, ports, and protocols.</p>
              <div class="endpoint-details-grid">
                <div class="detail-column">
                  <h4 class="detail-title">Query Parameters:</h4>
                  <ul class="field-list">
                    <li><span class="field-name">q</span> - Search query</li>
                  </ul>
                  <h4 class="detail-title">Search Types:</h4>
                  <ul class="field-list">
                    <li>IP addresses (exact or partial)</li>
                    <li>Domain names</li>
                    <li>Port numbers (1-65535)</li>
                    <li>Protocols (TCP/UDP)</li>
                  </ul>
                </div>
                <div class="detail-column">
                  <h4 class="detail-title">Example Usage:</h4>
                  <pre class="code-example">GET /api/search/?q=192.168.1.1
GET /api/search/?q=example.com
GET /api/search/?q=80
GET /api/search/?q=tcp</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>



      <!-- Response Format Section -->
      <section class="api-section">
        <h2 class="section-title">Response Format</h2>
        <div class="section-content">
          <p class="section-description">All API responses follow a consistent format:</p>
          
          <div class="format-examples">
            <div class="format-example">
              <h3 class="format-title">Success Response</h3>
              <pre class="code-example">{
  "count": 100,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}</pre>
            </div>
            
            <div class="format-example">
              <h3 class="format-title">Error Response</h3>
              <pre class="code-example">{
  "error": "Error message description",
  "detail": "Additional error details"
}</pre>
            </div>
            
                          <div class="format-example">
                <h3 class="format-title">Pagination</h3>
                <p class="format-description">List endpoints support pagination with the following parameters:</p>
                <ul class="field-list">
                  <li><span class="field-name">page</span> - Page number (default: 1)</li>
                </ul>
              </div>
          </div>
        </div>
      </section>

      <!-- Rate Limiting Section -->
      <section class="api-section">
        <h2 class="section-title">Rate Limiting & Best Practices</h2>
        <div class="section-content">
          <div class="practices-grid">
            <div class="practice-item">
              <h3 class="practice-title">Rate Limits</h3>
              <ul class="practice-list">
                <li>• Authentication endpoints: 5 requests per minute</li>
                <li>• API endpoints: 1000 requests per hour</li>
                <li>• Search endpoints: 100 requests per minute</li>
              </ul>
            </div>
            
            <div class="practice-item">
              <h3 class="practice-title">Best Practices</h3>
              <ul class="practice-list">
                <li>• Always include the Authorization header for protected endpoints</li>
                <li>• All endpoints are read-only (GET requests only)</li>
                <li>• Implement proper error handling for all API calls</li>
                <li>• Cache responses when appropriate to reduce server load</li>
                <li>• Use pagination for large result sets</li>
              </ul>
            </div>
            
            <div class="practice-item">
              <h3 class="practice-title">Error Handling</h3>
              <ul class="practice-list">
                <li>• 400: Bad Request - Invalid parameters or data</li>
                <li>• 401: Unauthorized - Missing or invalid authentication</li>
                <li>• 403: Forbidden - Insufficient permissions</li>
                <li>• 404: Not Found - Resource doesn't exist</li>
                <li>• 429: Too Many Requests - Rate limit exceeded</li>
                <li>• 500: Internal Server Error - Server-side issue</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ApiView',
  components: {},
  setup() {
    return {}
  }
})
</script>

<style scoped>
.api-view {
  min-height: 100vh;
  background-color: #f9fafb;
  padding: 20px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #495057;
  margin-bottom: 2rem;
  text-align: left;
}

.api-section {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
  text-align: left;
}

.section-title {
  margin: 0 0 12px 0;
  color: #495057;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 2px solid #007bff;
  padding-bottom: 0.5rem;
}

.section-content {
  color: #6c757d;
}

.section-description {
  margin: 0 0 12px 0;
  color: #6c757d;
  line-height: 1.5;
  font-size: 16px;
}

.code-block {
  background-color: #e9ecef;
  padding: 12px 16px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #e83e8c;
  margin: 12px 0;
  overflow-x: auto;
}

.auth-endpoints {
  margin-top: 16px;
}

.endpoint-item {
  border-left: 4px solid #007bff;
  padding-left: 16px;
  margin-bottom: 16px;
}

.endpoint-title {
  margin: 0 0 8px 0;
  color: #495057;
  font-size: 16px;
  font-weight: 600;
}

.endpoint-path {
  color: #6c757d;
  font-size: 14px;
  margin-bottom: 8px;
  font-family: 'Courier New', monospace;
}

.endpoint-details {
  margin-top: 8px;
}

.field-label {
  display: inline-block;
  background-color: #e3f2fd;
  color: #1976d2;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  margin-right: 8px;
}

.field-value {
  font-size: 14px;
  color: #495057;
}

.endpoint-group {
  margin-bottom: 24px;
}

.endpoint-group-title {
  margin: 0 0 16px 0;
  color: #495057;
  font-size: 16px;
  font-weight: 600;
}

.endpoint-card {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 16px;
}

.endpoint-header {
  background-color: #f8f9fa;
  padding: 16px 20px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.endpoint-url {
  font-family: 'Courier New', monospace;
  font-size: 16px;
  color: #007bff;
  font-weight: 700;
  background-color: #f8f9fa;
  padding: 8px 12px;
  border-radius: 6px;
  border: 2px solid #e9ecef;
  text-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.http-methods {
  display: flex;
  gap: 8px;
}

.method {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
}

.method.get {
  background-color: #dbeafe;
  color: #1e40af;
}

.method.post {
  background-color: #dcfce7;
  color: #166534;
}

.method.put {
  background-color: #fef3c7;
  color: #92400e;
}

.method.delete {
  background-color: #fee2e2;
  color: #991b1b;
}

.endpoint-body {
  padding: 20px;
}

.endpoint-description {
  color: #6c757d;
  margin-bottom: 16px;
  font-size: 14px;
  line-height: 1.5;
}

.endpoint-details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.detail-column {
  min-width: 0;
}

.detail-title {
  font-weight: 600;
  color: #495057;
  margin-bottom: 12px;
  font-size: 14px;
}

.field-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.field-list li {
  margin-bottom: 8px;
  font-size: 14px;
  color: #6c757d;
  line-height: 1.4;
}

.field-name {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #495057;
}

.code-example {
  background-color: #f8f9fa;
  padding: 12px 16px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #495057;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  border: 1px solid #e9ecef;
}

.note-text {
  font-size: 14px;
  color: #6c757d;
  font-style: italic;
  line-height: 1.5;
}

.format-examples {
  display: grid;
  gap: 16px;
}

.format-example {
  background-color: #f8f9fa;
  padding: 16px 20px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.format-title {
  font-weight: 600;
  color: #495057;
  margin-bottom: 12px;
  font-size: 16px;
}

.format-description {
  color: #6c757d;
  margin-bottom: 12px;
  line-height: 1.5;
  font-size: 14px;
}

.practices-grid {
  display: grid;
  gap: 16px;
}

.practice-item {
  background-color: #f8f9fa;
  padding: 16px 20px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.practice-title {
  font-weight: 600;
  color: #495057;
  margin-bottom: 12px;
  font-size: 16px;
}

.practice-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.practice-list li {
  margin-bottom: 8px;
  color: #6c757d;
  line-height: 1.5;
  font-size: 14px;
}

@media (max-width: 768px) {
  .endpoint-details-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .container {
    padding: 0 15px;
  }
  
  .api-section {
    padding: 16px;
  }
  
  .page-title {
    font-size: 2rem;
  }
}
</style>
