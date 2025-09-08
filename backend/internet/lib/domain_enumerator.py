import socket
import asyncio
import logging
import ssl
from typing import Optional, List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import re

# Optional DNS imports - handle gracefully if not available
try:
    import dns.resolver
    import dns.reversename
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("dnspython not available - DNS enumeration will be limited")

logger = logging.getLogger(__name__)


class DomainEnumerator:
    """Utility class for enumerating domains from IP addresses"""
    
    def __init__(self, timeout: int = 5, max_workers: int = 20):
        self.timeout = timeout
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def enumerate_domains(self, host_ip: str) -> List[str]:
        """
        Enumerate domains for a given IP address
        
        Args:
            host_ip: IP address to enumerate domains for
            
        Returns:
            List of domain names found
        """
        try:
            # Run domain enumeration in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            domains = await loop.run_in_executor(
                self.executor, 
                self._enumerate_domains_sync, 
                host_ip
            )
            return domains
        except Exception as e:
            logger.debug(f"Failed to enumerate domains for {host_ip}: {e}")
            return []
    
    def _enumerate_domains_sync(self, host_ip: str) -> List[str]:
        """Synchronous domain enumeration function"""
        domains = set()
        
        try:
            # 1. Reverse DNS lookup
            try:
                reverse_dns = socket.gethostbyaddr(host_ip)[0]
                if reverse_dns and reverse_dns != host_ip:
                    domains.add(reverse_dns)
            except (socket.herror, socket.gaierror):
                pass
            
            # 2. SSL certificate enumeration
            ssl_domains = self._get_ssl_domains(host_ip)
            domains.update(ssl_domains)
            
            # 3. HTTP/HTTPS response headers
            http_domains = self._get_http_domains(host_ip)
            domains.update(http_domains)
            
            # 4. DNS PTR record lookup
            dns_domains = self._get_dns_domains(host_ip)
            domains.update(dns_domains)
            
            # Filter and clean domains
            cleaned_domains = []
            for domain in domains:
                if self._is_valid_domain(domain):
                    cleaned_domains.append(domain.lower().strip())
            
            return list(set(cleaned_domains))
            
        except Exception as e:
            logger.debug(f"Domain enumeration failed for {host_ip}: {e}")
            return []
    
    def _get_ssl_domains(self, host_ip: str) -> List[str]:
        """Get domains from SSL certificates"""
        domains = set()
        
        # Common HTTPS ports
        https_ports = [443, 8443, 9443, 10443]
        
        for port in https_ports:
            try:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with socket.create_connection((host_ip, port), timeout=self.timeout) as sock:
                    with context.wrap_socket(sock, server_hostname=host_ip) as ssock:
                        cert = ssock.getpeercert()
                        
                        # Get Common Name
                        if 'subject' in cert:
                            for item in cert['subject']:
                                for key, value in item:
                                    if key == 'commonName':
                                        domains.add(value)
                        
                        # Get Subject Alternative Names
                        if 'subjectAltName' in cert:
                            for san_type, san_value in cert['subjectAltName']:
                                if san_type == 'DNS':
                                    domains.add(san_value)
                                    
            except Exception:
                continue
        
        return list(domains)
    
    def _get_http_domains(self, host_ip: str) -> List[str]:
        """Get domains from HTTP response headers"""
        domains = set()
        
        # Common HTTP ports
        http_ports = [80, 8080, 8000, 8008, 8888, 3000, 5000]
        
        for port in http_ports:
            try:
                with socket.create_connection((host_ip, port), timeout=self.timeout) as sock:
                    # Send HTTP request
                    request = f"GET / HTTP/1.1\r\nHost: {host_ip}\r\n\r\n"
                    sock.send(request.encode())
                    
                    # Read response
                    response = sock.recv(4096).decode('utf-8', errors='ignore')
                    
                    # Look for domain patterns in headers
                    domain_patterns = [
                        r'Server:\s*([^\r\n]+)',
                        r'X-Powered-By:\s*([^\r\n]+)',
                        r'Location:\s*https?://([^/\r\n]+)',
                        r'Set-Cookie:.*domain=([^;\r\n]+)',
                    ]
                    
                    for pattern in domain_patterns:
                        matches = re.findall(pattern, response, re.IGNORECASE)
                        for match in matches:
                            if self._is_valid_domain(match):
                                domains.add(match)
                                
            except Exception:
                continue
        
        return list(domains)
    
    def _get_dns_domains(self, host_ip: str) -> List[str]:
        """Get domains from DNS PTR records"""
        domains = set()
        
        if not DNS_AVAILABLE:
            return list(domains)
        
        try:
            # Create reverse DNS query
            reverse_name = dns.reversename.from_address(host_ip)
            
            # Query PTR record
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout
            
            answers = resolver.resolve(reverse_name, 'PTR')
            for answer in answers:
                domain = str(answer).rstrip('.')
                if self._is_valid_domain(domain):
                    domains.add(domain)
                    
        except Exception:
            pass
        
        return list(domains)
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Check if a string is a valid domain name"""
        if not domain or len(domain) > 253:
            return False
        
        # Basic domain validation
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        
        if not re.match(domain_pattern, domain):
            return False
        
        # Must have at least one dot
        if '.' not in domain:
            return False
        
        # Must not be an IP address
        try:
            socket.inet_aton(domain)
            return False
        except socket.error:
            pass
        
        return True
    
    async def enumerate_domains_batch(self, host_ips: List[str]) -> Dict[str, List[str]]:
        """
        Enumerate domains for multiple IP addresses in batch
        
        Args:
            host_ips: List of IP addresses
            
        Returns:
            Dictionary mapping IP to list of domains
        """
        tasks = []
        for host_ip in host_ips:
            task = self.enumerate_domains(host_ip)
            tasks.append((host_ip, task))
        
        results = {}
        for host_ip, task in tasks:
            try:
                domains = await task
                if domains:
                    results[host_ip] = domains
            except Exception as e:
                logger.debug(f"Batch domain enumeration failed for {host_ip}: {e}")
        
        return results
    
    def cleanup(self):
        """Clean up resources"""
        if self.executor:
            self.executor.shutdown(wait=True)


# Global domain enumerator instance
_domain_enumerator = None

def get_domain_enumerator() -> DomainEnumerator:
    """Get the global domain enumerator instance"""
    global _domain_enumerator
    if _domain_enumerator is None:
        _domain_enumerator = DomainEnumerator()
    return _domain_enumerator
