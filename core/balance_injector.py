import json
import logging
from typing import Dict, Any, Callable, Optional
from utils.network.connection_manager import ConnectionManager

# Configuração de logging
logger = logging.getLogger(__name__)

def send_forged_balance_request(
    endpoint: str,
    headers: Dict[str, str],
    body: Dict[str, Any],
    auth_type: str,
    log_callback: Callable[[str], None],
    result_callback: Callable[[Optional[Dict[str, Any]]], None]
) -> None:
    """
    Send a forged balance request to the endpoint.
    """
    try:
        log_callback(f"Enviando requisição para {endpoint}")
        
        # Parse headers
        try:
            headers_dict = json.loads(headers) if isinstance(headers, str) else headers
        except Exception as e:
            log_callback(f"Erro ao parsear headers JSON: {e}")
            result_callback(None)
            return
            
        # Parse body
        try:
            body_dict = json.loads(body) if isinstance(body, str) else body
        except Exception as e:
            log_callback(f"Erro ao parsear body JSON: {e}")
            result_callback(None)
            return
            
        # Set authentication header
        token_val = headers_dict.get('token', '')
        if auth_type == 'JWT':
            headers_dict['Authorization'] = f"JWT {token_val}"
        elif auth_type == 'Bearer':
            headers_dict['Authorization'] = f"Bearer {token_val}"
        elif auth_type == 'Cookie':
            headers_dict['Cookie'] = token_val
            
        # Configurar conexão
        conn = ConnectionManager(
            base_url=endpoint,
            timeout=30,
            verify_ssl=False
        )
        conn.session.headers.update(headers_dict)
        
        # Enviar requisição
        response = conn.post('', json=body_dict)
        
        if isinstance(response, dict) and "error" in response:
            log_callback(f"Erro na requisição: {response['error']}")
            result_callback(None)
            return
            
        log_callback(f"Status code: {response.status_code}")
        result_callback(response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text)
        
    except Exception as e:
        log_callback(f"Erro na requisição: {str(e)}")
        result_callback(None) 