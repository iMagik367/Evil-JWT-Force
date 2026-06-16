"""
Funções essenciais para trabalhar com JWT - versão simplificada
"""

import jwt
import base64
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger("EVIL_JWT_FORCE.jwt_utils_simple")

def decode_jwt(token: str, verify_signature=False, key=None, algorithm=None, options=None):
    """Decodifica um token JWT"""
    try:
        opts = {"verify_signature": False}
        if options:
            opts.update(options)
        if verify_signature and key:
            return jwt.decode(token, key, algorithms=[algorithm] if algorithm else ["HS256"], options=opts)
        return jwt.decode(token, options=opts)
    except Exception as e:
        logger.error(f"Erro ao decodificar JWT: {e}")
        return None

def extract_parts(token: str):
    """Extrai as partes de um token JWT"""
    try:
        header, payload, signature = token.split('.')
        def pad_b64(s):
            return s + '=' * (-len(s) % 4)
        return {
            "header": json.loads(base64.urlsafe_b64decode(pad_b64(header)).decode()),
            "payload": json.loads(base64.urlsafe_b64decode(pad_b64(payload)).decode()),
            "signature": signature
        }
    except Exception as e:
        logger.error(f"Token inválido: {e}")
        return None

def generate_token(payload: dict, secret: str, algorithm: str = "HS256", headers: dict = None):
    """Gera um token JWT"""
    try:
        return jwt.encode(payload, secret, algorithm=algorithm, headers=headers)
    except Exception as e:
        logger.error(f"Erro ao gerar JWT: {e}")
        return None

def generate_test_token():
    """Gera um token JWT para testes"""
    payload = {
        "sub": "1234567890",
        "name": "Test User",
        "iat": 1516239022,
        "admin": True
    }
    return generate_token(payload, 'test_secret', 'HS256')

def is_jwt(token: str):
    """Verifica se uma string é um token JWT válido (formato básico)"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return False
        # Verifica se as partes podem ser decodificadas como Base64
        base64.urlsafe_b64decode(parts[0] + '==')
        base64.urlsafe_b64decode(parts[1] + '==')
        return True
    except Exception:
        return False

def decode_token_parts(token: str):
    """Decodifica as partes de um token JWT e retorna como um dicionário"""
    try:
        parts = extract_parts(token)
        if not parts:
            return {"error": "Token inválido"}
        
        # Adiciona informações adicionais para análise
        now = datetime.now().timestamp()
        exp = parts["payload"].get("exp", 0)
        
        parts["analysis"] = {
            "expired": exp > 0 and exp < now,
            "time_to_expiration": exp - now if exp > now else 0,
            "algorithm": parts["header"].get("alg", "unknown"),
            "is_admin": parts["payload"].get("admin", False)
        }
        
        return parts
    except Exception as e:
        logger.error(f"Erro ao decodificar partes do token: {e}")
        return {"error": str(e)}

def check_tools_availability():
    """Simulação de verificação de ferramentas disponíveis"""
    return {
        "jwt_tool": True,
        "jwtXploiter": False,
        "jwt-hack": False,
        "jwt-cracker": True,
        "jwtcat": True,
        "c-jwt-cracker": False
    }

if __name__ == "__main__":
    # Teste rápido
    token = generate_test_token()
    print(f"Token gerado: {token}")
    print(f"Partes do token: {decode_token_parts(token)}") 