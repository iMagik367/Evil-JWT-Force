"""
Módulo avançado para rotação, validação e gerenciamento de proxies.
Suporte a proxies autenticados, blacklist dinâmica, integração com APIs públicas e logging detalhado.
"""

import requests
import random
import sys
import threading
import time
from typing import Dict, Optional, List, Union
from pathlib import Path
from utils.helpers import read_lines

class ProxyRotator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, proxy_file: Optional[str] = None, auto_reload: bool = False):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.proxy_file = proxy_file
                cls._instance.proxies = []
                cls._instance.current_index = 0
                cls._instance.blacklist = set()
                cls._instance.auto_reload = auto_reload
                cls._instance.last_reload = 0
                cls._instance.reload_interval = 300  # segundos
                cls._instance._initialize_proxies()
            return cls._instance

    def __init__(self, proxy_file: Optional[str] = None, auto_reload: bool = False) -> None:
        self.proxy_file: Optional[str] = proxy_file
        self.proxies: List[str] = []
        self.current_index: int = 0
        self.blacklist: set = set()
        self.auto_reload: bool = auto_reload
        self.last_reload: float = 0
        self.reload_interval: int = 300
        self._initialize_proxies()

    def _initialize_proxies(self) -> None:
        if self.proxy_file:
            self.load_proxies()
        else:
            self.proxies = []
        self.last_reload = time.time()

    def load_proxies(self) -> None:
        try:
            if not self.proxy_file or not Path(self.proxy_file).exists():
                print(f"[ProxyRotator] Arquivo de proxies não encontrado: {self.proxy_file}")
                self.proxies = []
                return
            self.proxies = [p for p in read_lines(self.proxy_file) if p and p not in self.blacklist]
            if not self.proxies:
                print("[ProxyRotator] Arquivo de proxies está vazio ou todos estão na blacklist.")
        except Exception as e:
            print(f"[ProxyRotator] Erro ao carregar proxies: {str(e)}")
            self.proxies = []

    def fetch_public_proxies(self, api_url: str = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=3000&country=all") -> None:
        try:
            resp = requests.get(api_url, timeout=10)
            if resp.status_code == 200:
                proxies = [line.strip() for line in resp.text.splitlines() if line.strip()]
                self.proxies.extend([p for p in proxies if p not in self.proxies and p not in self.blacklist])
                print(f"[ProxyRotator] {len(proxies)} proxies públicos adicionados.")
            else:
                print(f"[ProxyRotator] Falha ao buscar proxies públicos: {resp.status_code}")
        except Exception as e:
            print(f"[ProxyRotator] Erro ao buscar proxies públicos: {e}")

    def _format_proxy(self, proxy: str) -> Dict[str, str]:
        if "@" in proxy:
            # Proxy autenticado: usuario:senha@host:porta
            return {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
        return {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }

    def get_next_proxy(self, validate: bool = True, max_attempts: int = 10) -> Optional[Dict[str, str]]:
        self._maybe_reload()
        attempts = 0
        while self.proxies and attempts < max_attempts:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            if proxy in self.blacklist:
                attempts += 1
                continue
            if not validate or self._validate_proxy(proxy):
                return self._format_proxy(proxy)
            else:
                self.add_to_blacklist(proxy)
                attempts += 1
        return None

    def get_random_proxy(self, validate: bool = True, max_attempts: int = 10) -> Optional[Dict[str, str]]:
        self._maybe_reload()
        attempts = 0
        while self.proxies and attempts < max_attempts:
            proxy = random.choice(self.proxies)
            if proxy in self.blacklist:
                attempts += 1
                continue
            if not validate or self._validate_proxy(proxy):
                return self._format_proxy(proxy)
            else:
                self.add_to_blacklist(proxy)
                attempts += 1
        return None

    def _validate_proxy(self, proxy: str, timeout: int = 5) -> bool:
        proxies = self._format_proxy(proxy)
        test_url = "http://httpbin.org/ip"
        try:
            resp = requests.get(test_url, proxies=proxies, timeout=timeout)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        return False

    def add_to_blacklist(self, proxy: str) -> None:
        self.blacklist.add(proxy)
        print(f"[ProxyRotator] Proxy adicionado à blacklist: {proxy}")

    def remove_from_blacklist(self, proxy: str) -> None:
        self.blacklist.discard(proxy)

    def _maybe_reload(self):
        if self.auto_reload and (time.time() - self.last_reload > self.reload_interval):
            self.load_proxies()
            self.last_reload = time.time()

    def get_proxy_list(self, only_valid: bool = False, sample: int = 0) -> List[str]:
        self._maybe_reload()
        proxies = [p for p in self.proxies if p not in self.blacklist]
        if only_valid:
            proxies = [p for p in proxies if self._validate_proxy(p)]
        if sample > 0:
            proxies = random.sample(proxies, min(sample, len(proxies)))
        return proxies

    def reset_blacklist(self):
        self.blacklist.clear()
        print("[ProxyRotator] Blacklist limpa.")

    def reload(self):
        self.load_proxies()
        print("[ProxyRotator] Proxies recarregados.")

# Exemplo de uso:
# rotator = ProxyRotator("proxies.txt", auto_reload=True)
# proxy = rotator.get_next_proxy()