# IP Geolocation Setup Guide

This guide explains how to implement IP geolocation for your hosts in the Fauxdan system.

## 🚀 Quick Start

### 1. Run Database Migration
```bash
# Generate and apply the migration for geolocation fields
dc exec backend python manage.py makemigrations
dc exec backend python manage.py migrate
```

### 2. Test Single IP Geolocation
```bash
# Test geolocation on a specific IP
dc exec backend python manage.py geolocate_hosts --ip 8.8.8.8
```

### 3. Bulk Geolocate All Hosts
```bash
# Geolocate all hosts that need updates
dc exec backend python manage.py geolocate_hosts

# Force re-geolocate all hosts
dc exec backend python manage.py geolocate_hosts --force

# Geolocate with custom settings
dc exec backend python manage.py geolocate_hosts --batch-size 50 --delay 0.2
```

## 🔧 Configuration Options

### API Keys (Optional but Recommended)

Add these to your environment variables for higher rate limits:

```bash
# .env file
IPINFO_TOKEN=your_ipinfo_token_here
IPGEOLOCATION_API_KEY=your_ipgeolocation_api_key_here
```

### Free API Providers Used

1. **ip-api.com** - 1000 requests/month, no key required
2. **ipinfo.io** - 50,000 requests/month with free account
3. **freeipapi.com** - Unlimited free requests
4. **ipgeolocation.io** - 1000 requests/month free

## 📊 Features Added

### Database Fields
- `country` - Country name
- `country_code` - 2-letter country code
- `region` - State/province
- `city` - City name
- `latitude` - GPS latitude
- `longitude` - GPS longitude
- `timezone` - Timezone identifier
- `isp` - Internet Service Provider
- `organization` - Organization name
- `asn` - Autonomous System Number
- `geolocation_updated` - Last update timestamp

### Frontend Integration
- **Geolocation section** in host detail view
- **Location information** with city, region, country
- **Network information** with ISP and ASN details
- **Map integration** with Google Maps links
- **Coordinates display** with precision

### Management Commands
```bash
# Basic usage
python manage.py geolocate_hosts

# Advanced options
python manage.py geolocate_hosts \
  --batch-size 100 \
  --delay 0.1 \
  --max-age-days 30 \
  --force
```

## 🛠️ Advanced Usage

### Programmatic Access
```python
from internet.lib.geolocation import get_ip_geolocation

# Get location data
location = get_ip_geolocation('8.8.8.8')
print(location)
# {'country': 'United States', 'city': 'Mountain View', ...}

# Bulk geolocation
from internet.lib.geolocation import bulk_geolocate_hosts
results = bulk_geolocate_hosts(['8.8.8.8', '1.1.1.1'])
```

### Host Model Methods
```python
from internet.models import Host

host = Host.objects.get(ip='8.8.8.8')

# Get formatted location string
print(host.get_location_display())
# "Mountain View, California, United States"

# Check if needs update
if host.needs_geolocation_update():
    # Update geolocation
    pass
```

### Caching
- Geolocation results are cached for 24 hours
- Failed lookups are cached for 1 hour
- Uses Django's default cache backend

## 🔒 Rate Limiting & Best Practices

### Built-in Rate Limiting
- Default 0.1 second delay between requests
- Configurable batch processing
- Automatic fallback between providers
- Caching to minimize API calls

### Recommendations
1. **Start with small batches** to test your setup
2. **Use API keys** for higher rate limits
3. **Run during off-peak hours** for bulk operations
4. **Monitor your API usage** to avoid limits

### Error Handling
- Automatic provider fallback
- Private IP detection and skipping
- Graceful error handling with logging
- Resume capability for large datasets

## 📈 Monitoring

### Check Progress
```bash
# See how many hosts have been geolocated
dc exec backend python manage.py shell -c "
from internet.models import Host
total = Host.objects.count()
geolocated = Host.objects.filter(geolocation_updated__isnull=False).count()
print(f'Geolocated: {geolocated}/{total} ({geolocated/total*100:.1f}%)')
"
```

### View Results
```bash
# See recent geolocation results
dc exec backend python manage.py shell -c "
from internet.models import Host
hosts = Host.objects.filter(geolocation_updated__isnull=False)[:10]
for host in hosts:
    print(f'{host.ip}: {host.get_location_display()}')
"
```

## 🗺️ Map Integration

### Google Maps
The frontend includes Google Maps integration:
- Click "View on Google Maps" to see exact location
- Coordinates displayed with 4 decimal precision
- Direct links to map view

### Alternative Map Services
You can easily integrate other mapping services:
- OpenStreetMap
- Mapbox
- Leaflet
- Custom mapping solutions

## 🚨 Important Notes

1. **Private IPs**: Private/internal IP addresses are automatically skipped
2. **Rate Limits**: Respect API provider rate limits
3. **Accuracy**: Geolocation accuracy varies by provider and IP type
4. **Privacy**: Consider privacy implications of storing location data
5. **Updates**: Geolocation data can become stale, regular updates recommended

## 🐛 Troubleshooting

### Common Issues
1. **"No module named 'requests'"**: Install requests: `pip install requests`
2. **Rate limit exceeded**: Add delays or API keys
3. **No results**: Check internet connectivity and API status
4. **Migration errors**: Ensure you're running migrations as the correct user

### Debug Mode
```bash
# Test single IP with verbose output
dc exec backend python manage.py geolocate_hosts --ip 8.8.8.8
```

### Logs
Check Django logs for geolocation errors:
```bash
dc logs backend | grep -i geolocation
```

## 🔄 Automation

### Scheduled Updates
Add to your crontab or scheduler:
```bash
# Update geolocation weekly
0 2 * * 0 cd /path/to/fauxdan && dc exec backend python manage.py geolocate_hosts
```

### Integration with Scanning
You can integrate geolocation into your scanning pipeline by calling the geolocation service after host discovery.

## 📝 API Response Example

```json
{
  "ip": "8.8.8.8",
  "country": "United States",
  "country_code": "US",
  "region": "California",
  "city": "Mountain View",
  "latitude": 37.4056,
  "longitude": -122.0775,
  "timezone": "America/Los_Angeles",
  "isp": "Google LLC",
  "organization": "Google Public DNS",
  "asn": "AS15169 Google LLC",
  "provider": "ip-api.com"
}
```

This comprehensive geolocation system will give you detailed geographic and network information about all discovered hosts!
