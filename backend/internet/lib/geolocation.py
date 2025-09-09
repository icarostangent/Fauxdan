import requests
import logging
import time
import asyncio
import concurrent.futures
from typing import Dict, Optional, List
from django.conf import settings
from django.core.cache import cache
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class GeolocationService:
    """IP Geolocation service with multiple providers, caching, and async support"""
    
    def __init__(self, max_workers: int = 10):
        self.providers = [
            self._get_ipapi_data,
            self._get_ipinfo_data,
            self._get_freeipapi_data,
            self._get_ipgeolocation_data
        ]
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    
    def get_location(self, ip_address: str) -> Optional[Dict]:
        """
        Get geolocation data for an IP address with caching and fallback providers
        
        Args:
            ip_address: IP address to geolocate
            
        Returns:
            Dictionary with location data or None if all providers fail
        """
        # Check cache first
        cache_key = f"geolocation:{ip_address}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Try each provider until one succeeds
        for provider in self.providers:
            try:
                data = provider(ip_address)
                if data:
                    # Cache successful result for 24 hours
                    cache.set(cache_key, data, 86400)
                    return data
            except Exception as e:
                logger.warning(f"Geolocation provider failed for {ip_address}: {e}")
                continue
        
        # Cache negative result for 1 hour to avoid repeated failures
        cache.set(cache_key, None, 3600)
        return None
    
    async def get_location_async(self, ip_address: str) -> Optional[Dict]:
        """
        Async version of get_location using thread pool
        
        Args:
            ip_address: IP address to geolocate
            
        Returns:
            Dictionary with location data or None if all providers fail
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.get_location, ip_address)
    
    async def get_locations_batch_async(self, ip_addresses: List[str], 
                                      batch_size: int = 20) -> Dict[str, Optional[Dict]]:
        """
        Async batch geolocation with concurrent processing
        
        Args:
            ip_addresses: List of IP addresses to geolocate
            batch_size: Number of concurrent requests
            
        Returns:
            Dictionary mapping IP addresses to geolocation data
        """
        results = {}
        
        # Process in batches to avoid overwhelming APIs
        for i in range(0, len(ip_addresses), batch_size):
            batch = ip_addresses[i:i + batch_size]
            
            # Create tasks for concurrent processing
            tasks = [
                self.get_location_async(ip) 
                for ip in batch
            ]
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for ip, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error geolocating {ip}: {result}")
                    results[ip] = None
                else:
                    results[ip] = result
            
            # Rate limiting between batches
            if i + batch_size < len(ip_addresses):
                await asyncio.sleep(1)
        
        return results
    
    def _get_ipapi_data(self, ip_address: str) -> Optional[Dict]:
        """Get data from ip-api.com (free, no API key required)"""
        url = f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,region,regionName,city,lat,lon,timezone,isp,org,as,query"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'success':
            return {
                'ip': data.get('query'),
                'country': data.get('country'),
                'country_code': data.get('countryCode'),
                'region': data.get('regionName'),
                'city': data.get('city'),
                'latitude': data.get('lat'),
                'longitude': data.get('lon'),
                'timezone': data.get('timezone'),
                'isp': data.get('isp'),
                'organization': data.get('org'),
                'asn': data.get('as'),
                'provider': 'ip-api.com'
            }
        return None
    
    def _get_ipinfo_data(self, ip_address: str) -> Optional[Dict]:
        """Get data from ipinfo.io (free tier available)"""
        # You can add your API token here for higher limits
        token = getattr(settings, 'IPINFO_TOKEN', None)
        url = f"https://ipinfo.io/{ip_address}/json"
        
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'error' not in data:
            loc = data.get('loc', '').split(',')
            return {
                'ip': data.get('ip'),
                'country': data.get('country'),
                'region': data.get('region'),
                'city': data.get('city'),
                'latitude': float(loc[0]) if len(loc) > 0 and loc[0] else None,
                'longitude': float(loc[1]) if len(loc) > 1 and loc[1] else None,
                'timezone': data.get('timezone'),
                'isp': data.get('org'),
                'postal': data.get('postal'),
                'provider': 'ipinfo.io'
            }
        return None
    
    def _get_freeipapi_data(self, ip_address: str) -> Optional[Dict]:
        """Get data from freeipapi.com (free, no API key required)"""
        url = f"https://freeipapi.com/api/json/{ip_address}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            'ip': ip_address,
            'country': data.get('countryName'),
            'country_code': data.get('countryCode'),
            'region': data.get('regionName'),
            'city': data.get('cityName'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'timezone': data.get('timeZone'),
            'provider': 'freeipapi.com'
        }
    
    def _get_ipgeolocation_data(self, ip_address: str) -> Optional[Dict]:
        """Get data from ipgeolocation.io (free tier available)"""
        # You can add your API key here for higher limits
        api_key = getattr(settings, 'IPGEOLOCATION_API_KEY', None)
        url = f"https://api.ipgeolocation.io/ipgeo?ip={ip_address}"
        
        if api_key:
            url += f"&apiKey={api_key}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'message' not in data:  # No error message means success
            return {
                'ip': data.get('ip'),
                'country': data.get('country_name'),
                'country_code': data.get('country_code2'),
                'region': data.get('state_prov'),
                'city': data.get('city'),
                'latitude': float(data.get('latitude')) if data.get('latitude') else None,
                'longitude': float(data.get('longitude')) if data.get('longitude') else None,
                'timezone': data.get('time_zone', {}).get('name'),
                'isp': data.get('isp'),
                'provider': 'ipgeolocation.io'
            }
        return None


# Global instance
geolocation_service = GeolocationService()


def get_ip_geolocation(ip_address: str) -> Optional[Dict]:
    """Convenience function to get geolocation data"""
    return geolocation_service.get_location(ip_address)


async def get_ip_geolocation_async(ip_address: str) -> Optional[Dict]:
    """Async convenience function to get geolocation data"""
    return await geolocation_service.get_location_async(ip_address)


async def get_ip_geolocations_batch_async(ip_addresses: List[str], 
                                        batch_size: int = 20) -> Dict[str, Optional[Dict]]:
    """Async convenience function for batch geolocation"""
    return await geolocation_service.get_locations_batch_async(ip_addresses, batch_size)


def cleanup_geolocation_service():
    """Cleanup function to properly shutdown thread pool"""
    if geolocation_service.executor:
        geolocation_service.executor.shutdown(wait=True)


def bulk_geolocate_hosts(host_ips: list, delay: float = 0.1) -> Dict[str, Dict]:
    """
    Geolocate multiple hosts with rate limiting
    
    Args:
        host_ips: List of IP addresses to geolocate
        delay: Delay between requests to respect rate limits
        
    Returns:
        Dictionary mapping IP addresses to geolocation data
    """
    results = {}
    
    for ip in host_ips:
        try:
            location_data = get_ip_geolocation(ip)
            if location_data:
                results[ip] = location_data
            
            # Rate limiting
            if delay > 0:
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"Failed to geolocate {ip}: {e}")
            continue
    
    return results
