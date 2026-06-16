"""
Evil-Force-JWT - Módulos de Ataque e Análise
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/modules.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MODULES')

# Garantir que o diretório de logs exista
os.makedirs('logs', exist_ok=True)

# Adicionar o diretório raiz ao path para importações relativas
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Importar módulos principais
try:
    from .jwt_utils_simple import decode_token_parts, extract_parts, is_jwt, generate_token
    from .jwt_decrypt import JWTDecrypt
    from .token_bruteforce import TokenBruteforcer
    from .scan_target import TargetScanner
    from .fuzz_jwt import JWTFuzzer
    
    logger.info("Módulos carregados com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar módulos: {e}")

# Verificar se os módulos estão disponíveis
def check_modules_availability():
    """Verifica quais módulos estão disponíveis"""
    modules = {
        "jwt_utils_simple": "decode_token_parts" in globals(),
        "jwt_decrypt": "JWTDecrypt" in globals(),
        "token_bruteforce": "TokenBruteforcer" in globals(),
        "scan_target": "TargetScanner" in globals(),
        "fuzz_jwt": "JWTFuzzer" in globals()
    }
    
    logger.info(f"Status dos módulos: {modules}")
    return modules

# Verificar se os módulos dependentes estão instalados
def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    dependencies = {
        "jwt": True,
        "requests": True,
        "cryptography": True
    }
    
    try:
        import jwt
    except ImportError:
        dependencies["jwt"] = False
    
    try:
        import requests
    except ImportError:
        dependencies["requests"] = False
    
    try:
        import cryptography
    except ImportError:
        dependencies["cryptography"] = False
    
    logger.info(f"Status das dependências: {dependencies}")
    return dependencies

__all__ = [
    # Funções de jwt_utils_simple
    'decode_token_parts', 'extract_parts', 'is_jwt', 'generate_token',
    
    # Classes principais
    'JWTDecrypt', 'TokenBruteforcer', 'TargetScanner', 'JWTFuzzer',
    
    # Funções utilitárias
    'check_modules_availability', 'check_dependencies'
]

__version__ = "1.0.0"
__author__ = "EVIL_JWT_FORCE Team"
__license__ = "MIT"