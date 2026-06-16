import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import jwt
from tqdm import tqdm

def generate_test_tokens() -> List[Dict]:
    """Gera tokens JWT para teste."""
    tokens = []
    
    # 1. Tokens com diferentes algoritmos
    algorithms = ["HS256", "HS384", "HS512", "RS256", "none"]
    for alg in algorithms:
        try:
            token = jwt.encode(
                {"sub": "123", "exp": datetime.utcnow() + timedelta(days=1)},
                "test_secret" if alg != "none" else None,
                algorithm=alg
            )
            tokens.append({
                "token": token,
                "description": f"Token com algoritmo {alg}"
            })
        except Exception as e:
            logging.warning(f"Erro ao gerar token com algoritmo {alg}: {e}")
    
    # 2. Tokens com diferentes claims
    claims = [
        {"sub": "123"},  # Sem expiração
        {"sub": "123", "exp": datetime.utcnow() - timedelta(days=1)},  # Expirado
        {"sub": "123", "exp": datetime.utcnow() + timedelta(days=1)},  # Válido
        {"sub": "123", "iat": datetime.utcnow()},  # Sem expiração, com iat
        {"sub": "123", "nbf": datetime.utcnow() + timedelta(hours=1)},  # Não válido ainda
        {"sub": "123", "iss": "test", "aud": "api"},  # Com iss e aud
        {"sub": "123", "roles": ["user", "admin"]},  # Com roles
        {"sub": "123", "permissions": ["read", "write"]}  # Com permissions
    ]
    
    for claim in claims:
        token = jwt.encode(claim, "test_secret", algorithm="HS256")
        tokens.append({
            "token": token,
            "description": f"Token com claims: {list(claim.keys())}"
        })
    
    # 3. Tokens com headers personalizados
    headers = [
        {"typ": "JWT"},
        {"cty": "application/json"},
        {"kid": "test-key-1"},
        {"jku": "https://example.com/keys.json"},
        {"x5u": "https://example.com/cert.pem"},
        {"crit": ["exp", "iat"]},
        {"alg": "HS256", "typ": "JWT", "cty": "application/json"}
    ]
    
    for header in headers:
        token = jwt.encode(
            {"sub": "123", "exp": datetime.utcnow() + timedelta(days=1)},
            "test_secret",
            algorithm="HS256",
            headers=header
        )
        tokens.append({
            "token": token,
            "description": f"Token com headers: {list(header.keys())}"
        })
    
    # 4. Tokens com payloads maliciosos
    malicious_payloads = [
        {"sub": "123", "exp": datetime.utcnow() + timedelta(days=1), "admin": True},
        {"sub": "123", "exp": datetime.utcnow() + timedelta(days=1), "role": "admin"},
        {"sub": "123", "exp": datetime.utcnow() + timedelta(days=1), "is_admin": 1},
        {"sub": "123", "exp": datetime.utcnow() + timedelta(days=1), "access_level": 999}
    ]
    
    for payload in malicious_payloads:
        token = jwt.encode(payload, "test_secret", algorithm="HS256")
        tokens.append({
            "token": token,
            "description": f"Token com payload potencialmente malicioso: {list(payload.keys())}"
        })
    
    return tokens

def main():
    """Gera tokens de teste e salva em arquivo."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Cria diretório de dados
        data_dir = Path("data/jwt_samples")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Gera tokens
        logger.info("Gerando tokens de teste...")
        test_tokens = generate_test_tokens()
        
        # Salva em arquivo
        output_file = data_dir / "test_tokens.txt"
        with open(output_file, "w") as f:
            for token_data in test_tokens:
                f.write(f"{token_data['token']}\n")
        
        # Salva metadados
        metadata_file = data_dir / "test_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(test_tokens, f, indent=2)
        
        logger.info(f"Tokens de teste gerados e salvos em {output_file}")
        logger.info(f"Metadados salvos em {metadata_file}")
        
    except Exception as e:
        logger.error(f"Erro ao gerar dados de teste: {e}")
        raise

if __name__ == "__main__":
    main() 