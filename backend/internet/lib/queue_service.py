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
from internet.models import ScannerJob, JobQueue, JobWorker, Scan, AncillaryJob

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
        """Main loop for processing jobs (both ScannerJob and AncillaryJob)"""
        while self.running:
            try:
                # Check if we can accept more jobs
                available_slots = max(0, self.worker.max_concurrent_jobs - len(self.current_jobs))
                if available_slots > 0:
                    # Prefer one scanner job if available
                    scanner_job = await self._get_next_job()
                    if scanner_job:
                        asyncio.create_task(self._process_job(scanner_job))
                        available_slots -= 1
                    # Fill remaining with ancillary jobs in batches
                    if available_slots > 0:
                        ancillary_jobs = await self._get_next_ancillary_jobs(available_slots)
                        for aj in ancillary_jobs:
                            asyncio.create_task(self._process_post_discovery_analysis_job(aj))
                
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
    
    async def _get_next_ancillary_jobs(self, max_jobs: int) -> List['AncillaryJob']:
        """Get up to max_jobs ancillary jobs using priority and type ordering"""
        from asgiref.sync import sync_to_async
        from internet.models import AncillaryJob
        from django.conf import settings

        def _get_batch():
            # Get the next pending ancillary job that matches our supported job types
            # Prefer ssl_cert, then banner_grab, then domain_enum to avoid starvation
            supported_ancillary_types = [jt for jt in self.worker.supported_job_types 
                                       if jt in ['ssl_cert', 'banner_grab', 'domain_enum', 'service_detection', 'vulnerability_scan']]

            if not supported_ancillary_types:
                return []

            # Priority order within supported types
            type_priority = ['ssl_cert', 'banner_grab', 'domain_enum']
            batch_size = min(max_jobs, getattr(settings, 'ANCILLARY_BATCH_SIZE', 5))
            selected: List[AncillaryJob] = []

            # Pull by type priority first
            for jt in type_priority:
                if len(selected) >= batch_size:
                    break
                if jt not in supported_ancillary_types:
                    continue
                needed = batch_size - len(selected)
                jobs = list(
                    AncillaryJob.objects.filter(status='pending', job_type=jt)
                    .order_by('-priority', 'created_at')[:needed]
                )
                for job in jobs:
                    job.assigned_worker = self.worker
                    job.status = 'running'
                    job.save()
                selected.extend(jobs)

            # Fallback fill from any supported types
            if len(selected) < batch_size:
                needed = batch_size - len(selected)
                extras = list(
                    AncillaryJob.objects.filter(status='pending', job_type__in=supported_ancillary_types)
                    .order_by('-priority', 'created_at')[:needed]
                )
                for job in extras:
                    job.assigned_worker = self.worker
                    job.status = 'running'
                    job.save()
                selected.extend(extras)

            return selected
        
        return await sync_to_async(_get_batch)()
    
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
        if scan_options.get('tcp_udp', False):
            masscan.set_tcp(True)
            masscan.set_udp(True)
        if scan_options.get('use_proxychains', False):
            proxychains = ProxyChainsConfigurator()
            proxychains.set_config()
        
        if scan_options.get('rate'):
            masscan.set_rate(scan_options['rate'])
        
        if scan_options.get('resume', False):
            masscan.set_resume()
        if scan_options.get('all_ports', False):
            masscan.set_all_ports(True)
        
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
        from .banner_grabber import get_banner_grabber
        
        # Store discovered ports for banner grabbing
        discovered_ports = []
        
        def process_discovery(host_ip, port_number, proto, current_time, scan):
            """Process a discovered port and queue ancillary jobs"""
            from internet.models import Host, Port, AncillaryJob
            
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
                port_obj = existing_port
            else:
                port_obj = Port.objects.create(
                    scan=scan,
                    port_number=port_number,
                    proto=proto,
                    host=host_obj,
                    last_seen=current_time,
                    status='open'
                )
            
            # Queue banner grab job for this port
            banner_job = AncillaryJob.objects.create(
                job_type='banner_grab',
                host_ip=host_ip,
                port_number=port_number,
                protocol=proto,
                port=port_obj,
                host=host_obj,
                scanner_job=job,
                status='pending',
                priority=0
            )
            
            # Queue domain enumeration job for this host (only once per host)
            if host_created or not AncillaryJob.objects.filter(
                host=host_obj, 
                job_type='domain_enum', 
                status__in=['pending', 'running', 'completed']
            ).exists():
                domain_job = AncillaryJob.objects.create(
                    job_type='domain_enum',
                    host_ip=host_ip,
                    host=host_obj,
                    scanner_job=job,
                    status='pending',
                    priority=1  # Lower priority than banner grab
                )
            
            # Queue geolocation job for this host (only once per host or if data is stale)
            should_queue_geo = False
            if host_created:
                should_queue_geo = True
            elif host_obj.needs_geolocation_update():
                should_queue_geo = True
            
            if should_queue_geo and not AncillaryJob.objects.filter(
                host=host_obj,
                job_type='geolocation',
                status__in=['pending', 'running', 'completed']
            ).exists():
                geo_job = AncillaryJob.objects.create(
                    job_type='geolocation',
                    host_ip=host_ip,
                    host=host_obj,
                    scanner_job=job,
                    status='pending',
                    priority=2  # Lower priority than banner/domain jobs
                )
            
            # Queue SSL certificate job for HTTPS ports
            if port_number in [443, 8443, 9443, 10443]:
                ssl_job = AncillaryJob.objects.create(
                    job_type='ssl_cert',
                    host_ip=host_ip,
                    port_number=port_number,
                    protocol=proto,
                    port=port_obj,
                    host=host_obj,
                    scanner_job=job,
                    status='pending',
                    priority=2  # Lower priority than banner grab
                )
            
            return f'Queued ancillary jobs for {host_ip}:{port_number}/{proto}', host_created, port_obj
        
        async def parse_stdout(stdout_line):
            """Parse masscan output"""
            port_pattern = r'Discovered open port (\d+)/(\w+) on ([0-9\.]+)'
            match = re.search(port_pattern, stdout_line)
            if match:
                port_number = int(match.group(1))
                proto = match.group(2)
                host_ip = match.group(3)
                current_time = timezone.now()
                
                result, host_created, port_obj = await sync_to_async(process_discovery)(
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
            
            # Banner grab jobs have been queued during port discovery
            logger.info("Masscan completed. Banner grab jobs have been queued for processing.")
                
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
    
    async def _process_post_discovery_analysis_job(self, job: 'AncillaryJob'):
        """Process a single post-discovery analysis job (banner grab, domain enum, SSL cert, etc.)"""
        from asgiref.sync import sync_to_async
        
        job_id = f"ancillary_{job.job_uuid}"
        self.current_jobs[job_id] = job
        
        try:
            logger.info(f"Processing ancillary job {job_id}: {job.job_type} - {job.host_ip}:{job.port_number}")
            
            # Process based on job type
            if job.job_type == 'banner_grab':
                result_data = await self._process_banner_grab(job)
            elif job.job_type == 'domain_enum':
                result_data = await self._process_domain_enum(job)
            elif job.job_type == 'ssl_cert':
                result_data = await self._process_ssl_cert(job)
            elif job.job_type == 'geolocation':
                result_data = await self._process_geolocation(job)
            else:
                logger.warning(f'Unknown job type: {job.job_type}')
                result_data = {'error': f'Unknown job type: {job.job_type}'}
            
            # Mark job as completed
            def _mark_completed():
                from django.db import transaction
                with transaction.atomic():
                    job.status = 'completed'
                    job.completed_at = timezone.now()
                    if result_data:
                        job.result_data = result_data
                    job.save(update_fields=['status', 'completed_at', 'result_data'])
            
            await sync_to_async(_mark_completed)()
            logger.info(f"Completed ancillary job {job_id}")
            
        except Exception as e:
            logger.error(f"Ancillary job {job_id} failed: {e}")
            
            def _mark_failed():
                from django.db import transaction
                with transaction.atomic():
                    job.status = 'failed'
                    job.completed_at = timezone.now()
                    job.error_message = str(e)
                    job.save(update_fields=['status', 'completed_at', 'error_message'])
            
            await sync_to_async(_mark_failed)()
        finally:
            # Clean up
            if job_id in self.current_jobs:
                del self.current_jobs[job_id]
    
    async def _process_banner_grab(self, job: 'AncillaryJob') -> dict:
        """Process banner grab job with intelligent analysis and follow-up queuing"""
        from .banner_grabber import get_banner_grabber
        from .banner_analyzer import BannerAnalyzer
        from asgiref.sync import sync_to_async
        
        banner_grabber = get_banner_grabber()
        banner_analyzer = BannerAnalyzer()
        
        # Grab banner
        banner = await banner_grabber.grab_banner(
            job.host_ip, 
            job.port_number, 
            job.protocol
        )
        
        result_data = {'banner': banner or ''}
        
        if banner and job.port_id:
            # Update port with banner
            def update_port_banner():
                try:
                    from internet.models import Port
                    # Avoid relation access in async context by using the FK id
                    Port.objects.filter(id=job.port_id).update(banner=banner)
                except Exception as e:
                    logger.warning(f"Failed to update port banner: {e}")
            
            await sync_to_async(update_port_banner)()
            
            # Analyze banner for intelligent follow-up actions
            detections = banner_analyzer.analyze_banner(banner, job.port_number)
            
            # Queue SSL certificate grab if appropriate
            if banner_analyzer.should_queue_ssl_cert(detections):
                await self._queue_ssl_cert_job(job, detections)
            
            # Queue domain enumeration if appropriate
            if banner_analyzer.should_queue_domain_enum(detections):
                await self._queue_domain_enum_job(job, detections)
            
            # Add detection results to the banner grab result
            result_data['detections'] = [
                {
                    'service_type': detection.service_type.value,
                    'confidence': detection.confidence,
                    'version': detection.version,
                    'additional_info': detection.additional_info
                }
                for detection in detections
            ]
        
        return result_data
    
    async def _queue_ssl_cert_job(self, banner_job: 'AncillaryJob', detections: List) -> None:
        """Queue SSL certificate grab job based on banner analysis"""
        from asgiref.sync import sync_to_async
        from internet.models import AncillaryJob
        
        # Check if SSL cert job already exists for this host:port
        def check_existing_job():
            return AncillaryJob.objects.filter(
                job_type='ssl_cert',
                host_ip=banner_job.host_ip,
                port_number=banner_job.port_number,
                status__in=['pending', 'running', 'queued']
            ).exists()
        
        existing = await sync_to_async(check_existing_job)()
        if existing:
            return
        
        # Determine priority based on detection confidence
        priority = 0
        for detection in detections:
            if detection.service_type.value == 'https':
                priority = max(priority, int(detection.confidence * 10))
        
        # Create SSL cert job
        def create_ssl_job():
            try:
                return AncillaryJob.objects.create(
                    job_type='ssl_cert',
                    host_ip=banner_job.host_ip,
                    port_number=banner_job.port_number,
                    protocol=banner_job.protocol,
                    # Use *_id fields to avoid relation resolution in async context
                    port_id=banner_job.port_id,
                    host_id=banner_job.host_id,
                    scanner_job_id=banner_job.scanner_job_id,
                    status='pending',
                    priority=priority,
                    metadata={'triggered_by': 'banner_analysis'}
                )
            except Exception as e:
                logger.warning(f"Failed to create SSL cert job: {e}")
                return None
        
        result = await sync_to_async(create_ssl_job)()
        if result:
            logger.info(f"Queued SSL cert job for {banner_job.host_ip}:{banner_job.port_number}")
    
    async def _queue_domain_enum_job(self, banner_job: 'AncillaryJob', detections: List) -> None:
        """Queue domain enumeration job based on banner analysis"""
        from asgiref.sync import sync_to_async
        from internet.models import AncillaryJob
        
        # Check if domain enum job already exists for this host
        def check_existing_job():
            return AncillaryJob.objects.filter(
                job_type='domain_enum',
                host_ip=banner_job.host_ip,
                status__in=['pending', 'running', 'queued']
            ).exists()
        
        existing = await sync_to_async(check_existing_job)()
        if existing:
            return
        
        # Determine priority based on detection confidence
        priority = 0
        for detection in detections:
            if detection.service_type.value in ['http', 'https']:
                priority = max(priority, int(detection.confidence * 10))
        
        # Create domain enum job
        def create_domain_job():
            try:
                return AncillaryJob.objects.create(
                    job_type='domain_enum',
                    host_ip=banner_job.host_ip,
                    port_number=None,  # Domain enum is host-level, not port-specific
                    protocol='tcp',
                    port=None,
                    # Use *_id fields to avoid relation resolution in async context
                    host_id=banner_job.host_id,
                    scanner_job_id=banner_job.scanner_job_id,
                    status='pending',
                    priority=priority,
                    metadata={'triggered_by': 'banner_analysis'}
                )
            except Exception as e:
                logger.warning(f"Failed to create domain enum job: {e}")
                return None
        
        result = await sync_to_async(create_domain_job)()
        if result:
            logger.info(f"Queued domain enum job for {banner_job.host_ip}")
    
    async def _process_domain_enum(self, job: 'AncillaryJob') -> dict:
        """Process domain enumeration job"""
        from .domain_enumerator import get_domain_enumerator
        from asgiref.sync import sync_to_async
        from internet.models import Domain
        
        domain_enumerator = get_domain_enumerator()
        
        # Enumerate domains
        domains = await domain_enumerator.enumerate_domains(job.host_ip)
        
        result_data = {'domains': domains}
        
        if domains and job.host_id:
            # Save domains to database using sync_to_async
            def save_domains():
                for domain_name in domains:
                    domain, created = Domain.objects.get_or_create(
                        name=domain_name,
                        defaults={'host_id': job.host_id}
                    )
                    if not created and domain.host_id != job.host_id:
                        domain.host_id = job.host_id
                        domain.save()
            
            await sync_to_async(save_domains)()
        
        return result_data
    
    async def _process_ssl_cert(self, job: 'AncillaryJob') -> dict:
        """Process SSL certificate grab job"""
        from .ssl_cert_grabber import get_ssl_cert_grabber
        from asgiref.sync import sync_to_async
        from internet.models import SSLCertificate

        ssl_cert_grabber = get_ssl_cert_grabber()

        # Grab SSL certificate
        port_number = job.port_number or 443
        cert_data = await ssl_cert_grabber.grab_certificate(job.host_ip, port_number)

        result_data = {'certificate': cert_data} if cert_data else {'certificate': None}

        # Map grabber data -> model fields
        if cert_data and job.host_id and job.port_id:
            def save_ssl_cert():
                # The model uses unique fingerprint; prefer sha256 if available else sha1
                fingerprint = cert_data.get('fingerprint_sha256') or cert_data.get('fingerprint_sha1') or ''
                pem_hex = cert_data.get('raw_certificate', '')

                ssl_cert, created = SSLCertificate.objects.get_or_create(
                    fingerprint=fingerprint,
                    defaults={
                        'pem_data': pem_hex,
                        'subject_cn': (cert_data.get('subject') or {}).get('commonName') or (cert_data.get('subject') or {}).get('CN') or None,
                        'issuer_cn': (cert_data.get('issuer') or {}).get('commonName') or (cert_data.get('issuer') or {}).get('CN') or None,
                        'valid_from': cert_data.get('not_before') or '',
                        'valid_until': cert_data.get('not_after') or '',
                        'host_id': job.host_id,
                        'port_id': job.port_id,
                    }
                )

                if not created:
                    # Update fields if anything changed
                    ssl_cert.pem_data = pem_hex or ssl_cert.pem_data
                    ssl_cert.subject_cn = (cert_data.get('subject') or {}).get('commonName') or ssl_cert.subject_cn
                    ssl_cert.issuer_cn = (cert_data.get('issuer') or {}).get('commonName') or ssl_cert.issuer_cn
                    ssl_cert.valid_from = cert_data.get('not_before') or ssl_cert.valid_from
                    ssl_cert.valid_until = cert_data.get('not_after') or ssl_cert.valid_until
                    # Ensure FK associations are intact
                    if ssl_cert.host_id != job.host_id:
                        ssl_cert.host_id = job.host_id
                    if ssl_cert.port_id != job.port_id:
                        ssl_cert.port_id = job.port_id
                    ssl_cert.save()

            await sync_to_async(save_ssl_cert)()

        return result_data
    
    async def _process_geolocation(self, job: 'AncillaryJob') -> dict:
        """Process geolocation job for a host"""
        from asgiref.sync import sync_to_async
        from internet.lib.geolocation import get_ip_geolocation_async
        from internet.models import Host
        import ipaddress
        
        logger.info(f"Processing geolocation for {job.host_ip}")
        
        # Skip private IP addresses
        try:
            ip_obj = ipaddress.ip_address(job.host_ip)
            if ip_obj.is_private:
                logger.info(f"Skipping geolocation for private IP: {job.host_ip}")
                return {'geolocation': None, 'reason': 'private_ip'}
        except ValueError:
            logger.warning(f"Invalid IP address format: {job.host_ip}")
            return {'geolocation': None, 'reason': 'invalid_ip'}
        
        # Get geolocation data using async service
        try:
            location_data = await get_ip_geolocation_async(job.host_ip)
            
            if location_data:
                # Update host with geolocation data
                def update_host():
                    try:
                        host = Host.objects.get(id=job.host_id)
                        host.country = location_data.get('country')
                        host.country_code = location_data.get('country_code')
                        host.region = location_data.get('region')
                        host.city = location_data.get('city')
                        host.latitude = location_data.get('latitude')
                        host.longitude = location_data.get('longitude')
                        host.timezone = location_data.get('timezone')
                        host.isp = location_data.get('isp')
                        host.organization = location_data.get('organization')
                        host.asn = location_data.get('asn')
                        host.geolocation_updated = timezone.now()
                        host.save()
                        return True
                    except Exception as e:
                        logger.error(f"Failed to update host {job.host_ip} with geolocation: {e}")
                        return False
                
                success = await sync_to_async(update_host)()
                
                if success:
                    logger.info(f"✓ {job.host_ip} -> {location_data.get('city', 'Unknown')}, "
                              f"{location_data.get('country', 'Unknown')} "
                              f"({location_data.get('provider', 'Unknown')})")
                    return {'geolocation': location_data, 'updated': True}
                else:
                    return {'geolocation': location_data, 'updated': False, 'reason': 'db_error'}
            else:
                logger.info(f"✗ Failed to geolocate {job.host_ip}")
                # Still update the timestamp to avoid repeated attempts
                def update_timestamp():
                    try:
                        host = Host.objects.get(id=job.host_id)
                        host.geolocation_updated = timezone.now()
                        host.save(update_fields=['geolocation_updated'])
                        return True
                    except Exception as e:
                        logger.error(f"Failed to update timestamp for {job.host_ip}: {e}")
                        return False
                
                await sync_to_async(update_timestamp)()
                return {'geolocation': None, 'reason': 'no_data'}
                
        except Exception as e:
            logger.error(f"Error during geolocation for {job.host_ip}: {e}")
            return {'geolocation': None, 'reason': 'error', 'error': str(e)}
    
    
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
