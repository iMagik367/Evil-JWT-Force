"""
Injeto PyOpenSSL no urllib3 para forçar o uso de OpenSSL no place de SChannel, evitando erros de handshake em Windows.
"""
try:
    from urllib3.contrib import pyopenssl
    pyopenssl.inject_into_urllib3()
except Exception:
    pass

import logging
from typing import Tuple, Dict, Any
from .network.connection_manager import ConnectionManager

# Configuração de logging
logger = logging.getLogger(__name__)

def test_ai_connection(provider: str, config: dict) -> Tuple[bool, str]:
    """
    Testa conexão com IA selecionada.
    :param provider: 'OpenAI', 'Pentest Muse', 'LibreChat'
    :param config: dict com os campos relevantes
    :return: (True, 'OK') ou (False, 'Erro detalhado')
    """
    try:
        if provider == 'OpenAI':
            key = config.get('openai_key', '')
            conn = ConnectionManager(
                base_url='https://api.openai.com',
                timeout=10,
                verify_ssl=True
            )
            conn.session.headers.update({'Authorization': f'Bearer {key}'})
            response = conn.get('/v1/models')
            
            if isinstance(response, dict) and "error" in response:
                return False, f"Erro na conexão OpenAI: {response['error']}"
                
            return True, 'OK'
            
        elif provider == 'Pentest Muse':
            key = config.get('pentest_muse_key', '')
            conn = ConnectionManager(
                base_url='https://api.pentestmuse.ai',
                timeout=10,
                verify_ssl=False
            )
            conn.session.headers.update({
                'Authorization': f'Bearer {key}',
                'User-Agent': 'pentest-muse-cli/1.0'
            })
            
            # Tenta primeiro o endpoint v1
            response = conn.get('/v1/ping')
            if isinstance(response, dict) and "error" in response:
                # Se falhar, tenta o endpoint raiz
                response = conn.get('/')
                
            if isinstance(response, dict) and "error" in response:
                return False, f"Erro na conexão Pentest Muse: {response['error']}"
                
            return True, 'OK'
            
        elif provider == 'LibreChat':
            url = config.get('librechat_url', '')
            conn = ConnectionManager(
                base_url=url,
                timeout=10,
                verify_ssl=False
            )
            response = conn.get('/api/health')
            
            if isinstance(response, dict) and "error" in response:
                return False, f"Erro na conexão LibreChat: {response['error']}"
                
            return True, 'OK'
            
        else:
            return False, f"Provedor de IA desconhecido: {provider}"
            
    except Exception as e:
        logger.error(f"Erro ao testar conexão com {provider}: {str(e)}")
        return False, f"Erro inesperado: {str(e)}" 