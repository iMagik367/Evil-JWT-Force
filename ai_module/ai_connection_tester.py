"""
Testador de conexão para serviços de IA
"""

import logging
from typing import Dict, Any, Optional, Tuple
from utils.network.connection_manager import ConnectionManager

# Configuração de logging
logger = logging.getLogger(__name__)

def test_ai_connection(provider: str, api_key: Optional[str] = None, api_url: Optional[str] = None) -> Tuple[bool, str]:
    """
    Testa a conexão com um provedor de IA.
    
    Args:
        provider: Nome do provedor (openai, pentest_muse, librechat)
        api_key: Chave de API (opcional)
        api_url: URL base da API (opcional)
        
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
    """
    try:
        # Configurar headers
        headers = {
            "Content-Type": "application/json"
        }
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        # Configurar gerenciador de conexão
        conn = ConnectionManager(
            base_url=api_url or _get_default_url(provider),
            timeout=30,
            verify_ssl=False
        )
        conn.session.headers.update(headers)
        
        # Testar conexão
        response = conn.get("/health")
        
        if isinstance(response, dict) and "error" in response:
            logger.error(f"Erro na conexão com {provider}: {response['error']}")
            return False, f"Erro na conexão: {response['error']}"
            
        if response.status_code < 500:
            logger.info(f"Conexão com {provider} estabelecida com sucesso")
            return True, "Conexão estabelecida com sucesso"
        else:
            logger.error(f"Erro na conexão com {provider}: {response.status_code}")
            return False, f"Erro na conexão: HTTP {response.status_code}"
            
    except Exception as e:
        logger.error(f"Erro ao testar conexão com {provider}: {str(e)}")
        return False, f"Erro ao testar conexão: {str(e)}"
        
def _get_default_url(provider: str) -> str:
    """
    Retorna a URL padrão para o provedor.
    
    Args:
        provider: Nome do provedor
        
    Returns:
        str: URL base da API
    """
    urls = {
        "openai": "https://api.openai.com/v1",
        "pentest_muse": "https://api.pentestmuse.com/v1",
        "librechat": "https://api.librechat.com/v1"
    }
    return urls.get(provider.lower(), "") 