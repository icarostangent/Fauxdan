import os
from django.conf import settings

class MasscanConfigurator:
    def __init__(self):
        self.masscan_path = '/usr/bin/masscan'
        self.config_file = 'masscan.conf'
        self.target = ''
        self.top_ports = False
        self.UDP = '' # '-sU'
        self.TCP = '' # '-sT'
        self.SYN = '-sS'
        self.banners = False
        self.wait = '0'
        self.rate = settings.MASSCAN_RATE
        self.exclude_file = 'masscan/exclude.conf'
        self.resume = False
        self.all_ports = False
        # self.rotate = '30'
        # self.rotate_dir = 'masscan/output/'
        # self.output_format = 'json'
        # self.output_filename = 'masscan.json'
        # Default ports list covering major services
        self.ports = [
            # HTTP/HTTPS
            '80,443,8080,8443,8888,8000,8081,8082,8083,8084,8085,8086,8087,8088,8089,8090',
            # Databases
            '1433,1434,3306,3307,5432,5433,6379,27017,27018,27019,6380,6381,9200,9300',  # SQL Server, MySQL, PostgreSQL, Redis, MongoDB, Elasticsearch
            # Mail
            '25,465,587,110,995,143,993',  # SMTP, POP3, IMAP
            # FTP/SFTP/SSH
            '20,21,22,989,990',
            # DNS
            '53,853',  # DNS over TCP/UDP, DNS over TLS
            # Docker
            '2375,2376,2377,4789,7946',  # Docker API, Swarm, Overlay Network
            # Kubernetes
            '6443,8001,8002,10250,10255,10256,2379,2380',  # API server, etcd, kubelet
            # Proxies/Load Balancers
            '3128,8118,9090,9091,9092,8181,8282',  # Squid, HAProxy, etc.
            # SOCKS Proxies
            '1080,1081,9050,9051,9150',  # SOCKS4/5, Tor
            # LDAP
            '389,636',  # LDAP, LDAPS
            # RPC/RMI
            '111,135,139,445,1099,1098',  # Portmapper, Microsoft RPC, NetBIOS, SMB, Java RMI
            # Monitoring
            '161,162,9100,9090,9093,9094',  # SNMP, Prometheus Node Exporter, Prometheus, Alertmanager
            # VPN/Security
            '500,4500,1194,1723',  # ISAKMP/IKE, OpenVPN, PPTP
            # NoSQL
            '7000,7001,7199,9042,8087',  # Cassandra, CouchDB
            # Message Queues
            '5671,5672,15672,61613,61614,61616',  # RabbitMQ, ActiveMQ
            # Version Control
            '9418,443',  # Git, SVN over HTTPS
            # Remote Access
            '3389,5900,5901,5902',  # RDP, VNC
            # Caching
            '11211,11212,11213,11214,11215',  # Memcached
            # Search
            '8983,8984,8985',  # Solr
            # Development
            '8000,8080,3000,4200,5000,8008,9000'  # Common dev servers (Django, Node, Angular, Flask, etc.)
        ]
        self.ports = ','.join(self.ports)

    def set_masscan_path(self, path):
        self.masscan_path = path

    def set_target(self, target):
        self.target = target

    def set_top_ports(self, enabled=True):
        """
        Enable or disable scanning of predefined top ports.
        When enabled, only the predefined list of common ports will be scanned.
        When disabled, the full port range specified in self.ports will be used.
        """
        self.top_ports = enabled

    def set_ports(self, ports):
        """
        Set ports for scanning. Accepts either a string of comma-separated ports/ranges
        or a list of ports/ranges.
        
        Valid formats:
        - String: '80,443,8000-8100'
        - List: ['80', '443', '8000-8100'] or [80, 443, '8000-8100']
        """
        if isinstance(ports, list):
            # Convert any integer elements to strings
            ports = [str(port) for port in ports]
            self.ports = ','.join(ports)
        elif isinstance(ports, str):
            self.ports = ports
        else:
            raise ValueError("Ports must be provided as a string or list")

        # Setting specific ports disables all-ports mode
        self.all_ports = False

    def set_udp(self, enabled=True):
        self.UDP = '-sU' if enabled else ''

    def set_tcp(self, enabled=True):
        self.TCP = '-sT' if enabled else ''

    def set_syn(self, enabled=True):
        self.SYN = '-sS' if enabled else ''

    def set_rate(self, rate):
        self.rate = str(rate)

    def set_wait(self, wait):
        self.wait = str(wait)

    def set_output_filename(self, filename):
        self.output_filename = filename
    
    def set_resume(self, enabled=True):
        """Enable or disable resume functionality for masscan"""
        # This would typically set a resume file or flag
        # For now, we'll just store the state
        self.resume = enabled
    
    def set_all_ports(self, enabled=True):
        """Enable scanning all ports (equivalent to -p-)"""
        self.all_ports = enabled
    
    def get_cmd(self):
        cmd = [self.masscan_path]

        if self.target:
            cmd.append(self.target)
        
        # Masscan supports specifying both TCP and UDP flags together
        if self.UDP:
            cmd.append(self.UDP)
        if self.TCP:
            cmd.append(self.TCP)
        if self.SYN:
            cmd.append(self.SYN)

        if self.top_ports:
            cmd.append('--top-ports')
        else:
            if self.all_ports:
                cmd.extend(['--ports', '1-65535'])
            else:
                cmd.extend(['--ports', self.ports])
        
        if self.banners:
            cmd.append('--banners')

        cmd.extend(['--wait', str(self.wait)])
        cmd.extend(['--rate', str(self.rate)])
        cmd.extend(['--exclude-file', self.exclude_file])
        
        if self.resume:
            cmd.append('--resume')
        # cmd.extend(['--rotate', self.rotate])
        # cmd.extend(['--rotate-dir', self.rotate_dir])
        # cmd.extend(['--output-format', self.output_format])
        # cmd.extend(['--output-filename', self.output_filename])

        # Filter out empty strings and ensure all elements are strings
        return ' '.join(str(arg) for arg in cmd if arg)
    