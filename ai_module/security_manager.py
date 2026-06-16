import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
from dataclasses import dataclass
import json
import os

@dataclass
class RateLimitConfig:
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    cooldown_period: int = 60  # segundos

class SecurityManager:
    def __init__(self, config_path: str = "config/security_config.json"):
        self.config_path = config_path
        self.rate_limits = RateLimitConfig()
        self.request_history: Dict[str, list] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.setup_logging()
        self.load_config()

    def setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            filename='logs/security.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('SecurityManager')

    def load_config(self):
        """Carrega configurações de segurança do arquivo JSON"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.rate_limits = RateLimitConfig(**config.get('rate_limits', {}))
        except Exception as e:
            self.logger.error(f"Erro ao carregar configurações: {str(e)}")
            # Usa configurações padrão em caso de erro

    def check_rate_limit(self, client_id: str) -> bool:
        """
        Verifica se o cliente excedeu os limites de requisição
        Retorna True se estiver dentro dos limites, False caso contrário
        """
        current_time = datetime.now()
        
        # Limpa histórico antigo
        self._cleanup_old_requests(current_time)
        
        # Verifica se o IP está bloqueado
        if self._is_ip_blocked(client_id):
            return False

        # Inicializa histórico do cliente se não existir
        if client_id not in self.request_history:
            self.request_history[client_id] = []

        # Adiciona nova requisição
        self.request_history[client_id].append(current_time)

        # Verifica limites
        if not self._check_minute_limit(client_id, current_time):
            self._block_ip(client_id)
            return False

        if not self._check_hour_limit(client_id, current_time):
            self._block_ip(client_id)
            return False

        if not self._check_day_limit(client_id, current_time):
            self._block_ip(client_id)
            return False

        return True

    def _cleanup_old_requests(self, current_time: datetime):
        """Remove requisições antigas do histórico"""
        for client_id in list(self.request_history.keys()):
            self.request_history[client_id] = [
                req_time for req_time in self.request_history[client_id]
                if current_time - req_time < timedelta(days=1)
            ]
            if not self.request_history[client_id]:
                del self.request_history[client_id]

    def _is_ip_blocked(self, client_id: str) -> bool:
        """Verifica se um IP está bloqueado"""
        if client_id in self.blocked_ips:
            if datetime.now() - self.blocked_ips[client_id] > timedelta(seconds=self.rate_limits.cooldown_period):
                del self.blocked_ips[client_id]
                return False
            return True
        return False

    def _block_ip(self, client_id: str):
        """Bloqueia um IP por violação de rate limit"""
        self.blocked_ips[client_id] = datetime.now()
        self.logger.warning(f"IP {client_id} bloqueado por violação de rate limit")

    def _check_minute_limit(self, client_id: str, current_time: datetime) -> bool:
        """Verifica limite de requisições por minuto"""
        minute_ago = current_time - timedelta(minutes=1)
        recent_requests = [
            req_time for req_time in self.request_history[client_id]
            if req_time > minute_ago
        ]
        return len(recent_requests) <= self.rate_limits.requests_per_minute

    def _check_hour_limit(self, client_id: str, current_time: datetime) -> bool:
        """Verifica limite de requisições por hora"""
        hour_ago = current_time - timedelta(hours=1)
        recent_requests = [
            req_time for req_time in self.request_history[client_id]
            if req_time > hour_ago
        ]
        return len(recent_requests) <= self.rate_limits.requests_per_hour

    def _check_day_limit(self, client_id: str, current_time: datetime) -> bool:
        """Verifica limite de requisições por dia"""
        day_ago = current_time - timedelta(days=1)
        recent_requests = [
            req_time for req_time in self.request_history[client_id]
            if req_time > day_ago
        ]
        return len(recent_requests) <= self.rate_limits.requests_per_day

    def get_client_stats(self, client_id: str) -> Dict:
        """Retorna estatísticas de uso do cliente"""
        if client_id not in self.request_history:
            return {
                "requests_last_minute": 0,
                "requests_last_hour": 0,
                "requests_last_day": 0,
                "is_blocked": False
            }

        current_time = datetime.now()
        minute_ago = current_time - timedelta(minutes=1)
        hour_ago = current_time - timedelta(hours=1)
        day_ago = current_time - timedelta(days=1)

        return {
            "requests_last_minute": len([t for t in self.request_history[client_id] if t > minute_ago]),
            "requests_last_hour": len([t for t in self.request_history[client_id] if t > hour_ago]),
            "requests_last_day": len([t for t in self.request_history[client_id] if t > day_ago]),
            "is_blocked": self._is_ip_blocked(client_id)
        } 