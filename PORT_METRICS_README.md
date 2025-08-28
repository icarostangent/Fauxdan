# Port-Specific Metrics System

## Overview

The Port-Specific Metrics System provides intelligent, context-aware insights based on the ports and services being searched. Instead of showing generic metrics, it dynamically displays relevant information tailored to the specific service types detected.

## Features

### 🎯 **Context-Aware Metrics**
- Automatically detects port categories from search queries
- Shows relevant metrics based on detected services
- Adapts dashboard content to user's current investigation

### 🔍 **Port Categories Supported**
- **Web Services**: Ports 80, 443, 8080, 8443, 3000, 8000, 9000
- **Database Services**: Ports 3306, 5432, 6379, 27017, 1433, 1521, 5984
- **Proxy Services**: Ports 3128, 8080, 8118, 1080, 9050, 9150
- **DNS Services**: Ports 53, 5353, 853, 8600
- **Mail Services**: Ports 25, 587, 465, 110, 143, 993, 995
- **SSH Services**: Ports 22, 2222, 2200
- **FTP Services**: Ports 21, 990, 989, 2121
- **RDP Services**: Ports 3389, 3388
- **VNC Services**: Ports 5900-5903
- **Telnet Services**: Ports 23, 2323

### 📊 **Dynamic Metrics Dashboard**

#### Web Services Metrics
- Total hosts with web services
- SSL/TLS coverage percentage
- Common technologies detected (Nginx, Apache, IIS, Node.js, Python, PHP)

#### Database Services Metrics
- Total database hosts
- Database types detected (MySQL, PostgreSQL, Redis, MongoDB, Elasticsearch)
- Anonymous access detection

#### Proxy Services Metrics
- Total proxy hosts
- Proxy types (SOCKS, HTTP, Transparent)
- High anonymity proxy count

#### DNS Services Metrics
- Total DNS servers
- Server types (BIND, dnsmasq, Unbound)
- DNSSEC adoption

#### Security Overview
- Risk score (1-10 scale)
- Vulnerable hosts count
- Exposed services count

#### Geographic Distribution
- Countries detected
- Top regions
- Cloud provider identification

## Usage

### Search Examples

#### Port Numbers
```
80               # HTTP services
443              # HTTPS services
3306             # MySQL databases
5432             # PostgreSQL databases
22               # SSH services
53               # DNS services
3128             # HTTP proxies
```

#### IP Addresses
```
192.168.1.1      # Private network IP
10.0.0.1         # Private network IP
172.16.0.1       # Private network IP
8.8.8.8          # Public IP (Google DNS)
```

#### Host Names
```
example.com      # Domain name
mail.example.com # Subdomain
db.example.com   # Database hostname
web.example.com  # Web server hostname
```

#### Common Service Searches
```
nginx            # Nginx web servers
mysql            # MySQL services
apache           # Apache web servers
ssh              # SSH services
```

### Component Integration

The system consists of two main components:

1. **PortMetrics.vue**: Main metrics dashboard component
2. **Enhanced SearchBar.vue**: Search with examples and suggestions

### Integration in HostsView

```vue
<template>
  <div class="about">
    <SearchBar 
      :initial-value="route.query.q?.toString() || ''"
      @search="handleSearch" 
    />
    
    <!-- Port-Specific Metrics Dashboard -->
    <PortMetrics 
      :hosts="hosts.results"
      :search-query="route.query.q?.toString() || ''"
    />
    
    <HostList 
      :hosts="hosts"
      :loading="loading"
      :error="error"
      @page-change="handlePageChange"
    />
  </div>
</template>
```

## Technical Implementation

### Port Detection Logic

1. **Query Analysis**: Parse search query for port numbers and keywords
2. **Data Analysis**: Analyze host data for port patterns
3. **Category Mapping**: Map detected ports to service categories
4. **Metrics Generation**: Generate relevant metrics for detected categories

### Performance Considerations

- Computed properties for efficient metric calculation
- Lazy loading of metrics based on detected categories
- Responsive design for mobile devices
- Efficient filtering and aggregation algorithms

### Data Sources

- Host data from Vuex store
- Port information from host objects
- SSL certificate data for security metrics
- Banner information for technology detection

## Future Enhancements

### Planned Features
- **Real-time Updates**: WebSocket integration for live metrics
- **Advanced Filtering**: Date ranges, geographic filters
- **Export Functionality**: CSV/JSON export of metrics
- **Historical Trends**: Time-based metric analysis
- **Custom Dashboards**: User-configurable metric layouts

### API Integration
- **Enhanced Backend**: Dedicated metrics endpoints
- **Caching Layer**: Redis cache for performance
- **Aggregation Queries**: Database-level metric calculations

## Styling and Design

### Design Principles
- **Consistent**: Follows existing design system
- **Responsive**: Mobile-first approach
- **Accessible**: Screen reader support
- **Interactive**: Hover effects and transitions

### Color Scheme
- **Web Services**: Blue (#1976d2)
- **Database Services**: Purple (#7b1fa2)
- **Proxy Services**: Orange (#f57c00)
- **DNS Services**: Green (#388e3c)
- **Security**: Red (#d32f2f)
- **Geographic**: Green (#388e3c)

### Responsive Breakpoints
- **Desktop**: 4-column grid layout
- **Tablet**: 2-column grid layout
- **Mobile**: Single-column layout

## Troubleshooting

### Common Issues

1. **Metrics Not Showing**: Check if hosts data is loaded
2. **Categories Not Detected**: Verify search query format
3. **Performance Issues**: Check host data size and filtering

### Debug Mode

Enable debug logging by setting `console.log` statements in the component setup function.

## Contributing

When adding new port categories or metrics:

1. Update `PORT_CATEGORIES` object
2. Add corresponding metric computation logic
3. Update component template
4. Add appropriate styling
5. Test with various search queries

## License

This system is part of the Fauxdan project and follows the same licensing terms.
