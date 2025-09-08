"""
Queue Service for managing scanner jobs
"""
import asyncio
import logging
import os
import socket
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from django.conf import settings
from django.db import transaction, models
from django.utils import timezone
from internet.models import ScannerJob, JobQueue, JobWorker, Scan

logger = logging.getLogger(__name__)


class QueueService:
    """Service for managing scanner job queues"""
    
    def __init__(self):
        self.worker_id = f"worker-{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        self.worker = None
        self.running = False
        self.current_jobs = {}
        
    async def start_worker(self, supported_job_types: List[str] = None, max_concurrent_jobs: int = 1):
        """Start the queue worker"""
        if supported_job_types is None:
            supported_job_types = ['masscan', 'nmap', 'custom']
            
        self.running = True
        
        # Register worker
        self.worker = await self._register_worker(supported_job_types, max_concurrent_jobs)
        
        logger.info(f"Started queue worker: {self.worker_id}")
        
        # Start heartbeat and job processing
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        job_processor_task = asyncio.create_task(self._job_processor_loop())
        
        try:
            await asyncio.gather(heartbeat_task, job_processor_task)
        except asyncio.CancelledError:
            logger.info("Worker shutdown requested")
        finally:
            await self._cleanup_worker()
    
    async def _register_worker(self, supported_job_types: List[str], max_concurrent_jobs: int) -> JobWorker:
        """Register this worker in the database"""
        from asgiref.sync import sync_to_async
        
        def _create_worker():
            worker, created = JobWorker.objects.get_or_create(
                worker_id=self.worker_id,
                defaults={
                    'hostname': socket.gethostname(),
                    'pid': os.getpid(),
                    'supported_job_types': supported_job_types,
                    'max_concurrent_jobs': max_concurrent_jobs,
                    'status': 'active',
                    'version': '1.0.0',
                }
            )
            if not created:
                # Update existing worker
                worker.hostname = socket.gethostname()
                worker.pid = os.getpid()
                worker.supported_job_types = supported_job_types
                worker.max_concurrent_jobs = max_concurrent_jobs
                worker.status = 'active'
                worker.save()
            return worker
        
        return await sync_to_async(_create_worker)()
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to keep worker alive"""
        while self.running:
            try:
                await self._update_heartbeat()
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(10)
    
    async def _update_heartbeat(self):
        """Update worker heartbeat"""
        from asgiref.sync import sync_to_async
        
        def _update():
            if self.worker:
                self.worker.update_heartbeat()
        
        await sync_to_async(_update)()
    
    async def _job_processor_loop(self):
        """Main loop for processing jobs"""
        while self.running:
            try:
                # Check if we can accept more jobs
                if len(self.current_jobs) < self.worker.max_concurrent_jobs:
                    job = await self._get_next_job()
                    if job:
                        # Process job asynchronously
                        asyncio.create_task(self._process_job(job))
                
                await asyncio.sleep(1)  # Check for jobs every second
            except Exception as e:
                logger.error(f"Job processor error: {e}")
                await asyncio.sleep(5)
    
    async def _get_next_job(self) -> Optional[ScannerJob]:
        """Get the next available job from queues"""
        from asgiref.sync import sync_to_async
        
        def _get_job():
            # Get available queues ordered by priority
            queues = JobQueue.objects.filter(enabled=True).order_by('-priority')
            
            for queue in queues:
                # Check if queue has capacity
                running_jobs = ScannerJob.objects.filter(
                    queue=queue,
                    status__in=['running', 'queued'],
                    assigned_worker=self.worker
                ).count()
                
                if running_jobs >= queue.max_concurrent_jobs:
                    continue
                
                # Get next job from this queue
                job = ScannerJob.objects.filter(
                    queue=queue,
                    status='pending',
                    job_type__in=self.worker.supported_job_types
                ).filter(
                    models.Q(scheduled_for__isnull=True) | models.Q(scheduled_for__lte=timezone.now())
                ).order_by('-priority', 'created_at').first()
                
                if job:
                    # Assign job to this worker
                    job.assigned_worker = self.worker
                    job.status = 'queued'
                    job.save()
                    return job
            
            return None
        
        return await sync_to_async(_get_job)()
    
    async def _process_job(self, job: ScannerJob):
        """Process a single job"""
        job_id = str(job.job_uuid)
        self.current_jobs[job_id] = job
        
        try:
            logger.info(f"Processing job {job_id}: {job.job_type} - {job.target}")
            
            # Mark job as started
            await self._mark_job_started(job)
            
            # Process based on job type
            if job.job_type == 'masscan':
                await self._process_masscan_job(job)
            elif job.job_type == 'nmap':
                await self._process_nmap_job(job)
            elif job.job_type == 'custom':
                await self._process_custom_job(job)
            else:
                raise ValueError(f"Unsupported job type: {job.job_type}")
            
            # Mark job as completed
            await self._mark_job_completed(job)
            logger.info(f"Completed job {job_id}")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await self._mark_job_failed(job, str(e))
        finally:
            # Clean up
            if job_id in self.current_jobs:
                del self.current_jobs[job_id]
            await self._decrement_worker_job_count()
    
    async def _process_masscan_job(self, job: ScannerJob):
        """Process a masscan job"""
        from internet.lib.masscan import MasscanConfigurator
        from internet.lib.proxychains import ProxyChainsConfigurator
        from asgiref.sync import sync_to_async
        
        # Create masscan configurator
        masscan = MasscanConfigurator()
        masscan.set_target(job.target)
        
        # Apply scan options
        scan_options = job.scan_options or {}
        
        if scan_options.get('syn', True):
            masscan.set_syn()
        if scan_options.get('tcp', False):
            masscan.set_tcp()
        if scan_options.get('udp', False):
            masscan.set_udp()
        if scan_options.get('use_proxychains', False):
            proxychains = ProxyChainsConfigurator()
            proxychains.set_config()
        
        if scan_options.get('rate'):
            masscan.set_rate(scan_options['rate'])
        
        if scan_options.get('resume', False):
            masscan.set_resume()
        
        if job.ports:
            masscan.set_ports(job.ports)
        
        # Create scan record
        scan = await sync_to_async(Scan.objects.create)(
            scan_command=masscan.get_cmd(),
            scan_type='masscan',
            user=job.user
        )
        
        # Link job to scan
        job.scan = scan
        await sync_to_async(job.save)()
        
        # Run the scan with timeout
        timeout = scan_options.get('timeout', 3600)  # Default 1 hour
        await self._run_masscan_scan(job, masscan.get_cmd(), timeout)
    
    async def _run_masscan_scan(self, job: ScannerJob, command: str, timeout: int = 3600):
        """Run masscan command and process output with timeout"""
        from asgiref.sync import sync_to_async
        import re
        
        def process_discovery(host_ip, port_number, proto, current_time, scan):
            """Process a discovered port"""
            from internet.models import Host, Port
            
            # Get or create host
            host_obj, host_created = Host.objects.get_or_create(ip=host_ip)
            host_obj.last_seen = current_time
            host_obj.save()
            
            # Check if port already exists
            existing_port = Port.objects.filter(
                host=host_obj,
                port_number=port_number,
                proto=proto
            ).first()
            
            if existing_port:
                existing_port.last_seen = current_time
                existing_port.status = 'open'
                existing_port.save()
                return f'Updated existing port: {host_ip}:{port_number}/{proto}', host_created
            else:
                Port.objects.create(
                    scan=scan,
                    port_number=port_number,
                    proto=proto,
                    host=host_obj,
                    last_seen=current_time,
                    status='open'
                )
                return f'New port discovered: {host_ip}:{port_number}/{proto}', host_created
        
        async def parse_stdout(stdout_line):
            """Parse masscan output"""
            port_pattern = r'Discovered open port (\d+)/(\w+) on ([0-9\.]+)'
            match = re.search(port_pattern, stdout_line)
            if match:
                port_number = int(match.group(1))
                proto = match.group(2)
                host_ip = match.group(3)
                current_time = timezone.now()
                
                result, host_created = await sync_to_async(process_discovery)(
                    host_ip, port_number, proto, current_time, job.scan
                )
                
                if host_created:
                    logger.info(f'New host discovered: {host_ip}')
                logger.info(result)
        
        async def read_stream(stream, callback):
            """Read from stream and call callback for each line"""
            buffer = b''
            while True:
                chunk = await stream.read(1024)
                if not chunk:
                    break
                buffer += chunk
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    line_str = line.decode('utf-8').strip()
                    if callback and line_str:
                        await callback(line_str)
        
        # Run the process
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Process output concurrently
        stdout_task = asyncio.create_task(read_stream(process.stdout, parse_stdout))
        stderr_task = asyncio.create_task(read_stream(process.stderr, None))
        
        try:
            # Wait for both streams and process to complete with timeout
            await asyncio.wait_for(
                asyncio.gather(stdout_task, stderr_task, process.wait()),
                timeout=timeout
            )
            
            if process.returncode != 0:
                raise Exception(f"Masscan failed with return code {process.returncode}")
                
        except asyncio.TimeoutError:
            logger.warning(f'Masscan scan timed out after {timeout} seconds. Terminating process...')
            # Terminate the process
            process.terminate()
            try:
                # Give it a moment to terminate gracefully
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                # Force kill if it doesn't terminate gracefully
                process.kill()
                await process.wait()
            
            # Cancel the stream reading tasks
            stdout_task.cancel()
            stderr_task.cancel()
            
            raise Exception(f"Masscan scan timed out after {timeout} seconds")
    
    async def _process_nmap_job(self, job: ScannerJob):
        """Process an nmap job (placeholder)"""
        # TODO: Implement nmap job processing
        await asyncio.sleep(1)  # Placeholder
        raise NotImplementedError("Nmap job processing not yet implemented")
    
    async def _process_custom_job(self, job: ScannerJob):
        """Process a custom job (placeholder)"""
        # TODO: Implement custom job processing
        await asyncio.sleep(1)  # Placeholder
        raise NotImplementedError("Custom job processing not yet implemented")
    
    async def _mark_job_started(self, job: ScannerJob):
        """Mark job as started"""
        from asgiref.sync import sync_to_async
        
        def _mark():
            job.mark_started()
            self.worker.increment_job_count()
        
        await sync_to_async(_mark)()
    
    async def _mark_job_completed(self, job: ScannerJob):
        """Mark job as completed"""
        from asgiref.sync import sync_to_async
        
        def _mark():
            job.mark_completed()
        
        await sync_to_async(_mark)()
    
    async def _mark_job_failed(self, job: ScannerJob, error_message: str):
        """Mark job as failed"""
        from asgiref.sync import sync_to_async
        
        def _mark():
            job.mark_failed(error_message)
        
        await sync_to_async(_mark)()
    
    async def _decrement_worker_job_count(self):
        """Decrement worker job count"""
        from asgiref.sync import sync_to_async
        
        def _decrement():
            if self.worker:
                self.worker.decrement_job_count()
        
        await sync_to_async(_decrement)()
    
    async def _cleanup_worker(self):
        """Clean up worker on shutdown"""
        from asgiref.sync import sync_to_async
        
        def _cleanup():
            if self.worker:
                # Mark any running jobs as failed
                running_jobs = ScannerJob.objects.filter(
                    assigned_worker=self.worker,
                    status__in=['running', 'queued']
                )
                for job in running_jobs:
                    job.status = 'failed'
                    job.error_message = 'Worker shutdown'
                    job.completed_at = timezone.now()
                    job.save()
                
                # Mark worker as offline
                self.worker.status = 'offline'
                self.worker.save()
        
        await sync_to_async(_cleanup)()
        logger.info(f"Worker {self.worker_id} cleaned up")


class QueueManager:
    """Manager for queue operations"""
    
    @staticmethod
    def create_job(
        job_type: str,
        target: str,
        queue_name: str = 'default',
        ports: List[int] = None,
        scan_options: Dict[str, Any] = None,
        priority: int = 0,
        user=None,
        scheduled_for: datetime = None
    ) -> ScannerJob:
        """Create a new scanner job"""
        queue, created = JobQueue.objects.get_or_create(
            name=queue_name,
            defaults={
                'description': f'Default queue for {queue_name}',
                'max_concurrent_jobs': 5,
                'priority': 0
            }
        )
        
        job = ScannerJob.objects.create(
            job_type=job_type,
            target=target,
            queue=queue,
            ports=ports or [],
            scan_options=scan_options or {},
            priority=priority,
            user=user,
            scheduled_for=scheduled_for
        )
        
        logger.info(f"Created job {job.job_uuid}: {job_type} - {target}")
        return job
    
    @staticmethod
    def get_job_status(job_uuid: str) -> Optional[Dict[str, Any]]:
        """Get job status and details"""
        try:
            job = ScannerJob.objects.get(job_uuid=job_uuid)
            return {
                'job_uuid': str(job.job_uuid),
                'status': job.status,
                'progress': job.progress,
                'created_at': job.created_at,
                'started_at': job.started_at,
                'completed_at': job.completed_at,
                'error_message': job.error_message,
                'target': job.target,
                'job_type': job.job_type,
            }
        except ScannerJob.DoesNotExist:
            return None
    
    @staticmethod
    def cancel_job(job_uuid: str) -> bool:
        """Cancel a job"""
        try:
            job = ScannerJob.objects.get(job_uuid=job_uuid)
            if job.status in ['pending', 'queued', 'running']:
                job.mark_cancelled()
                return True
            return False
        except ScannerJob.DoesNotExist:
            return False
    
    @staticmethod
    def get_queue_stats(queue_name: str = None) -> Dict[str, Any]:
        """Get queue statistics"""
        if queue_name:
            queues = JobQueue.objects.filter(name=queue_name)
        else:
            queues = JobQueue.objects.all()
        
        stats = {}
        for queue in queues:
            queue_stats = {
                'name': queue.name,
                'enabled': queue.enabled,
                'max_concurrent_jobs': queue.max_concurrent_jobs,
                'pending_jobs': ScannerJob.objects.filter(queue=queue, status='pending').count(),
                'running_jobs': ScannerJob.objects.filter(queue=queue, status='running').count(),
                'completed_jobs': ScannerJob.objects.filter(queue=queue, status='completed').count(),
                'failed_jobs': ScannerJob.objects.filter(queue=queue, status='failed').count(),
            }
            stats[queue.name] = queue_stats
        
        return stats
