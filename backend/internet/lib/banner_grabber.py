import socket
import asyncio
import logging
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import ssl
import subprocess
import xml.etree.ElementTree as ET

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
        """Synchronous banner grabbing that prefers nmap and falls back to sockets."""
        # Try with nmap first
        try:
            banner = self._grab_banner_via_nmap(host, port)
            if banner:
                return banner
        except Exception as nmap_exc:
            logger.debug(f"nmap banner grab failed for {host}:{port}: {nmap_exc}")

        # Fallback to socket-based approach
        return self._grab_banner_via_socket(host, port)

    def _grab_banner_via_nmap(self, host: str, port: int) -> Optional[str]:
        """Use nmap -sV (and banner script) to detect service banner and version."""
        cmd = [
            "nmap",
            "-Pn",
            "-n",
            "-sV",
            "--version-light",
            "--host-timeout",
            f"{self.timeout}s",
            "--max-retries",
            "1",
            "--script",
            "banner",
            "-p",
            str(port),
            "-oX",
            "-",
            host,
        ]
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=max(self.timeout + 5, 10),
            )
            stdout = completed.stdout or ""
            if not stdout.strip():
                return None

            # Parse XML output
            root = ET.fromstring(stdout)
            service_elem = root.find(f".//port[@portid='{port}']/service")
            banner_text: Optional[str] = None
            if service_elem is not None:
                name = service_elem.get("name") or ""
                product = service_elem.get("product") or ""
                version = service_elem.get("version") or ""
                extrainfo = service_elem.get("extrainfo") or ""
                banner_attr = service_elem.get("banner") or ""

                parts: List[str] = []
                if name:
                    parts.append(name)
                if product:
                    parts.append(product)
                if version:
                    parts.append(version)
                if extrainfo:
                    parts.append(f"({extrainfo})")

                if not parts and banner_attr:
                    parts.append(banner_attr)

                if parts:
                    banner_text = " ".join(parts)

            # Check for banner script output if service-based assembly failed
            if not banner_text:
                script_elem = root.find(f".//port[@portid='{port}']/script[@id='banner']")
                if script_elem is not None:
                    out = script_elem.get("output") or ""
                    if out:
                        banner_text = out

            if banner_text:
                return self._clean_banner_text(banner_text)

            return None
        except subprocess.TimeoutExpired:
            return None
        except ET.ParseError as parse_err:
            logger.debug(f"nmap XML parse error for {host}:{port}: {parse_err}")
            return None

    def _grab_banner_via_socket(self, host: str, port: int) -> Optional[str]:
        """Legacy socket-based banner grabbing as a fallback."""
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((host, port))

            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()

            if port in [443, 8443, 9443] and not banner:
                try:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    ssl_sock = context.wrap_socket(sock, server_hostname=host)
                    ssl_sock.settimeout(self.timeout)
                    ssl_sock.send(b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
                    banner = ssl_sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    ssl_sock.close()
                except Exception:
                    pass
            elif port in [80, 8080, 8000, 8008, 8888] and not banner:
                try:
                    sock.send(b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
            elif port == 22 and not banner:
                try:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
            elif port == 21 and not banner:
                try:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
            elif port in [25, 587, 465] and not banner:
                try:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass
            else:
                try:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                except Exception:
                    pass

            if banner:
                return self._clean_banner_text(banner)
            return None
        except Exception as e:
            logger.debug(f"Socket banner grab failed for {host}:{port}: {e}")
            return None
        finally:
            try:
                if sock:
                    sock.close()
            except Exception:
                pass

    def _clean_banner_text(self, banner: str) -> str:
        """Normalize and truncate banner text consistently."""
        banner = banner.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
        banner = ' '.join(banner.split())
        if len(banner) > 500:
            banner = banner[:500] + "..."
        return banner
    
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
