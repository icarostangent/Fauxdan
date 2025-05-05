import subprocess
import ipaddress
from typing import Generator
from django.core.management.base import BaseCommand
from internet.models import Host

class Command(BaseCommand):
    help = 'Generate IPv4 addresses using masscan and stores them in the database'

    def __init__(self):
        super().__init__()
        self.batch_size = 1000

    def add_arguments(self, parser):
        parser.add_argument(
            '--target',
            type=str,
            help='Target IP address or range'
        )

    def handle(self, *args, **options):
        target = options['target']
        
        # Build masscan command
        cmd = [
            'masscan',
            '-sL',
            target, 
        ]

        self.stdout.write(f'Starting masscan... {" ".join(cmd)}')
        
        # Start masscan process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        try:
            # Process output line by line
            for line in self._read_process_output(process):
                try:
                    ip = ipaddress.ip_address(line.strip())
                    if ip.version == 4:  # Ensure IPv4
                        _, created = Host.objects.get_or_create(ip=str(ip))
                        if created:
                            self.stdout.write(f'Inserted {str(ip)}')
                        else:
                            self.stdout.write(f'Skipped {str(ip)}')
                            
                except ValueError:
                    continue  # Skip invalid IP addresses
                
        except KeyboardInterrupt:
            self.stdout.write('\nScan interrupted by user')
        finally:
            process.terminate()
            process.wait()  # Wait for process to terminate
            
        self.stdout.write(self.style.SUCCESS('Scan completed'))

    def _read_process_output(self, process) -> Generator[str, None, None]:
        """Read process output line by line."""
        while True:
            # Check if process has terminated
            if process.poll() is not None:
                # Read any remaining data
                remaining = process.stdout.readlines()
                for line in remaining:
                    yield line.strip()
                break
            
            # Read available data
            line = process.stdout.readline()
            if line:
                yield line.strip()
