# Async & Multithreaded Geolocation System

This guide explains the enhanced IP geolocation system with async processing, multithreading, and automatic job queuing.

## 🚀 New Features

### 1. **Async Geolocation Service**
- **ThreadPoolExecutor** with configurable worker threads (default: 10)
- **Async batch processing** with concurrent API calls
- **Smart rate limiting** between batches
- **Exception handling** for individual requests

### 2. **Automatic Job Queuing**
- **Masscan integration** - automatically queues geolocation jobs for new hosts
- **Job deduplication** - prevents duplicate jobs
- **Priority system** - geolocation jobs have lower priority than banner/SSL jobs
- **Stale data detection** - re-queues jobs for hosts with old geolocation data

### 3. **Enhanced Management Command**
- **Three processing modes**: job queuing, async batch, sequential
- **Configurable concurrency** and batch sizes
- **Progress tracking** with detailed statistics

## 📋 Usage Examples

### Job Queuing Mode (Recommended for Production)
```bash
# Queue geolocation jobs for all hosts needing updates
dc exec backend python manage.py geolocate_hosts --queue-jobs

# Queue jobs for specific batch size
dc exec backend python manage.py geolocate_hosts --queue-jobs --batch-size 100

# Force queue jobs for all hosts (even those already geolocated)
dc exec backend python manage.py geolocate_hosts --queue-jobs --force
```

### Async Batch Mode (Fast Direct Processing)
```bash
# Process hosts with async batch geolocation (20 concurrent per batch)
dc exec backend python manage.py geolocate_hosts --async-batch --batch-size 20

# Single IP with async processing
dc exec backend python manage.py geolocate_hosts --ip 8.8.8.8 --async-batch

# Force process all hosts with async batching
dc exec backend python manage.py geolocate_hosts --async-batch --force --batch-size 50
```

### Sequential Mode (Original Behavior)
```bash
# Original sequential processing with rate limiting
dc exec backend python manage.py geolocate_hosts --batch-size 10 --delay 0.2

# Single IP with sequential processing
dc exec backend python manage.py geolocate_hosts --ip 1.1.1.1
```

## 🔄 Automatic Integration

### Masscan Discovery Integration
When masscan discovers a new host, the system automatically:

1. **Creates the host** in the database
2. **Queues banner grab job** for each open port
3. **Queues domain enumeration job** for the host
4. **Queues geolocation job** for the host (NEW!)

### Job Processing Priority
Jobs are processed in this order:
1. **Priority 0**: Banner grab jobs
2. **Priority 1**: Domain enumeration jobs  
3. **Priority 2**: Geolocation jobs (NEW!)
4. **Priority 3+**: SSL certificate and other jobs

## 🏗️ System Architecture

### Async Geolocation Service
```python
# ThreadPoolExecutor with 10 workers by default
geolocation_service = GeolocationService(max_workers=10)

# Async single IP geolocation
location = await get_ip_geolocation_async('8.8.8.8')

# Async batch processing (20 IPs concurrently)
results = await get_ip_geolocations_batch_async(['8.8.8.8', '1.1.1.1'], batch_size=20)
```

### Job Queue Integration
```python
# Jobs are automatically created during host discovery
AncillaryJob.objects.create(
    job_type='geolocation',
    host_ip=host_ip,
    host=host_obj,
    status='pending',
    priority=2  # Lower priority than banner/domain jobs
)
```

### Queue Service Processing
The queue service automatically processes geolocation jobs:
```python
async def _process_geolocation(self, job: 'AncillaryJob') -> dict:
    # Skip private IPs
    # Get geolocation data using async service  
    # Update host with location data
    # Handle errors gracefully
```

## 📊 Performance Comparison

| Mode | Speed | Resource Usage | API Efficiency | Best For |
|------|-------|----------------|----------------|----------|
| **Job Queue** | ⭐⭐⭐ | Low | ⭐⭐⭐⭐⭐ | Production, large datasets |
| **Async Batch** | ⭐⭐⭐⭐⭐ | Medium | ⭐⭐⭐⭐ | Fast processing, medium datasets |
| **Sequential** | ⭐⭐ | Low | ⭐⭐ | Small datasets, testing |

## 🔧 Configuration Options

### Environment Variables
```bash
# Optional API keys for higher rate limits
IPINFO_TOKEN=your_ipinfo_token_here
IPGEOLOCATION_API_KEY=your_ipgeolocation_api_key_here
```

### Geolocation Service Configuration
```python
# Custom thread pool size
service = GeolocationService(max_workers=20)

# Custom batch processing
results = await service.get_locations_batch_async(
    ip_addresses=['8.8.8.8', '1.1.1.1'], 
    batch_size=50
)
```

## 📈 Monitoring & Statistics

### Check Job Status
```bash
# View geolocation job statistics
dc exec backend python manage.py shell -c "
from internet.models import AncillaryJob
total = AncillaryJob.objects.filter(job_type='geolocation').count()
pending = AncillaryJob.objects.filter(job_type='geolocation', status='pending').count()
completed = AncillaryJob.objects.filter(job_type='geolocation', status='completed').count()
print(f'Geolocation jobs - Total: {total}, Pending: {pending}, Completed: {completed}')
"
```

### Check Geolocation Coverage
```bash
# See geolocation coverage statistics
dc exec backend python manage.py shell -c "
from internet.models import Host
total = Host.objects.count()
geolocated = Host.objects.filter(geolocation_updated__isnull=False).count()
print(f'Geolocated hosts: {geolocated}/{total} ({geolocated/total*100:.1f}%)')
"
```

### View Recent Results
```bash
# See recent geolocation results
dc exec backend python manage.py shell -c "
from internet.models import Host
hosts = Host.objects.filter(geolocation_updated__isnull=False).order_by('-geolocation_updated')[:10]
for host in hosts:
    print(f'{host.ip}: {host.get_location_display()}')
"
```

## 🚨 Important Notes

### Rate Limiting
- **Built-in rate limiting** between batches (1 second default)
- **API provider rotation** to distribute load
- **Caching** to minimize repeated requests
- **Configurable delays** for custom rate limiting

### Error Handling
- **Private IP detection** - automatically skips internal addresses
- **Provider failover** - tries multiple APIs if one fails
- **Graceful degradation** - continues processing if some IPs fail
- **Timestamp updates** - prevents repeated failed attempts

### Resource Management
- **Thread pool cleanup** on service shutdown
- **Memory efficient** batch processing
- **Database transaction optimization**
- **Async context management**

## 🔄 Integration with Queue Service

The geolocation system integrates seamlessly with the existing queue service:

1. **Jobs are queued** during host discovery
2. **Queue service processes** geolocation jobs alongside other job types
3. **Results are stored** in the AncillaryJob model
4. **Host records are updated** with geolocation data
5. **Frontend displays** the location information with interactive maps

## 🎯 Best Practices

### For Large Datasets (1000+ hosts)
```bash
# Use job queuing for maximum efficiency
dc exec backend python manage.py geolocate_hosts --queue-jobs --batch-size 100
```

### For Medium Datasets (100-1000 hosts)
```bash
# Use async batch processing for speed
dc exec backend python manage.py geolocate_hosts --async-batch --batch-size 20
```

### For Small Datasets (< 100 hosts)
```bash
# Use sequential processing with rate limiting
dc exec backend python manage.py geolocate_hosts --batch-size 10 --delay 0.1
```

### For Testing Single IPs
```bash
# Quick async test
dc exec backend python manage.py geolocate_hosts --ip 8.8.8.8 --async-batch
```

This enhanced geolocation system provides maximum flexibility and performance for any scale of operation! 🌍
