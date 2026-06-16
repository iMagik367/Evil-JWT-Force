#!/usr/bin/env python3
"""
Módulo utilitário para formatação e análise de tokens JWT
"""

import base64
import json
import logging
import re
from typing import Dict, Any, Optional, List, Tuple

# Configuração de logging
logging.basicConfig(
    filename='logs/token_formatter.log',
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [TOKEN_FORMATTER] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('TOKEN_FORMATTER')

def decode_base64_url(data: str) -> bytes:
    """
    Decodifica um string base64url para bytes.
    Adiciona padding se necessário.
    """
    padding_needed = len(data) % 4
    if padding_needed:
        data += '=' * (4 - padding_needed)
    
    try:
        return base64.urlsafe_b64decode(data)
    except Exception as e:
        logger.error(f"Erro ao decodificar base64url: {e}")
        return b''

def decode_jwt_part(part: str) -> Dict[str, Any]:
    """
    Decodifica uma parte do token JWT (header ou payload).
    """
    try:
        decoded = decode_base64_url(part)
        return json.loads(decoded.decode('utf-8'))
    except Exception as e:
        logger.error(f"Erro ao decodificar parte do JWT: {e}")
        return {}

def format_token_parts(token: str) -> Dict[str, Any]:
    """
    Formata um token JWT em suas partes componentes: header, payload e signature.
    
    Args:
        token: Token JWT para ser formatado
        
    Returns:
        Dicionário com as partes do token decodificadas
    """
    try:
        # Verificar formato do token
        if not re.match(r'^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$', token):
            logger.warning(f"Formato de token inválido: {token[:15]}...")
            return {"error": "Formato de token inválido"}
        
        # Dividir o token em suas partes
        parts = token.split('.')
        if len(parts) != 3:
            logger.warning(f"Token não possui 3 partes: {token[:15]}...")
            return {"error": "Token não possui 3 partes"}
        
        header_part, payload_part, signature_part = parts
        
        # Decodificar header e payload
        header = decode_jwt_part(header_part)
        payload = decode_jwt_part(payload_part)
        
        # A assinatura não é um JSON, então apenas mantemos o valor codificado
        result = {
            "header": header,
            "payload": payload,
            "signature": signature_part,
            "raw": {
                "header": header_part,
                "payload": payload_part,
                "signature": signature_part
            }
        }
        
        logger.info(f"Token formatado com sucesso: {token[:15]}...")
        return result
    
    except Exception as e:
        logger.error(f"Erro ao formatar token: {e}")
        return {"error": str(e)}

def reconstruct_token(header: Dict[str, Any], payload: Dict[str, Any], signature: Optional[str] = None) -> str:
    """
    Reconstrói um token JWT a partir de suas partes componentes.
    
    Args:
        header: Dicionário contendo o header
        payload: Dicionário contendo o payload
        signature: String contendo a assinatura (opcional)
        
    Returns:
        Token JWT reconstruído
    """
    try:
        # Codificar header e payload
        header_json = json.dumps(header, separators=(',', ':'))
        payload_json = json.dumps(payload, separators=(',', ':'))
        
        header_b64 = base64.urlsafe_b64encode(header_json.encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip('=')
        
        # Se não foi fornecida assinatura, retorna token sem assinatura
        if signature is None:
            token = f"{header_b64}.{payload_b64}."
        else:
            # Remover padding da assinatura se existir
            signature = signature.rstrip('=')
            token = f"{header_b64}.{payload_b64}.{signature}"
        
        logger.info("Token reconstruído com sucesso")
        return token
    
    except Exception as e:
        logger.error(f"Erro ao reconstruir token: {e}")
        return ""

def extract_token_from_auth_header(auth_header: str) -> Optional[str]:
    """
    Extrai um token JWT de um cabeçalho de autorização
    
    Args:
        auth_header: Cabeçalho de autorização (ex: "Bearer eyJhbGci...")
        
    Returns:
        Token JWT extraído ou None se não encontrado
    """
    try:
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if re.match(r'^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$', token):
                logger.info("Token extraído com sucesso do cabeçalho de autorização")
                return token
        
        logger.warning(f"Formato de cabeçalho de autorização inválido: {auth_header[:20]}...")
        return None
    
    except Exception as e:
        logger.error(f"Erro ao extrair token do cabeçalho: {e}")
        return None

def extract_token_from_cookie(cookie_str: str, cookie_name: Optional[str] = None) -> Optional[str]:
    """
    Extrai um token JWT de um cookie
    
    Args:
        cookie_str: String de cookie (ex: "jwt=eyJhbGci...; Path=/;")
        cookie_name: Nome do cookie contendo o token (opcional)
        
    Returns:
        Token JWT extraído ou None se não encontrado
    """
    try:
        cookies = {}
        for item in cookie_str.split(';'):
            if '=' in item:
                name, value = item.split('=', 1)
                cookies[name.strip()] = value.strip()
        
        # Se o nome do cookie for fornecido, verificar apenas esse cookie
        if cookie_name and cookie_name in cookies:
            token = cookies[cookie_name]
            if re.match(r'^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$', token):
                logger.info(f"Token extraído com sucesso do cookie '{cookie_name}'")
                return token
            return None
        
        # Se o nome do cookie não for fornecido, procurar por qualquer cookie que pareça um token JWT
        for name, value in cookies.items():
            if re.match(r'^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$', value):
                logger.info(f"Token extraído com sucesso do cookie '{name}'")
                return value
        
        logger.warning("Nenhum token encontrado nos cookies")
        return None
    
    except Exception as e:
        logger.error(f"Erro ao extrair token do cookie: {e}")
        return None

def format_token_for_display(token: str) -> str:
    """
    Formata um token JWT para exibição mais legível
    
    Args:
        token: Token JWT para ser formatado
        
    Returns:
        Token formatado para exibição
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return token
        
        header_part, payload_part, signature_part = parts
        
        # Decodificar header e payload
        header = decode_jwt_part(header_part)
        payload = decode_jwt_part(payload_part)
        
        # Formatar para exibição
        header_str = json.dumps(header, indent=2)
        payload_str = json.dumps(payload, indent=2)
        
        formatted = f"HEADER:\n{header_str}\n\nPAYLOAD:\n{payload_str}\n\nSIGNATURE:\n{signature_part}"
        return formatted
    
    except Exception as e:
        logger.error(f"Erro ao formatar token para exibição: {e}")
        return token

if __name__ == "__main__":
    # Exemplo de uso
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    # Formatar token
    parts = format_token_parts(test_token)
    print(json.dumps(parts, indent=2))
    
    # Formatar para exibição
    print("\nToken formatado para exibição:")
    print(format_token_for_display(test_token)) 