# Scanner Queue System

This document describes the queue system implementation for scanner jobs in the Fauxdan project.

## Overview

The queue system provides a robust, scalable way to manage scanner jobs (masscan, nmap, etc.) with the following features:

- **Job Queuing**: Queue scanner jobs with different priorities and scheduling
- **Worker Management**: Distribute jobs across multiple worker processes
- **Status Tracking**: Real-time job status and progress monitoring
- **Admin Interface**: Web-based management through Django admin
- **Retry Logic**: Automatic retry for failed jobs
- **Priority Queues**: Multiple queues with different priorities
- **Timeout Protection**: Configurable timeouts to prevent runaway scans
- **Resource Management**: Graceful process termination and cleanup

## Architecture

### Models

1. **JobQueue**: Represents a queue for scanner jobs
   - `name`: Unique queue name
   - `max_concurrent_jobs`: Maximum concurrent jobs allowed
   - `priority`: Queue priority (higher = more important)
   - `enabled`: Whether the queue is active

2. **ScannerJob**: Represents a single scanner job
   - `job_uuid`: Unique identifier
   - `job_type`: Type of scanner (masscan, nmap, custom)
   - `status`: Current job status (pending, running, completed, etc.)
   - `target`: Target IP, range, or hostname
   - `ports`: List of ports to scan
   - `scan_options`: Additional scan configuration
   - `priority`: Job priority within the queue
   - `progress`: Completion percentage (0-100)

3. **JobWorker**: Represents a worker process
   - `worker_id`: Unique worker identifier
   - `status`: Worker status (active, idle, busy, offline)
   - `supported_job_types`: Types of jobs this worker can handle
   - `max_concurrent_jobs`: Maximum jobs this worker can run
   - `current_job_count`: Current number of running jobs

### Services

1. **QueueService**: Core queue management service
   - Job processing and distribution
   - Worker registration and heartbeat
   - Job status updates and progress tracking

2. **QueueManager**: High-level queue operations
   - Job creation and management
   - Status queries and statistics
   - Job cancellation and retry

## Usage

### 1. Start the Scanner Service

```bash
# Start a scanner worker
python manage.py run_scanner_service

# With custom options
python manage.py run_scanner_service --job-types masscan nmap --max-concurrent 3
```

### 2. Queue Scanner Jobs

```bash
# Queue a masscan job (replaces direct execution)
python manage.py run_masscan_queued --target 192.168.1.0/24 --ports 80,443,8080

# With additional options and timeout
python manage.py run_masscan_queued \
    --target 10.0.0.0/8 \
    --ports 22,80,443,3306,5432 \
    --syn \
    --rate 1000 \
    --timeout 1800 \
    --queue high_priority \
    --priority 5

# Schedule for later execution with custom timeout
python manage.py run_masscan_queued \
    --target 172.16.0.0/16 \
    --timeout 3600 \
    --schedule "2024-01-15T14:30:00"

# Quick scan with short timeout
python manage.py run_masscan_queued \
    --target 192.168.1.1 \
    --ports 80,443 \
    --timeout 60 \
    --syn
```

### 3. Manage Jobs and Queues

```bash
# List all jobs
python manage.py queue_manager list

# List jobs by status
python manage.py queue_manager list --status running

# Check job status
python manage.py queue_manager status <job-uuid>

# Cancel a job
python manage.py queue_manager cancel <job-uuid>

# Show queue statistics
python manage.py queue_manager stats

# Show worker status
python manage.py queue_manager workers

# Clean up old jobs
python manage.py queue_manager cleanup --days 7

# Create jobs directly via queue manager
python manage.py queue_manager create \
    --type masscan \
    --target 192.168.1.0/24 \
    --ports 80,443,8080 \
    --timeout 1800 \
    --syn \
    --rate 1000
```

### 4. Set Up Default Queues

```bash
# Create default queues
python manage.py setup_queues
```

## Admin Interface

Access the Django admin interface to manage:

- **Job Queues**: Create, edit, and configure queues
- **Scanner Jobs**: View, cancel, and retry jobs
- **Job Workers**: Monitor worker status and availability
- **Statistics**: Real-time queue and job statistics

## Configuration

### Queue Configuration

Default queues are created with the following configuration:

- **default**: Standard queue (max 5 concurrent jobs, priority 0)
- **high_priority**: Urgent jobs (max 3 concurrent jobs, priority 10)
- **low_priority**: Background jobs (max 2 concurrent jobs, priority -5)

### Worker Configuration

Workers can be configured with:

- **Supported job types**: Which scanner types the worker can handle
- **Max concurrent jobs**: How many jobs can run simultaneously
- **Heartbeat interval**: How often to check worker health (30 seconds)

## Job Types

### Masscan Jobs

```python
# Example masscan job configuration
{
    "job_type": "masscan",
    "target": "192.168.1.0/24",
    "ports": [80, 443, 8080, 3306],
    "scan_options": {
        "syn": True,
        "tcp": False,
        "udp": False,
        "rate": 1000,
        "use_proxychains": False,
        "timeout": 3600  # 1 hour timeout
    }
}
```

### Nmap Jobs (Future)

```python
# Example nmap job configuration
{
    "job_type": "nmap",
    "target": "192.168.1.1",
    "ports": [22, 80, 443],
    "scan_options": {
        "scan_type": "tcp_syn",
        "service_detection": True,
        "os_detection": True
    }
}
```

## API Integration

The queue system can be integrated with REST APIs:

```python
from internet.lib.queue_service import QueueManager

# Create a job programmatically
job = QueueManager.create_job(
    job_type='masscan',
    target='192.168.1.0/24',
    queue_name='default',
    ports=[80, 443, 8080],
    scan_options={
        'syn': True, 
        'rate': 1000,
        'timeout': 1800  # 30 minutes
    },
    priority=5,
    user=request.user
)

# Check job status
status = QueueManager.get_job_status(str(job.job_uuid))

# Get queue statistics
stats = QueueManager.get_queue_stats()
```

## Timeout Protection

The queue system includes comprehensive timeout protection to prevent runaway scans and ensure proper resource management.

### Timeout Features

- **Configurable Timeouts**: Set custom timeout values for each scan job
- **Graceful Termination**: Processes are terminated gracefully before force-killing
- **Resource Cleanup**: Proper cleanup of streams and async tasks
- **Status Tracking**: Timeout events are logged and tracked in job status
- **Default Values**: Sensible 1-hour default timeout for most scans

### Timeout Usage

```bash
# Quick scan with 30-second timeout
python manage.py run_masscan_queued --target 192.168.1.1 --timeout 30 --ports 80,443

# Long-running scan with 2-hour timeout
python manage.py run_masscan_queued --target 10.0.0.0/8 --timeout 7200 --ports 1-65535

# Direct execution with timeout
python manage.py run_masscan --target 172.16.0.0/16 --timeout 1800 --syn

# Queue manager with timeout
python manage.py queue_manager create --type masscan --target 192.168.1.0/24 --timeout 900
```

### Timeout Behavior

1. **Process Monitoring**: The system monitors scan processes in real-time
2. **Timeout Detection**: When timeout is reached, the process is terminated
3. **Graceful Shutdown**: First attempts graceful termination (SIGTERM)
4. **Force Kill**: If graceful shutdown fails, force kills the process (SIGKILL)
5. **Cleanup**: All associated streams and async tasks are properly cleaned up
6. **Status Update**: Job status is updated to reflect timeout condition

### Timeout Configuration

- **Default Timeout**: 3600 seconds (1 hour)
- **Minimum Recommended**: 60 seconds for quick scans
- **Maximum Recommended**: 86400 seconds (24 hours) for large scans
- **Queue Override**: Timeout can be set per job or globally per queue

## Monitoring and Logging

### Logs

The queue system logs to:

- **Console**: Real-time job processing logs
- **File**: Persistent logs in `/var/log/app/` (if writable)
- **JSON Format**: Structured logs for ELK stack integration

### Metrics

Key metrics to monitor:

- **Queue depth**: Number of pending jobs per queue
- **Worker utilization**: Active vs idle workers
- **Job completion rate**: Success/failure ratios
- **Processing time**: Average job duration
- **Error rates**: Failed job frequency
- **Timeout events**: Frequency of job timeouts
- **Resource usage**: CPU and memory consumption per job

### Health Checks

- **Worker heartbeat**: Workers send heartbeats every 30 seconds
- **Job timeout**: Long-running jobs can be monitored for timeouts
- **Queue health**: Monitor queue capacity and processing rates

## Scaling

### Horizontal Scaling

- **Multiple Workers**: Run multiple worker processes on different machines
- **Load Balancing**: Distribute jobs across workers based on capacity
- **Queue Sharding**: Split large queues across multiple database shards

### Vertical Scaling

- **Worker Capacity**: Increase `max_concurrent_jobs` per worker
- **Queue Capacity**: Increase `max_concurrent_jobs` per queue
- **Database Optimization**: Add indexes and optimize queries

## Troubleshooting

### Common Issues

1. **Jobs stuck in pending**: Check if workers are running and healthy
2. **High memory usage**: Reduce `max_concurrent_jobs` or optimize scan options
3. **Database locks**: Check for long-running transactions or deadlocks
4. **Worker disconnections**: Verify network connectivity and heartbeat settings
5. **Frequent timeouts**: Adjust timeout values or optimize scan parameters
6. **Resource exhaustion**: Monitor system resources and adjust concurrency limits

### Debug Commands

```bash
# Check worker status
python manage.py queue_manager workers

# View job details
python manage.py queue_manager status <job-uuid>

# Check queue statistics
python manage.py queue_manager stats

# Clean up stuck jobs
python manage.py queue_manager cleanup --dry-run

# Test timeout functionality
python manage.py run_masscan_queued --target 127.0.0.1 --timeout 5 --ports 80

# Monitor job progress
python manage.py queue_manager list --status running
```

## Migration from Direct Execution

To migrate from direct masscan execution to the queue system:

1. **Replace direct calls**: Use `run_masscan_queued` instead of `run_masscan`
2. **Start workers**: Run `run_scanner_service` on worker machines
3. **Update scripts**: Modify existing scripts to use the queue API
4. **Monitor queues**: Set up monitoring for queue health and job status

## Future Enhancements

- **Nmap integration**: Full nmap job support
- **Custom scanners**: Plugin system for custom scanner types
- **Job dependencies**: Chain jobs with dependencies
- **Resource limits**: CPU and memory limits per job
- **Job scheduling**: Cron-like scheduling for recurring jobs
- **Webhooks**: Notifications when jobs complete
- **Job templates**: Reusable job configurations
- **Dynamic timeouts**: Adaptive timeout based on target size
- **Timeout policies**: Queue-level timeout policies
- **Resource monitoring**: Real-time resource usage tracking

## Quick Reference

### Essential Commands

```bash
# Start scanner service
python manage.py run_scanner_service

# Queue a scan job
python manage.py run_masscan_queued --target <target> --ports <ports> --timeout <seconds>

# Check job status
python manage.py queue_manager status <job-uuid>

# List all jobs
python manage.py queue_manager list

# Show queue statistics
python manage.py queue_manager stats

# Setup default queues
python manage.py setup_queues
```

### Common Timeout Values

- **Quick scans**: 60-300 seconds
- **Standard scans**: 1800-3600 seconds (30-60 minutes)
- **Large scans**: 7200-14400 seconds (2-4 hours)
- **Massive scans**: 86400+ seconds (24+ hours)

### Job Status Values

- `pending`: Job created, waiting to be processed
- `queued`: Job assigned to worker, waiting to start
- `running`: Job currently executing
- `completed`: Job finished successfully
- `failed`: Job failed with error
- `cancelled`: Job was cancelled
- `timeout`: Job exceeded timeout limit
