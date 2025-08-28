/**
 * Port-Specific Metrics System Demo
 * 
 * This script demonstrates how the new metrics system works
 * with different types of search queries and host data.
 */

// Sample host data for demonstration
const sampleHosts = [
  {
    id: 1,
    ip: "192.168.1.100",
    ports: [
      { port_number: 80, status: "open", banner: "nginx/1.18.0" },
      { port_number: 443, status: "open", banner: "nginx/1.18.0" }
    ],
    ssl_certificates: [
      { subject_cn: "example.com", valid_until: "2025-12-31" }
    ],
    score: 3,
    private: false
  },
  {
    id: 2,
    ip: "10.0.0.50",
    ports: [
      { port_number: 3306, status: "open", banner: "mysql 8.0.26" },
      { port_number: 22, status: "open", banner: "OpenSSH 8.2p1" }
    ],
    ssl_certificates: [],
    score: 8,
    private: true
  },
  {
    id: 3,
    ip: "172.16.0.25",
    ports: [
      { port_number: 3128, status: "open", banner: "socks5 proxy" },
      { port_number: 53, status: "open", banner: "bind 9.16.1" }
    ],
    ssl_certificates: [],
    score: 6,
    private: false
  }
];

// Demo search queries
const demoQueries = [
  "80",
  "443", 
  "nginx",
  "3306",
  "mysql",
  "3128",
  "192.168.1.1",
  "example.com",
  "53",
  "ssh",
  "apache"
];

// Port categorization system (same as in component)
const PORT_CATEGORIES = {
  web: [80, 443, 8080, 8443, 3000, 8000, 9000, 4000, 5000, 6000],
  database: [3306, 5432, 6379, 27017, 1433, 1521, 5984, 9200, 11211, 2181],
  proxy: [3128, 8080, 8118, 1080, 9050, 9150, 4145, 1080, 1081],
  dns: [53, 5353, 853, 8600],
  mail: [25, 587, 465, 110, 143, 993, 995, 4190],
  ssh: [22, 2222, 2200],
  ftp: [21, 990, 989, 2121],
  rdp: [3389, 3388],
  vnc: [5900, 5901, 5902, 5903],
  telnet: [23, 2323]
};

/**
 * Detect port categories from search query
 */
function detectPortCategories(searchQuery, hosts) {
  const categories = new Set();
  const query = searchQuery.toLowerCase();
  
  // Check for port numbers in search
  Object.entries(PORT_CATEGORIES).forEach(([category, ports]) => {
    if (ports.some(port => query.includes(port.toString()))) {
      categories.add(category);
    }
  });
  
  // Check for keywords in search
  if (query.includes('web') || query.includes('http') || query.includes('https')) {
    categories.add('web');
  }
  if (query.includes('db') || query.includes('database') || query.includes('mysql') || query.includes('postgres')) {
    categories.add('database');
  }
  if (query.includes('proxy') || query.includes('socks')) {
    categories.add('proxy');
  }
  if (query.includes('dns') || query.includes('domain')) {
    categories.add('dns');
  }
  
  // If no specific categories detected, analyze host data
  if (categories.size === 0) {
    hosts.forEach(host => {
      host.ports.forEach(port => {
        Object.entries(PORT_CATEGORIES).forEach(([category, ports]) => {
          if (port.port_number && ports.includes(port.port_number)) {
            categories.add(category);
          }
        });
      });
    });
  }
  
  return Array.from(categories);
}

/**
 * Generate web metrics
 */
function generateWebMetrics(hosts) {
  const webHosts = hosts.filter(host => 
    host.ports.some(port => 
      port.port_number && PORT_CATEGORIES.web.includes(port.port_number)
    )
  );
  
  const sslHosts = webHosts.filter(host => 
    host.ssl_certificates.length > 0
  );
  
  const technologies = new Set();
  webHosts.forEach(host => {
    host.ports.forEach(port => {
      if (port.banner) {
        const banner = port.banner.toLowerCase();
        if (banner.includes('nginx')) technologies.add('Nginx');
        if (banner.includes('apache')) technologies.add('Apache');
        if (banner.includes('iis')) technologies.add('IIS');
        if (banner.includes('node')) technologies.add('Node.js');
        if (banner.includes('python')) technologies.add('Python');
        if (banner.includes('php')) technologies.add('PHP');
      }
    });
  });
  
  return {
    totalHosts: webHosts.length,
    sslEnabled: sslHosts.length,
    sslPercentage: webHosts.length > 0 ? Math.round((sslHosts.length / webHosts.length) * 100) : 0,
    commonTechnologies: Array.from(technologies).slice(0, 3)
  };
}

/**
 * Generate database metrics
 */
function generateDatabaseMetrics(hosts) {
  const dbHosts = hosts.filter(host => 
    host.ports.some(port => 
      port.port_number && PORT_CATEGORIES.database.includes(port.port_number)
    )
  );
  
  const dbTypes = new Set();
  dbHosts.forEach(host => {
    host.ports.forEach(port => {
      if (port.banner) {
        const banner = port.banner.toLowerCase();
        if (banner.includes('mysql')) dbTypes.add('MySQL');
        if (banner.includes('postgresql')) dbTypes.add('PostgreSQL');
        if (banner.includes('redis')) dbTypes.add('Redis');
        if (banner.includes('mongodb')) dbTypes.add('MongoDB');
        if (banner.includes('elasticsearch')) dbTypes.add('Elasticsearch');
      }
    });
  });
  
  return {
    totalHosts: dbHosts.length,
    databaseTypes: Array.from(dbTypes).slice(0, 3),
    anonymousAccess: dbHosts.filter(host => 
      host.ports.some(port => 
        port.banner && port.banner.toLowerCase().includes('anonymous')
      )
    ).length
  };
}

/**
 * Generate security metrics
 */
function generateSecurityMetrics(hosts) {
  const totalHosts = hosts.length;
  const vulnerableHosts = hosts.filter(host => 
    host.score && host.score > 7
  ).length;
  
  const exposedServices = hosts.filter(host => 
    host.ports.some(port => 
      port.status === 'open' && !host.private
    )
  ).length;
  
  const riskScore = Math.round((vulnerableHosts / totalHosts) * 10) || 0;
  
  return {
    riskScore,
    vulnerableHosts,
    exposedServices
  };
}

/**
 * Run demo with sample data
 */
function runDemo() {
  console.log('🚀 Port-Specific Metrics System Demo\n');
  
  demoQueries.forEach(query => {
    console.log(`\n🔍 Search Query: "${query}"`);
    
    const categories = detectPortCategories(query, sampleHosts);
    console.log(`📊 Detected Categories: ${categories.join(', ') || 'None'}`);
    
    if (categories.includes('web')) {
      const webMetrics = generateWebMetrics(sampleHosts);
      console.log(`🌐 Web Metrics:`, webMetrics);
    }
    
    if (categories.includes('database')) {
      const dbMetrics = generateDatabaseMetrics(sampleHosts);
      console.log(`🗄️ Database Metrics:`, dbMetrics);
    }
    
    const securityMetrics = generateSecurityMetrics(sampleHosts);
    console.log(`🛡️ Security Metrics:`, securityMetrics);
  });
  
  console.log('\n✨ Demo completed!');
  console.log('\nThis demonstrates how the system:');
  console.log('1. Detects port categories from search queries');
  console.log('2. Generates relevant metrics for detected services');
  console.log('3. Provides context-aware insights');
  console.log('4. Adapts the dashboard based on user intent');
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    detectPortCategories,
    generateWebMetrics,
    generateDatabaseMetrics,
    generateSecurityMetrics,
    runDemo,
    sampleHosts,
    demoQueries
  };
}

// Run demo if script is executed directly
if (typeof window === 'undefined') {
  runDemo();
}
