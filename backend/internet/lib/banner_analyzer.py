"""
Banner analysis service for intelligent service detection and job queuing
"""
import re
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """Enumeration of detected service types"""
    HTTP = "http"
    HTTPS = "https"
    SSH = "ssh"
    FTP = "ftp"
    SMTP = "smtp"
    DNS = "dns"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    MONGODB = "mongodb"
    MSSQL = "mssql"
    TELNET = "telnet"
    IMAP = "imap"
    POP3 = "pop3"
    RDP = "rdp"
    VNC = "vnc"
    UNKNOWN = "unknown"


@dataclass
class ServiceDetection:
    """Result of service detection from banner"""
    service_type: ServiceType
    confidence: float  # 0.0 to 1.0
    version: Optional[str] = None
    additional_info: Dict[str, str] = None
    
    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}


class BannerAnalyzer:
    """Analyzes banners to detect services and determine appropriate follow-up actions"""
    
    def __init__(self):
        self.service_patterns = self._build_service_patterns()
        self.ssl_indicators = self._build_ssl_indicators()
        self.web_indicators = self._build_web_indicators()
    
    def _build_service_patterns(self) -> Dict[ServiceType, List[Dict]]:
        """Build regex patterns for service detection"""
        return {
            ServiceType.HTTP: [
                {'pattern': r'(?i)(apache|httpd)', 'confidence': 0.9},
                {'pattern': r'(?i)nginx', 'confidence': 0.9},
                {'pattern': r'(?i)iis', 'confidence': 0.9},
                {'pattern': r'(?i)lighttpd', 'confidence': 0.8},
                {'pattern': r'(?i)caddy', 'confidence': 0.8},
                {'pattern': r'(?i)http/1\.[01]', 'confidence': 0.7},
                {'pattern': r'(?i)server:\s*([^\r\n]+)', 'confidence': 0.6},
            ],
            ServiceType.HTTPS: [
                {'pattern': r'(?i)https', 'confidence': 0.8},
                {'pattern': r'(?i)ssl', 'confidence': 0.7},
                {'pattern': r'(?i)tls', 'confidence': 0.7},
                {'pattern': r'(?i)secure', 'confidence': 0.6},
            ],
            ServiceType.SSH: [
                {'pattern': r'(?i)ssh-2\.0', 'confidence': 0.95},
                {'pattern': r'(?i)openssh', 'confidence': 0.9},
                {'pattern': r'(?i)dropbear', 'confidence': 0.8},
                {'pattern': r'(?i)libssh', 'confidence': 0.7},
            ],
            ServiceType.FTP: [
                {'pattern': r'(?i)vsftpd', 'confidence': 0.9},
                {'pattern': r'(?i)proftpd', 'confidence': 0.8},
                {'pattern': r'(?i)pure-ftpd', 'confidence': 0.8},
                {'pattern': r'(?i)220.*ftp', 'confidence': 0.7},
            ],
            ServiceType.SMTP: [
                {'pattern': r'(?i)postfix', 'confidence': 0.9},
                {'pattern': r'(?i)sendmail', 'confidence': 0.8},
                {'pattern': r'(?i)exim', 'confidence': 0.8},
                {'pattern': r'(?i)220.*smtp', 'confidence': 0.7},
                {'pattern': r'(?i)esmtp', 'confidence': 0.7},
            ],
            ServiceType.DNS: [
                {'pattern': r'(?i)bind', 'confidence': 0.9},
                {'pattern': r'(?i)dnsmasq', 'confidence': 0.8},
                {'pattern': r'(?i)powerdns', 'confidence': 0.8},
                {'pattern': r'(?i)53.*dns', 'confidence': 0.6},
            ],
            ServiceType.MYSQL: [
                {'pattern': r'(?i)mysql', 'confidence': 0.9},
                {'pattern': r'(?i)mariadb', 'confidence': 0.9},
                {'pattern': r'(?i)percona', 'confidence': 0.8},
            ],
            ServiceType.POSTGRESQL: [
                {'pattern': r'(?i)postgresql', 'confidence': 0.9},
                {'pattern': r'(?i)postgres', 'confidence': 0.8},
            ],
            ServiceType.REDIS: [
                {'pattern': r'(?i)redis', 'confidence': 0.9},
            ],
            ServiceType.MONGODB: [
                {'pattern': r'(?i)mongodb', 'confidence': 0.9},
                {'pattern': r'(?i)mongo', 'confidence': 0.8},
            ],
            ServiceType.MSSQL: [
                {'pattern': r'(?i)mssql', 'confidence': 0.9},
                {'pattern': r'(?i)sql server', 'confidence': 0.8},
            ],
            ServiceType.TELNET: [
                {'pattern': r'(?i)telnet', 'confidence': 0.8},
            ],
            ServiceType.IMAP: [
                {'pattern': r'(?i)imap', 'confidence': 0.8},
                {'pattern': r'(?i)dovecot', 'confidence': 0.9},
            ],
            ServiceType.POP3: [
                {'pattern': r'(?i)pop3', 'confidence': 0.8},
            ],
            ServiceType.RDP: [
                {'pattern': r'(?i)rdp', 'confidence': 0.8},
                {'pattern': r'(?i)terminal services', 'confidence': 0.7},
            ],
            ServiceType.VNC: [
                {'pattern': r'(?i)vnc', 'confidence': 0.8},
                {'pattern': r'(?i)tightvnc', 'confidence': 0.9},
                {'pattern': r'(?i)tigervnc', 'confidence': 0.9},
            ],
        }
    
    def _build_ssl_indicators(self) -> List[str]:
        """Build list of SSL/TLS indicators"""
        return [
            'ssl', 'tls', 'https', 'starttls', 'ssl/tls', 'tls/ssl',
            'secure', 'encrypted', 'certificate', 'x509'
        ]
    
    def _build_web_indicators(self) -> List[str]:
        """Build list of web service indicators"""
        return [
            'http', 'https', 'www', 'web', 'server', 'apache', 'nginx',
            'iis', 'lighttpd', 'caddy', 'tomcat', 'jetty'
        ]
    
    def analyze_banner(self, banner: str, port_number: int) -> List[ServiceDetection]:
        """
        Analyze a banner to detect services
        
        Args:
            banner: The banner string to analyze
            port_number: The port number where the banner was found
            
        Returns:
            List of ServiceDetection objects
        """
        if not banner or not banner.strip():
            return [ServiceDetection(ServiceType.UNKNOWN, 0.0)]
        
        banner_lower = banner.lower()
        detections = []
        
        # Check each service type
        for service_type, patterns in self.service_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                base_confidence = pattern_info['confidence']
                
                match = re.search(pattern, banner_lower)
                if match:
                    # Calculate confidence based on pattern match and context
                    confidence = self._calculate_confidence(
                        base_confidence, banner_lower, port_number, service_type
                    )
                    
                    # Extract version if possible
                    version = self._extract_version(banner_lower, service_type)
                    
                    # Extract additional info
                    additional_info = self._extract_additional_info(banner_lower, service_type)
                    
                    detections.append(ServiceDetection(
                        service_type=service_type,
                        confidence=confidence,
                        version=version,
                        additional_info=additional_info
                    ))
        
        # If no specific service detected, check for generic indicators
        if not detections:
            if any(indicator in banner_lower for indicator in self.ssl_indicators):
                detections.append(ServiceDetection(ServiceType.HTTPS, 0.5))
            elif any(indicator in banner_lower for indicator in self.web_indicators):
                detections.append(ServiceDetection(ServiceType.HTTP, 0.5))
            else:
                detections.append(ServiceDetection(ServiceType.UNKNOWN, 0.0))
        
        # Special handling for HTTPS: if we detect HTTP on port 443, it's likely HTTPS
        if port_number == 443 and any(d.service_type == ServiceType.HTTP for d in detections):
            # Add HTTPS detection with high confidence
            detections.append(ServiceDetection(ServiceType.HTTPS, 0.9))
        
        # Sort by confidence (highest first)
        detections.sort(key=lambda x: x.confidence, reverse=True)
        
        return detections
    
    def _calculate_confidence(self, base_confidence: float, banner: str, 
                            port_number: int, service_type: ServiceType) -> float:
        """Calculate confidence score based on context"""
        confidence = base_confidence
        
        # Port-based adjustments (but not assumptions)
        port_adjustments = {
            ServiceType.HTTP: {80: 0.1, 8080: 0.1, 8000: 0.1},
            ServiceType.HTTPS: {443: 0.1, 8443: 0.1, 9443: 0.1},
            ServiceType.SSH: {22: 0.1},
            ServiceType.FTP: {21: 0.1},
            ServiceType.SMTP: {25: 0.1, 587: 0.1, 465: 0.1},
            ServiceType.DNS: {53: 0.1},
            ServiceType.MYSQL: {3306: 0.1},
            ServiceType.POSTGRESQL: {5432: 0.1},
            ServiceType.REDIS: {6379: 0.1},
            ServiceType.MONGODB: {27017: 0.1},
            ServiceType.MSSQL: {1433: 0.1},
            ServiceType.TELNET: {23: 0.1},
            ServiceType.IMAP: {143: 0.1, 993: 0.1},
            ServiceType.POP3: {110: 0.1, 995: 0.1},
            ServiceType.RDP: {3389: 0.1},
            ServiceType.VNC: {5900: 0.1, 5901: 0.1},
        }
        
        if service_type in port_adjustments:
            port_adj = port_adjustments[service_type].get(port_number, 0)
            confidence += port_adj
        
        # Multiple indicators boost confidence
        if service_type in [ServiceType.HTTP, ServiceType.HTTPS]:
            web_indicators = sum(1 for indicator in self.web_indicators if indicator in banner)
            if web_indicators > 1:
                confidence += 0.1
        
        # SSL indicators boost HTTPS confidence
        if service_type == ServiceType.HTTPS:
            ssl_indicators = sum(1 for indicator in self.ssl_indicators if indicator in banner)
            if ssl_indicators > 1:
                confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _extract_version(self, banner: str, service_type: ServiceType) -> Optional[str]:
        """Extract version information from banner"""
        version_patterns = {
            ServiceType.HTTP: [
                r'(?i)apache/([0-9.]+)',
                r'(?i)nginx/([0-9.]+)',
                r'(?i)iis/([0-9.]+)',
                r'(?i)server:\s*([^\r\n]+)',
            ],
            ServiceType.SSH: [
                r'(?i)openssh_([0-9.]+)',
                r'(?i)ssh-2\.0-([^\s]+)',
            ],
            ServiceType.FTP: [
                r'(?i)vsftpd\s+([0-9.]+)',
                r'(?i)proftpd\s+([0-9.]+)',
            ],
            ServiceType.SMTP: [
                r'(?i)postfix/([0-9.]+)',
                r'(?i)sendmail\s+([0-9.]+)',
            ],
            ServiceType.MYSQL: [
                r'(?i)mysql\s+([0-9.]+)',
                r'(?i)mariadb\s+([0-9.]+)',
            ],
        }
        
        if service_type in version_patterns:
            for pattern in version_patterns[service_type]:
                match = re.search(pattern, banner)
                if match:
                    return match.group(1)
        
        return None
    
    def _extract_additional_info(self, banner: str, service_type: ServiceType) -> Dict[str, str]:
        """Extract additional information from banner"""
        info = {}
        
        # Extract server headers for web services
        if service_type in [ServiceType.HTTP, ServiceType.HTTPS]:
            server_match = re.search(r'(?i)server:\s*([^\r\n]+)', banner)
            if server_match:
                info['server'] = server_match.group(1).strip()
        
        # Extract SSH version info
        if service_type == ServiceType.SSH:
            ssh_match = re.search(r'(?i)ssh-([0-9.]+)-([^\s]+)', banner)
            if ssh_match:
                info['ssh_version'] = ssh_match.group(1)
                info['software'] = ssh_match.group(2)
        
        return info
    
    def should_queue_ssl_cert(self, detections: List[ServiceDetection]) -> bool:
        """Determine if SSL certificate should be queued based on detections"""
        for detection in detections:
            if detection.service_type == ServiceType.HTTPS:
                return True
            # Also check for SSL indicators in other services
            if detection.service_type in [ServiceType.SMTP, ServiceType.IMAP, ServiceType.POP3]:
                if any(indicator in detection.additional_info.get('server', '').lower() 
                      for indicator in self.ssl_indicators):
                    return True
        return False
    
    def should_queue_domain_enum(self, detections: List[ServiceDetection]) -> bool:
        """Determine if domain enumeration should be queued based on detections"""
        for detection in detections:
            if detection.service_type in [ServiceType.HTTP, ServiceType.HTTPS]:
                return True
        return False
    
    def get_priority_for_ancillary_job(self, detection: ServiceDetection, job_type: str) -> int:
        """Get priority for ancillary job based on service detection"""
        base_priorities = {
            'banner_grab': 0,
            'ssl_cert': 1,
            'domain_enum': 2,
        }
        
        priority = base_priorities.get(job_type, 0)
        
        # Boost priority for high-confidence detections
        if detection.confidence > 0.8:
            priority += 2
        elif detection.confidence > 0.6:
            priority += 1
        
        # Boost priority for critical services
        critical_services = [ServiceType.HTTPS, ServiceType.HTTP, ServiceType.SSH]
        if detection.service_type in critical_services:
            priority += 1
        
        return priority
