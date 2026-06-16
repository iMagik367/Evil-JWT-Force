import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import jwt
from tqdm import tqdm

def generate_vulnerable_tokens() -> List[Dict]:
    """Gera tokens JWT vulneráveis para treinamento."""
    tokens = []
    
    # 1. Token com algoritmo 'none'
    token_none = jwt.encode(
        {"sub": "123", "exp": datetime.utcnow() + timedelta(days=1)},
        None,
        algorithm="none"
    )
    tokens.append({
        "token": token_none,
        "vulnerability": "none_alg",
        "description": "Token usando algoritmo 'none'"
    })
    
    # 2. Token sem expiração
    token_no_exp = jwt.encode(
        {"sub": "123"},
        "weak_secret",
        algorithm="HS256"
    )
    tokens.append({
        "token": token_no_exp,
        "vulnerability": "no_exp",
        "description": "Token sem campo de expiração"
    })
    
    # 3. Token expirado
    token_expired = jwt.encode(
        {
            "sub": "123",
            "exp": datetime.utcnow() - timedelta(days=1)
        },
        "weak_secret",
        algorithm="HS256"
    )
    tokens.append({
        "token": token_expired,
        "vulnerability": "expired_token",
        "description": "Token expirado"
    })
    
    # 4. Token com KID vulnerável
    token_kid = jwt.encode(
        {"sub": "123", "exp": datetime.utcnow() + timedelta(days=1)},
        "weak_secret",
        algorithm="HS256",
        headers={"kid": "../../../etc/passwd"}
    )
    tokens.append({
        "token": token_kid,
        "vulnerability": "kid_injection",
        "description": "Token com KID vulnerável a path traversal"
    })
    
    # 5. Token com JKU malicioso
    token_jku = jwt.encode(
        {"sub": "123", "exp": datetime.utcnow() + timedelta(days=1)},
        "weak_secret",
        algorithm="HS256",
        headers={"jku": "https://evil.com/keys.json"}
    )
    tokens.append({
        "token": token_jku,
        "vulnerability": "jku_injection",
        "description": "Token com JKU apontando para servidor malicioso"
    })
    
    return tokens

def generate_secure_tokens() -> List[Dict]:
    """Gera tokens JWT seguros para treinamento."""
    tokens = []
    
    # Chave secreta forte
    strong_secret = "x" * 32  # 32 bytes
    
    # 1. Token seguro básico
    token_secure = jwt.encode(
        {
            "sub": "123",
            "exp": datetime.utcnow() + timedelta(days=1),
            "iat": datetime.utcnow(),
            "iss": "secure_app"
        },
        strong_secret,
        algorithm="HS256"
    )
    tokens.append({
        "token": token_secure,
        "vulnerability": None,
        "description": "Token seguro com todos os campos necessários"
    })
    
    # 2. Token com claims adicionais
    token_claims = jwt.encode(
        {
            "sub": "123",
            "exp": datetime.utcnow() + timedelta(days=1),
            "iat": datetime.utcnow(),
            "iss": "secure_app",
            "aud": "api",
            "roles": ["user", "admin"]
        },
        strong_secret,
        algorithm="HS256"
    )
    tokens.append({
        "token": token_claims,
        "vulnerability": None,
        "description": "Token seguro com claims adicionais"
    })
    
    # 3. Token com header personalizado
    token_header = jwt.encode(
        {
            "sub": "123",
            "exp": datetime.utcnow() + timedelta(days=1)
        },
        strong_secret,
        algorithm="HS256",
        headers={"typ": "JWT", "cty": "application/json"}
    )
    tokens.append({
        "token": token_header,
        "vulnerability": None,
        "description": "Token seguro com header personalizado"
    })
    
    return tokens

def main():
    """Gera dados de treinamento e salva em arquivo."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Cria diretório de dados
        data_dir = Path("data/jwt_samples")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Gera tokens
        logger.info("Gerando tokens vulneráveis...")
        vulnerable_tokens = generate_vulnerable_tokens()
        
        logger.info("Gerando tokens seguros...")
        secure_tokens = generate_secure_tokens()
        
        # Combina todos os tokens
        all_tokens = vulnerable_tokens + secure_tokens
        
        # Salva em arquivo
        output_file = data_dir / "raw_tokens.txt"
        with open(output_file, "w") as f:
            for token_data in all_tokens:
                f.write(f"{token_data['token']}\n")
        
        # Salva metadados
        metadata_file = data_dir / "token_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(all_tokens, f, indent=2)
        
        logger.info(f"Tokens gerados e salvos em {output_file}")
        logger.info(f"Metadados salvos em {metadata_file}")
        
    except Exception as e:
        logger.error(f"Erro ao gerar dados de treinamento: {e}")
        raise

if __name__ == "__main__":
    main() 