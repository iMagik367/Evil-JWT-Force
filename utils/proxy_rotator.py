"""
Proxy Rotation Module for EVIL_JWT_FORCE
"""

import random
from typing import Dict, List, Optional

class ProxyRotator:
    """
    A class to manage and rotate proxies for HTTP requests.
    """
    def __init__(self, proxy_list: Optional[List[str]] = None):
        self.proxy_list = proxy_list or []
        self.current_proxy = None
        self.failed_proxies = set()

    def get_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get a proxy from the list, rotating to the next available one.
        
        Returns:
            dict: Proxy configuration dictionary or None if no proxies are available.
        """
        if not self.proxy_list:
            return None
        
        available_proxies = [p for p in self.proxy_list if p not in self.failed_proxies]
        if not available_proxies:
            self.failed_proxies.clear()  # Reset failed proxies if all have failed
            available_proxies = self.proxy_list
        
        if available_proxies:
            self.current_proxy = random.choice(available_proxies)
            return {
                "http": self.current_proxy,
                "https": self.current_proxy
            }
        return None

    def mark_proxy_failed(self, proxy: str) -> None:
        """
        Mark a proxy as failed.
        
        Args:
            proxy (str): The proxy URL that failed.
        """
        self.failed_proxies.add(proxy)

    def load_proxies_from_file(self, filepath: str) -> None:
        """
        Load proxies from a file.
        
        Args:
            filepath (str): Path to the file containing proxy URLs, one per line.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.proxy_list = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error loading proxies from {filepath}: {e}") 