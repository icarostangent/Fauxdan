"""
Unified management command for masscan that can run directly or queue jobs
"""
import asyncio
import aioredis
import re
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from internet.models import Scan, Port, Host
from internet.lib.proxychains import ProxyChainsConfigurator
from internet.lib.masscan import MasscanConfigurator
from internet.lib.queue_service import QueueManager
from asgiref.sync import sync_to_async


class Command(BaseCommand):
    help = 'Masscan command that can run directly or queue jobs for processing by the scanner service'
    
    def __init__(self):
        super().__init__()
        self.masscan = MasscanConfigurator()
        self.proxychains = ProxyChainsConfigurator()

    def add_arguments(self, parser):
        # Target and basic options
        parser.add_argument(
            '--target', 
            type=str, 
            required=True,
            help='Target IP address or range'
        )
        parser.add_argument(
            '--ports',
            type=lambda x: [int(p.strip()) for p in x.split(',')],  # Split by comma and convert to int
            default=[],
            help='Comma-separated ports to scan (e.g. "80,443,8080")'
        )
        
        # Scan type options
        parser.add_argument(
            '--syn', 
            action='store_true', 
            help='SYN packets'
        )
        parser.add_argument(
            '--tcp', 
            action='store_true', 
            help='TCP packets'
        )
        parser.add_argument(
            '--udp', 
            action='store_true', 
            help='UDP packets'
        )
        parser.add_argument(
            '--use_proxychains', 
            action='store_true', 
            help='Use proxychains'
        )
        parser.add_argument(
            '--resume', 
            action='store_true', 
            help='Resume paused scan'
        )
        
        # Performance options
        parser.add_argument(
            '--rate',
            type=int,
            help='Scan rate in packets per second (e.g. 1000)'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=3600,  # 1 hour default timeout
            help='Maximum scan duration in seconds (default: 3600)'
        )
        
        # Execution mode
        parser.add_argument(
            '--queue',
            action='store_true',
            help='Queue the job for processing by the scanner service instead of running directly'
        )
        
        # Queue options (only used when --queue is specified)
        parser.add_argument(
            '--queue-name',
            type=str,
            default='default',
            help='Queue name (default: default) - only used with --queue'
        )
        parser.add_argument(
            '--priority',
            type=int,
            default=0,
            help='Job priority (higher number = higher priority) - only used with --queue'
        )
        parser.add_argument(
            '--schedule',
            type=str,
            help='Schedule for later execution (ISO format: YYYY-MM-DDTHH:MM:SS) - only used with --queue'
        )
        parser.add_argument(
            '--user',
            type=int,
            help='User ID to associate with the job - only used with --queue'
        )

    def handle(self, *args, **kwargs):
        target = kwargs['target']
        ports = kwargs['ports']
        syn = kwargs['syn']
        tcp = kwargs['tcp']
        udp = kwargs['udp']
        use_proxychains = kwargs['use_proxychains']
        resume = kwargs['resume']
        rate = kwargs['rate']
        timeout = kwargs['timeout']
        queue_mode = kwargs['queue']
        queue_name = kwargs['queue_name']
        priority = kwargs['priority']
        schedule = kwargs['schedule']
        user_id = kwargs['user']

        if queue_mode:
            self._handle_queued_mode(
                target, ports, syn, tcp, udp, use_proxychains, resume, rate, timeout,
                queue_name, priority, schedule, user_id
            )
        else:
            self._handle_direct_mode(
                target, ports, syn, tcp, udp, use_proxychains, resume, rate, timeout
            )

    def _handle_queued_mode(self, target, ports, syn, tcp, udp, use_proxychains, resume, rate, timeout,
                           queue_name, priority, schedule, user_id):
        """Handle queued execution mode"""
        # Build scan options
        scan_options = {}
        if syn:
            scan_options['syn'] = True
        if tcp:
            scan_options['tcp'] = True
        if udp:
            scan_options['udp'] = True
        if use_proxychains:
            scan_options['use_proxychains'] = True
        if rate:
            scan_options['rate'] = rate
        if resume:
            scan_options['resume'] = True
        scan_options['timeout'] = timeout

        # Parse scheduled time
        scheduled_for = None
        if schedule:
            try:
                scheduled_for = datetime.fromisoformat(schedule)
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid schedule format. Use ISO format (YYYY-MM-DDTHH:MM:SS)')
                )
                return

        # Get user if specified
        user = None
        if user_id:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} not found')
                )
                return

        # Create the job
        try:
            job = QueueManager.create_job(
                job_type='masscan',
                target=target,
                queue_name=queue_name,
                ports=ports,
                scan_options=scan_options,
                priority=priority,
                user=user,
                scheduled_for=scheduled_for
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully queued masscan job:\n'
                    f'  Job UUID: {job.job_uuid}\n'
                    f'  Target: {target}\n'
                    f'  Ports: {ports if ports else "default"}\n'
                    f'  Queue: {queue_name}\n'
                    f'  Priority: {priority}\n'
                    f'  Status: {job.status}\n'
                    f'  Scheduled: {scheduled_for or "immediately"}'
                )
            )
            
            # Show how to check status
            self.stdout.write(
                f'\nTo check job status, run:\n'
                f'  python manage.py queue_manager status {job.job_uuid}\n\n'
                f'To list all jobs, run:\n'
                f'  python manage.py queue_manager list'
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to queue job: {str(e)}')
            )

    def _handle_direct_mode(self, target, ports, syn, tcp, udp, use_proxychains, resume, rate, timeout):
        """Handle direct execution mode"""
        # Configure masscan
        self.masscan.set_target(target)
        if syn:
            self.masscan.set_syn()
        if tcp:
            self.masscan.set_tcp()
        if udp:
            self.masscan.set_udp()
        if use_proxychains:
            self.proxychains.set_config()
        if resume:
            self.masscan.set_resume()
        
        if rate:
            self.masscan.set_rate(rate)
        
        if ports:
            self.masscan.set_ports(ports)

        # Create scan record
        scan = Scan.objects.create(scan_command=self.masscan.get_cmd(), scan_type='masscan')

        def process_discovery(host_ip, port_number, proto, current_time, scan):
            """Synchronous function to process a discovered port"""
            # Get or create host
            host_obj, host_created = Host.objects.get_or_create(ip=host_ip)
            
            # Update host's last_seen timestamp
            host_obj.last_seen = current_time
            host_obj.save()
            
            # Check if this port already exists for this host
            existing_port = Port.objects.filter(
                host=host_obj,
                port_number=port_number,
                proto=proto
            ).first()
            
            if existing_port:
                # Update existing port's last_seen timestamp and status
                existing_port.last_seen = current_time
                existing_port.status = 'open'
                existing_port.save()
                return f'Updated existing port: {host_ip}:{port_number}/{proto}', host_created
            else:
                # Create new port
                Port.objects.create(
                    scan=scan,
                    port_number=port_number,
                    proto=proto,
                    host=host_obj,
                    last_seen=current_time,
                    status='open'
                )
                return f'New port discovered: {host_ip}:{port_number}/{proto}', host_created

        async def parse_stdout(stdout_line, redis):
            """Parse a line of stdout looking for port, protocol, and host information and send to Redis"""
            # Match pattern like: "Discovered open port 80/tcp on 192.168.1.1"
            port_pattern = r'Discovered open port (\d+)/(\w+) on ([0-9\.]+)'
            match = re.search(port_pattern, stdout_line)
            if match:
                port_number = int(match.group(1))
                proto = match.group(2)  # 'tcp' or 'udp'
                host_ip = match.group(3)      # IP address
                current_time = timezone.now()
                
                # Process the discovery synchronously
                result, host_created = await sync_to_async(process_discovery)(host_ip, port_number, proto, current_time, scan)
                
                if host_created:
                    self.stdout.write(self.style.SUCCESS(f'New host discovered: {host_ip}'))
                
                self.stdout.write(result)
            return None

        async def process_runner(command, redis):
            """Run the process and handle output with timeout"""
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Handle stdout and stderr concurrently
            async def read_stream(stream, cb, redis):
                """Run the process and handle output"""
                buffer = b''
                while True:
                    chunk = await stream.read(1024)  # Read in chunks instead of lines
                    if not chunk:
                        break
                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        line_str = line.decode('utf-8').strip()
                        if cb:
                            await cb(line_str, redis)
                        print(line_str)
                
                # Process any remaining data
                if buffer:
                    line_str = buffer.decode('utf-8').strip()
                    if cb:
                        await cb(line_str, redis)
                    print(line_str)

            # Create tasks for both stdout and stderr
            stdout_task = asyncio.create_task(read_stream(process.stdout, parse_stdout, redis))
            stderr_task = asyncio.create_task(read_stream(process.stderr, None, redis))

            try:
                # Wait for both streams and process to complete with timeout
                await asyncio.wait_for(
                    asyncio.gather(stdout_task, stderr_task, process.wait()),
                    timeout=timeout
                )
                return process.returncode
            except asyncio.TimeoutError:
                self.stdout.write(
                    self.style.WARNING(f'Scan timed out after {timeout} seconds. Terminating process...')
                )
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
                
                return -1  # Return error code for timeout

        async def main():
            redis = await aioredis.from_url(f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}')
            try:
                self.stdout.write(self.style.SUCCESS(f'Running masscan command: {self.masscan.get_cmd()}'))
                self.stdout.write(self.style.SUCCESS(f'Timeout set to: {timeout} seconds'))
                return_code = await process_runner(self.masscan.get_cmd(), redis)
                
                if return_code == -1:
                    # Timeout occurred
                    await sync_to_async(setattr)(scan, 'status', 'timeout')
                    await sync_to_async(setattr)(scan, 'end_time', timezone.now())
                    await sync_to_async(lambda: scan.save())()
                    self.stdout.write(self.style.ERROR('Scan timed out and was terminated'))
                elif return_code == 0:
                    # Success
                    await sync_to_async(setattr)(scan, 'status', 'completed')
                    await sync_to_async(setattr)(scan, 'end_time', timezone.now())
                    await sync_to_async(lambda: scan.save())()
                    self.stdout.write(self.style.SUCCESS('Scan completed successfully'))
                else:
                    # Error
                    await sync_to_async(setattr)(scan, 'status', 'failed')
                    await sync_to_async(setattr)(scan, 'end_time', timezone.now())
                    await sync_to_async(lambda: scan.save())()
                    self.stdout.write(self.style.ERROR(f'Scan failed with return code: {return_code}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Command failed with error: {str(e)}'))
                await sync_to_async(setattr)(scan, 'status', 'failed')
                await sync_to_async(setattr)(scan, 'end_time', timezone.now())
                await sync_to_async(lambda: scan.save())()
            finally:
                await redis.close()
        
        async def handle_interrupt():
            self.stdout.write(self.style.WARNING('Shutting down gracefully...'))
            await sync_to_async(setattr)(scan, 'status', 'interrupted')
            await sync_to_async(setattr)(scan, 'end_time', timezone.now())
            await sync_to_async(lambda: scan.save())()

        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            asyncio.run(handle_interrupt())
