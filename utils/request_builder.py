"""
Utility module for building HTTP requests with custom headers, proxies, and configurations.
"""

import requests
from typing import Dict, Optional, Any, Union
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def build_headers(
    auth_token: Optional[str] = None,
    data_mode: str = "cipher",
    extra_headers: Optional[Dict[str, str]] = None,
    user_agent: Optional[str] = None
) -> Dict[str, str]:
    """Build HTTP headers with optional authentication and custom headers."""
    headers = {
        "Content-Type": "application/json",
        "x-data-mode": data_mode,
        "User-Agent": user_agent or "EVIL_JWT_FORCE/1.0"
    }
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    if extra_headers:
        headers.update(extra_headers)
    
    return headers

def create_session(
    proxies: Optional[Dict[str, str]] = None,
    timeout: int = 10,
    verify_ssl: bool = True
) -> requests.Session:
    """Create a configured requests Session object."""
    session = requests.Session()
    
    if proxies:
        session.proxies = proxies
    
    session.timeout = timeout
    session.verify = verify_ssl
    
    return session

class RequestBuilder:
    """
    A class to build and configure HTTP requests.
    """
    def __init__(
        self,
        base_url: str = '',
        proxies: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        verify_ssl: bool = True
    ):
        self.base_url = base_url.rstrip('/')
        self.session = create_session(proxies, timeout, verify_ssl)
        self.headers = {
            "User-Agent": "EVIL_JWT_FORCE/1.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json"
        }

    def set_headers(self, extra: Dict[str, str]) -> None:
        """
        Update headers with additional values.
        Args:
            extra (dict): Additional headers to include or override defaults.
        """
        self.headers.update(extra)
        self.session.headers.update(self.headers)

    def build_payload(self, username: str, password: str) -> Dict[str, Any]:
        """
        Build a payload dictionary for authentication requests.
        Args:
            username (str): Username for authentication.
            password (str): Password for authentication.
        Returns:
            dict: Payload dictionary with username and password.
        """
        return {"username": username, "password": password}

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Union[Dict[str, Any], Any]:
        """
        Send a GET request to the specified endpoint.
        Args:
            endpoint (str): The endpoint to send the request to.
            params (dict, optional): Query parameters for the request.
        Returns:
            Response object or error dictionary.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        except Exception as e:
            logger.error(f"GET request failed: {e}")
            return {"error": str(e)}

    def post(self, endpoint: str, data: Optional[Dict] = None) -> Union[Dict[str, Any], Any]:
        """
        Send a POST request to the specified endpoint.
        Args:
            endpoint (str): The endpoint to send the request to.
            data (dict, optional): Data payload for the request.
        Returns:
            Response object or error dictionary.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        except Exception as e:
            logger.error(f"POST request failed: {e}")
            return {"error": str(e)}

    def put(self, endpoint: str, data: Optional[Dict] = None) -> Union[Dict[str, Any], Any]:
        """
        Send a PUT request to the specified endpoint.
        Args:
            endpoint (str): The endpoint to send the request to.
            data (dict, optional): Data payload for the request.
        Returns:
            Response object or error dictionary.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.put(url, json=data)
            response.raise_for_status()
            return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        except Exception as e:
            logger.error(f"PUT request failed: {e}")
            return {"error": str(e)}

    def delete(self, endpoint: str) -> Union[Dict[str, Any], Any]:
        """
        Send a DELETE request to the specified endpoint.
        Args:
            endpoint (str): The endpoint to send the request to.
        Returns:
            Response object or error dictionary.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            return response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        except Exception as e:
            logger.error(f"DELETE request failed: {e}")
            return {"error": str(e)}

def build_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Build a dictionary of HTTP headers with default values and optional extras.
    
    Args:
        extra (dict, optional): Additional headers to include or override defaults.
    
    Returns:
        dict: Combined headers dictionary.
    """
    headers = {
        "User-Agent": "EVIL_JWT_FORCE/1.0",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json"
    }
    if extra:
        headers.update(extra)
    return headers

def build_payload(username: str, password: str) -> Dict[str, Any]:
    """
    Build a payload dictionary for authentication requests.
    
    Args:
        username (str): Username for authentication.
        password (str): Password for authentication.
    
    Returns:
        dict: Payload dictionary with username and password.
    """
    return {"username": username, "password": password}

def create_session(proxies: Optional[Dict[str, str]] = None, timeout: int = 10) -> requests.Session:
    """
    Create a configured requests Session object.
    
    Args:
        proxies (dict, optional): Proxy settings for the session.
        timeout (int): Timeout value for requests in seconds.
    
    Returns:
        requests.Session: Configured session object.
    """
    session = requests.Session()
    if proxies:
        session.proxies = proxies
    session.timeout = timeout
    return session 