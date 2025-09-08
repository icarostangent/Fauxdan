import socket
import asyncio
import logging
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import ssl

logger = logging.getLogger(__name__)


class BannerGrabber:
    """Utility class for grabbing banners from open ports"""
    
    def __init__(self, timeout: int = 3, max_workers: int = 50):
        self.timeout = timeout
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def grab_banner(self, host: str, port: int, protocol: str = 'tcp') -> Optional[str]:
        """
        Grab banner from a specific host:port combination
        
        Args:
            host: IP address or hostname
            port: Port number
            protocol: Protocol (tcp/udp)
            
        Returns:
            Banner string or None if no banner could be grabbed
        """
        if protocol.lower() != 'tcp':
            # UDP banner grabbing is more complex and less reliable
            return None
            
        try:
            # Run banner grabbing in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            banner = await loop.run_in_executor(
                self.executor, 
                self._grab_banner_sync, 
                host, 
                port
            )
            return banner
        except Exception as e:
            logger.debug(f"Failed to grab banner from {host}:{port}: {e}")
            return None
    
    def _grab_banner_sync(self, host: str, port: int) -> Optional[str]:
        """Synchronous banner grabbing function"""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Connect to the port
            sock.connect((host, port))
            
            # Try to receive data
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
            
            # For HTTPS ports, try SSL handshake
            if port in [443, 8443, 9443] and not banner:
                try:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    
                    ssl_sock = context.wrap_socket(sock, server_hostname=host)
                    ssl_sock.settimeout(self.timeout)
                    
                    # Try to get SSL certificate info or HTTP response
                    ssl_sock.send(b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
                    banner = ssl_sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    ssl_sock.close()
                except Exception:
                    pass
            
            # For HTTP ports, try HTTP request
            elif port in [80, 8080, 8000, 8008, 8888] and not banner:
                try:
                    sock.send(b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
            
            # For SSH ports, try SSH handshake
            elif port == 22 and not banner:
                try:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
            
            # For FTP ports, try FTP banner
            elif port == 21 and not banner:
                try:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
            
            # For SMTP ports, try SMTP banner
            elif port in [25, 587, 465] and not banner:
                try:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
            
            # For other ports, just try to receive any data
            else:
                try:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
            
            sock.close()
            
            # Clean up the banner
            if banner:
                # Remove common prefixes and clean up
                banner = banner.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
                banner = ' '.join(banner.split())  # Remove extra whitespace
                
                # Limit banner length
                if len(banner) > 500:
                    banner = banner[:500] + "..."
                
                return banner
            
            return None
            
        except Exception as e:
            logger.debug(f"Banner grab failed for {host}:{port}: {e}")
            return None
        finally:
            try:
                sock.close()
            except:
                pass
    
    async def grab_banners_batch(self, port_data: List[Tuple[str, int, str]]) -> Dict[Tuple[str, int], str]:
        """
        Grab banners for multiple ports in batch
        
        Args:
            port_data: List of (host, port, protocol) tuples
            
        Returns:
            Dictionary mapping (host, port) to banner string
        """
        tasks = []
        for host, port, protocol in port_data:
            task = self.grab_banner(host, port, protocol)
            tasks.append((host, port, task))
        
        results = {}
        for host, port, task in tasks:
            try:
                banner = await task
                if banner:
                    results[(host, port)] = banner
            except Exception as e:
                logger.debug(f"Batch banner grab failed for {host}:{port}: {e}")
        
        return results
    
    def cleanup(self):
        """Clean up resources"""
        if self.executor:
            self.executor.shutdown(wait=True)


# Global banner grabber instance
_banner_grabber = None

def get_banner_grabber() -> BannerGrabber:
    """Get the global banner grabber instance"""
    global _banner_grabber
    if _banner_grabber is None:
        _banner_grabber = BannerGrabber()
    return _banner_grabber
