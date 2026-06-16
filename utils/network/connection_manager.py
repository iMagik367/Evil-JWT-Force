"""
Gerenciador de conexão com tratamento robusto de erros de rede.
"""

import time
import logging
import socket
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any, Union
from urllib3.exceptions import MaxRetryError, ConnectionError, TimeoutError
from pathlib import Path

# Configuração de logging
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages HTTP connections with retry logic and error handling."""
    
    def __init__(
        self,
        base_url: str = '',
        timeout: int = 10,
        max_retries: int = 3,
        verify_ssl: bool = True
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.timeout = timeout
    
    def _handle_request_error(self, error: Exception, url: str) -> Dict[str, Any]:
        """Handle request errors and return appropriate error response."""
        error_msg = str(error)
        logger.error(f"Request failed for {url}: {error_msg}")
        
        if isinstance(error, requests.exceptions.ConnectionError):
            return {"error": "Connection error", "details": error_msg}
        elif isinstance(error, requests.exceptions.Timeout):
            return {"error": "Request timeout", "details": error_msg}
        elif isinstance(error, requests.exceptions.HTTPError):
            return {"error": f"HTTP error {error.response.status_code}", "details": error_msg}
        else:
            return {"error": "Request failed", "details": error_msg}
    
    def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Union[requests.Response, Dict[str, Any]]:
        """Make an HTTP request with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        retries = 0
        
        while retries < self.max_retries:
            try:
                kwargs.setdefault('timeout', self.timeout)
                kwargs.setdefault('verify', self.verify_ssl)
                
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except Exception as e:
                retries += 1
                if retries == self.max_retries:
                    return self._handle_request_error(e, url)
                time.sleep(1)  # Wait before retrying
    
    def get(self, endpoint: str, **kwargs) -> Union[requests.Response, Dict[str, Any]]:
        """Make a GET request."""
        return self.request('GET', endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> Union[requests.Response, Dict[str, Any]]:
        """Make a POST request."""
        return self.request('POST', endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> Union[requests.Response, Dict[str, Any]]:
        """Make a PUT request."""
        return self.request('PUT', endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Union[requests.Response, Dict[str, Any]]:
        """Make a DELETE request."""
        return self.request('DELETE', endpoint, **kwargs)

    def _resolve_dns(self, hostname: str) -> Optional[str]:
        """
        Tenta resolver o hostname usando múltiplos servidores DNS.
        
        Args:
            hostname: Nome do host para resolver
            
        Returns:
            IP resolvido ou None se falhar
        """
        for dns_server in ['8.8.8.8', '1.1.1.1', '208.67.222.222']:
            try:
                resolver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                resolver.settimeout(5)
                resolver.sendto(b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00' + 
                              b''.join(bytes([len(x)]) + x.encode() for x in hostname.split('.')) + 
                              b'\x00\x00\x01\x00\x01', (dns_server, 53))
                data, _ = resolver.recvfrom(1024)
                ip = '.'.join(str(x) for x in data[-4:])
                resolver.close()
                return ip
            except Exception as e:
                logger.warning(f"Falha ao resolver DNS usando {dns_server}: {e}")
                continue
        return None

    def _handle_request_error(self, error: Exception, url: str) -> Dict[str, Any]:
        """
        Trata erros de requisição e retorna informações detalhadas.
        
        Args:
            error: Exceção capturada
            url: URL que causou o erro
            
        Returns:
            Dicionário com informações do erro
        """
        error_info = {
            "error": str(error),
            "url": url,
            "timestamp": time.time()
        }
        
        if isinstance(error, MaxRetryError):
            error_info["type"] = "max_retries_exceeded"
            error_info["retries"] = getattr(error, "retries", 0)
        elif isinstance(error, ConnectionError):
            error_info["type"] = "connection_error"
            # Tenta resolver DNS
            hostname = url.split("://")[-1].split("/")[0]
            ip = self._resolve_dns(hostname)
            if ip:
                error_info["resolved_ip"] = ip
        elif isinstance(error, TimeoutError):
            error_info["type"] = "timeout"
        else:
            error_info["type"] = "unknown"
            
        logger.error(f"Erro na requisição: {error_info}")
        return error_info 