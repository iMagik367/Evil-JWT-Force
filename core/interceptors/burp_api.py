import logging
from typing import Dict, Any, Optional, Callable
from utils.network.connection_manager import ConnectionManager

# Configuração de logging
logger = logging.getLogger(__name__)

class BurpAPI:
    """
    Controla o Burp Suite via API REST de interceptação.
    Endpoints esperados:
      POST /burp/start  -> inicia proxy no target
      GET  /burp/intercept -> retorna próxima requisição interceptada
      POST /burp/forward -> reenviar requisição interceptada
      POST /burp/drop    -> descartar requisição interceptada
      POST /burp/stop    -> para proxy
    Payloads JSON:
      start: {"target": target, "script": script_path}
      forward/drop: {"id": request_id, "request": modified_request (opcional)}
    """
    def __init__(self, api_url: str, api_token: str):
        self.conn = ConnectionManager(
            base_url=api_url.rstrip('/'),
            timeout=30,
            verify_ssl=False
        )
        self.conn.session.headers.update({'Authorization': f'Bearer {api_token}'})

    def start(self, target: str, script: Optional[str] = None, log_callback: Callable[[str], None] = lambda msg: None) -> None:
        """
        Inicia a interceptação no target especificado.
        """
        payload = {"target": target}
        if script:
            payload["script"] = script
            
        log_callback(f"[BurpAPI] Iniciando interceptação de {target}")
        
        try:
            response = self.conn.post('/burp/start', json=payload)
            
            if isinstance(response, dict) and "error" in response:
                log_callback(f"[BurpAPI] Erro ao iniciar: {response['error']}")
                return
                
            log_callback(f"[BurpAPI] Start: HTTP {response.status_code}")
            
        except Exception as e:
            log_callback(f"[BurpAPI] Erro ao iniciar: {str(e)}")

    def intercept_next(self, log_callback: Callable[[str], None] = lambda msg: None) -> Optional[Dict[str, Any]]:
        """
        Retorna a próxima requisição interceptada.
        """
        try:
            response = self.conn.get('/burp/intercept')
            
            if isinstance(response, dict) and "error" in response:
                log_callback(f"[BurpAPI] Erro ao interceptar: {response['error']}")
                return None
                
            if response.status_code == 200:
                data = response.json()
                log_callback(f"[BurpAPI] Intercepted ID {data.get('id')}")
                return data
            else:
                log_callback(f"[BurpAPI] Intercept failed: HTTP {response.status_code}")
                
        except Exception as e:
            log_callback(f"[BurpAPI] Erro ao interceptar: {str(e)}")
            
        return None

    def forward(self, request_id: str, modified_request: Optional[str] = None, log_callback: Callable[[str], None] = lambda msg: None) -> None:
        """
        Reenvia a requisição interceptada.
        """
        payload = {"id": request_id}
        if modified_request:
            payload["request"] = modified_request
            
        try:
            response = self.conn.post('/burp/forward', json=payload)
            
            if isinstance(response, dict) and "error" in response:
                log_callback(f"[BurpAPI] Erro ao reenviar: {response['error']}")
                return
                
            log_callback(f"[BurpAPI] Forward: HTTP {response.status_code}")
            
        except Exception as e:
            log_callback(f"[BurpAPI] Erro ao reenviar: {str(e)}")

    def drop(self, request_id: str, log_callback: Callable[[str], None] = lambda msg: None) -> None:
        """
        Descarta a requisição interceptada.
        """
        try:
            response = self.conn.post('/burp/drop', json={"id": request_id})
            
            if isinstance(response, dict) and "error" in response:
                log_callback(f"[BurpAPI] Erro ao descartar: {response['error']}")
                return
                
            log_callback(f"[BurpAPI] Drop: HTTP {response.status_code}")
            
        except Exception as e:
            log_callback(f"[BurpAPI] Erro ao descartar: {str(e)}")

    def stop(self, log_callback: Callable[[str], None] = lambda msg: None) -> None:
        """
        Para o proxy de interceptação.
        """
        try:
            response = self.conn.post('/burp/stop')
            
            if isinstance(response, dict) and "error" in response:
                log_callback(f"[BurpAPI] Erro ao parar: {response['error']}")
                return
                
            log_callback(f"[BurpAPI] Stop: HTTP {response.status_code}")
            
        except Exception as e:
            log_callback(f"[BurpAPI] Erro ao parar: {str(e)}") 