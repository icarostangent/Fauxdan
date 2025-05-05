import asyncio
import json
import aioredis
import re
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from internet.models import Scan
from internet.lib.proxychains import ProxyChainsConfigurator
from internet.lib.masscan import MasscanConfigurator
from asgiref.sync import sync_to_async

class Command(BaseCommand):
    help = 'Run masscan'
    def __init__(self):
        super().__init__()
        self.masscan = MasscanConfigurator()
        self.proxychains = ProxyChainsConfigurator()

    def add_arguments(self, parser):
        parser.add_argument(
            '--target', 
            type=str, 
            help='Target IP address or range'
        )
        parser.add_argument(
            '--ports',
            type=lambda x: [int(p.strip()) for p in x.split(',')],  # Split by comma and convert to int
            default=[],
            help='Comma-separated ports to scan (e.g. "80,443,8080")'
        )
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

    def handle(self, *args, **kwargs):
        if not kwargs['target']:
            self.stdout.write(self.style.ERROR('Error: --target is required'))
            return

        self.target = kwargs['target']
        self.ports = kwargs['ports']
        self.syn = kwargs['syn']
        self.tcp = kwargs['tcp']
        self.udp = kwargs['udp']
        self.use_proxychains = kwargs['use_proxychains']
        self.resume = kwargs['resume']

        self.masscan.set_target(self.target)
        if self.syn:
            self.masscan.set_syn()
        if self.tcp:
            self.masscan.set_tcp()
        if self.udp:
            self.masscan.set_udp()
        if self.use_proxychains:
            self.proxychains.set_config()
        if self.resume:
            self.masscan.set_resume()
        
        if self.ports:
            print(self.ports)
            self.masscan.set_ports(self.ports)

        scan = Scan.objects.create(scan_command=self.masscan.get_cmd(), scan_type='masscan')

        async def parse_stdout(stdout_line, redis):
            """Parse a line of stdout looking for port, protocol, and host information and send to Redis"""
            # Match pattern like: "Discovered open port 80/tcp on 192.168.1.1"
            port_pattern = r'Discovered open port (\d+)/(\w+) on ([0-9\.]+)'
            match = re.search(port_pattern, stdout_line)
            if match:
                data = {
                    'scan_id': scan.id,
                    'port': int(match.group(1)),
                    'proto': match.group(2),  # 'tcp' or 'udp'
                    'host': match.group(3),      # IP address
                    'timestamp': timezone.now().isoformat(),
                    'status': 'open'
                }
                # print(data)
                await redis.rpush(settings.REDIS_QUEUE_PORT_SCANNER, json.dumps(data))
            return None

        async def process_runner(command, redis):
            """Run the process and handle output"""
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

            # Wait for both streams and process to complete
            await asyncio.gather(stdout_task, stderr_task)
            await process.wait()

            return process.returncode

        async def main():
            redis = await aioredis.from_url(f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}')
            try:
                self.stdout.write(self.style.SUCCESS(f'Running masscan command: {self.masscan.get_cmd()}'))
                return_code = await process_runner(self.masscan.get_cmd(), redis)
                # Wrap the database operations with sync_to_async
                await sync_to_async(scan.save)()
                await sync_to_async(setattr)(scan, 'status', 'completed')
                await sync_to_async(setattr)(scan, 'end_time', timezone.now())
                await sync_to_async(scan.save)()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Command failed with error: {str(e)}'))
                await sync_to_async(setattr)(scan, 'status', 'failed')
                await sync_to_async(setattr)(scan, 'end_time', timezone.now())
                await sync_to_async(scan.save)()
            finally:
                await redis.close()
        
        async def handle_interrupt():
            self.stdout.write(self.style.WARNING('Shutting down gracefully...'))
            await sync_to_async(setattr)(scan, 'status', 'interrupted')
            await sync_to_async(setattr)(scan, 'end_time', timezone.now())
            await sync_to_async(scan.save)()

        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            asyncio.run(handle_interrupt())