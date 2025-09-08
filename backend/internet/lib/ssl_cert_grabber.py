import socket
import asyncio
import logging
import ssl
import json
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class SSLCertGrabber:
    """Utility class for grabbing SSL certificates from hosts"""
    
    def __init__(self, timeout: int = 5, max_workers: int = 20):
        self.timeout = timeout
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def grab_certificate(self, host_ip: str, port: int = 443) -> Optional[Dict]:
        """
        Grab SSL certificate from a specific host:port combination
        
        Args:
            host_ip: IP address
            port: Port number (default: 443)
            
        Returns:
            Certificate data dictionary or None if no certificate found
        """
        try:
            # Run certificate grabbing in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            cert_data = await loop.run_in_executor(
                self.executor, 
                self._grab_certificate_sync, 
                host_ip, 
                port
            )
            return cert_data
        except Exception as e:
            logger.debug(f"Failed to grab SSL certificate from {host_ip}:{port}: {e}")
            return None
    
    def _grab_certificate_sync(self, host_ip: str, port: int) -> Optional[Dict]:
        """Synchronous certificate grabbing function"""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            with socket.create_connection((host_ip, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host_ip) as ssock:
                    cert = ssock.getpeercert()
                    cert_der = ssock.getpeercert(binary_form=True)
                    
                    if cert and cert_der:
                        return self._process_certificate(cert, cert_der, host_ip, port)
            
            return None
            
        except Exception as e:
            logger.debug(f"SSL certificate grab failed for {host_ip}:{port}: {e}")
            return None
    
    def _process_certificate(self, cert: Dict, cert_der: bytes, host_ip: str, port: int) -> Dict:
        """Process and format certificate data"""
        try:
            # Extract certificate information
            cert_data = {
                'host_ip': host_ip,
                'port': port,
                'subject': self._extract_subject(cert.get('subject', [])),
                'issuer': self._extract_subject(cert.get('issuer', [])),
                'version': cert.get('version'),
                'serial_number': cert.get('serialNumber'),
                'not_before': cert.get('notBefore'),
                'not_after': cert.get('notAfter'),
                'fingerprint_sha1': self._get_certificate_fingerprint(cert_der, 'sha1'),
                'fingerprint_sha256': self._get_certificate_fingerprint(cert_der, 'sha256'),
                'signature_algorithm': cert.get('signatureAlgorithm'),
                'public_key_info': self._extract_public_key_info(cert),
                'extensions': self._extract_extensions(cert),
                'domains': self._extract_domains(cert),
                'raw_certificate': cert_der.hex() if cert_der else None,
                'created_at': datetime.utcnow().isoformat()
            }
            
            return cert_data
            
        except Exception as e:
            logger.debug(f"Certificate processing failed: {e}")
            return None
    
    def _extract_subject(self, subject_list: List) -> Dict:
        """Extract subject information from certificate"""
        subject = {}
        for item in subject_list:
            for key, value in item:
                if key in subject:
                    if isinstance(subject[key], list):
                        subject[key].append(value)
                    else:
                        subject[key] = [subject[key], value]
                else:
                    subject[key] = value
        return subject
    
    def _extract_public_key_info(self, cert: Dict) -> Dict:
        """Extract public key information"""
        try:
            # This is a simplified version - in practice you'd use cryptography library
            # to properly parse the public key
            return {
                'algorithm': cert.get('signatureAlgorithm', 'unknown'),
                'size': 'unknown'  # Would need cryptography library for actual size
            }
        except Exception:
            return {'algorithm': 'unknown', 'size': 'unknown'}
    
    def _extract_extensions(self, cert: Dict) -> Dict:
        """Extract certificate extensions"""
        extensions = {}
        
        # Common extensions we might want to capture
        extension_keys = [
            'keyUsage',
            'extendedKeyUsage', 
            'subjectAltName',
            'basicConstraints',
            'authorityKeyIdentifier',
            'subjectKeyIdentifier',
            'crlDistributionPoints',
            'authorityInfoAccess'
        ]
        
        for key in extension_keys:
            if key in cert:
                extensions[key] = cert[key]
        
        return extensions
    
    def _extract_domains(self, cert: Dict) -> List[str]:
        """Extract domains from certificate"""
        domains = set()
        
        # Get Common Name from subject
        subject = cert.get('subject', [])
        for item in subject:
            for key, value in item:
                if key == 'commonName':
                    domains.add(value)
        
        # Get Subject Alternative Names
        san = cert.get('subjectAltName', [])
        for san_type, san_value in san:
            if san_type == 'DNS':
                domains.add(san_value)
        
        return list(domains)
    
    def _get_certificate_fingerprint(self, cert_der: bytes, algorithm: str) -> str:
        """Get certificate fingerprint"""
        try:
            if algorithm == 'sha1':
                return hashlib.sha1(cert_der).hexdigest().upper()
            elif algorithm == 'sha256':
                return hashlib.sha256(cert_der).hexdigest().upper()
            else:
                return ''
        except Exception:
            return ''
    
    async def grab_certificates_batch(self, host_port_pairs: List[Tuple[str, int]]) -> Dict[Tuple[str, int], Dict]:
        """
        Grab certificates for multiple host:port combinations in batch
        
        Args:
            host_port_pairs: List of (host_ip, port) tuples
            
        Returns:
            Dictionary mapping (host_ip, port) to certificate data
        """
        tasks = []
        for host_ip, port in host_port_pairs:
            task = self.grab_certificate(host_ip, port)
            tasks.append(((host_ip, port), task))
        
        results = {}
        for (host_ip, port), task in tasks:
            try:
                cert_data = await task
                if cert_data:
                    results[(host_ip, port)] = cert_data
            except Exception as e:
                logger.debug(f"Batch SSL cert grab failed for {host_ip}:{port}: {e}")
        
        return results
    
    def cleanup(self):
        """Clean up resources"""
        if self.executor:
            self.executor.shutdown(wait=True)


# Global SSL cert grabber instance
_ssl_cert_grabber = None

def get_ssl_cert_grabber() -> SSLCertGrabber:
    """Get the global SSL cert grabber instance"""
    global _ssl_cert_grabber
    if _ssl_cert_grabber is None:
        _ssl_cert_grabber = SSLCertGrabber()
    return _ssl_cert_grabber
