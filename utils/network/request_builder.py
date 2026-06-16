"""
RequestBuilder - Advanced HTTP request builder module (Kali Linux Only)
"""

import sys
import json
import requests
import random
from pathlib import Path
from typing import Dict, Optional, Union, Any, List

from utils.helpers import generate_nonce, get_current_timestamp

# Integration with ProxyRotator if available
try:
    from utils.network.proxy_rotator import ProxyRotator
except ImportError:
    ProxyRotator = None

# Linux-only User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

class RequestBuilder:
    """Advanced HTTP request builder with proxy, Linux User-Agent rotation, authentication, and cookie management."""

    def __init__(self, base_url: str, use_proxy: bool = False, proxy_file: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.headers: Dict[str, str] = {}
        self.params: Dict[str, Any] = {}
        self.timeout = 30
        self.cookies: Dict[str, str] = {}
        self.use_proxy = use_proxy
        self.proxy_rotator = ProxyRotator(proxy_file) if use_proxy and ProxyRotator else None
        self.last_proxy = None

    def set_headers(self, headers: Dict[str, str]) -> 'RequestBuilder':
        self.headers.update(headers)
        return self

    def set_params(self, params: Dict[str, Any]) -> 'RequestBuilder':
        self.params.update(params)
        return self

    def set_timeout(self, timeout: int) -> 'RequestBuilder':
        self.timeout = timeout
        return self

    def set_cookies(self, cookies: Dict[str, str]) -> 'RequestBuilder':
        self.cookies.update(cookies)
        return self

    def rotate_user_agent(self) -> 'RequestBuilder':
        ua = random.choice(USER_AGENTS)
        self.headers["User-Agent"] = ua
        return self

    def add_auth(self, auth_type: str, token: str, username: Optional[str] = None, password: Optional[str] = None) -> 'RequestBuilder':
        auth_type = auth_type.lower()
        if auth_type in ['bearer', 'jwt']:
            self.headers['Authorization'] = f'Bearer {token}'
        elif auth_type == 'basic' and username and password:
            import base64
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            self.headers['Authorization'] = f'Basic {credentials}'
        elif auth_type == 'apikey':
            self.headers['X-API-KEY'] = token
        elif auth_type == 'custom':
            self.headers['Authorization'] = token
        return self

    def set_proxy(self, proxy: Optional[Dict[str, str]] = None) -> 'RequestBuilder':
        if proxy:
            self.session.proxies = proxy
            self.last_proxy = proxy
        elif self.proxy_rotator:
            proxy = self.proxy_rotator.get_next_proxy(validate=True)
            if proxy:
                self.session.proxies = proxy
                self.last_proxy = proxy
        return self

    def build(self) -> requests.Session:
        self.session.headers.update(self.headers)
        if self.cookies:
            self.session.cookies.update(self.cookies)
        return self.session

    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('params', self.params)
        if self.cookies:
            kwargs.setdefault('cookies', self.cookies)
        if self.use_proxy and self.proxy_rotator:
            self.set_proxy()
        print(f"[RequestBuilder] {method.upper()} {url} | Headers: {self.headers} | Params: {self.params} | Proxy: {self.last_proxy}")
        return self.session.request(method, url, **kwargs)

# --- Utility Functions ---
def build_headers(
    auth_token: Optional[str] = None,
    data_mode: str = "cipher",
    extra_headers: Optional[Dict[str, str]] = None,
    user_agent: Optional[str] = None
) -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "x-data-mode": data_mode,
        "X-Request-Id": generate_nonce(),
        "User-Agent": user_agent or random.choice(USER_AGENTS)
    }
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    if extra_headers:
        headers.update(extra_headers)
    return headers

def build_payload(
    username: Optional[str] = None,
    password: Optional[str] = None,
    timestamp: Optional[int] = None,
    nonce: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None
) -> str:
    data = {
        "timestamp": timestamp or get_current_timestamp(),
        "nonce": nonce or generate_nonce()
    }
    if username is not None:
        data["username"] = username
    if password is not None:
        data["password"] = password
    if extra:
        data.update(extra)
    return json.dumps(data)

def build_form_payload(fields: Dict[str, Any]) -> Dict[str, Any]:
    """Builds payload for multipart/form-data or application/x-www-form-urlencoded"""
    return fields

def build_files_payload(file_paths: List[str]) -> Dict[str, Any]:
    """Builds payload for file uploads"""
    files = {}
    for path in file_paths:
        name = Path(path).name
        files[name] = open(path, "rb")
    return files

def close_files(files: Dict[str, Any]):
    """Closes open files in payloads"""
    for f in files.values():
        try:
            f.close()
        except Exception:
            pass