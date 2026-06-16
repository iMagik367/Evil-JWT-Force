"""
EVIL_JWT_FORCE Core Package

Este módulo centraliza as funcionalidades principais do sistema, incluindo:
- Autenticação e gerenciamento de sessões JWT
- Parsing de argumentos de linha de comando
- Geração de relatórios detalhados
- Ataques de força bruta em JWT
- Injeção SQL automatizada

Desenvolvido para máxima extensibilidade, robustez e facilidade de manutenção.
"""

import logging
import importlib

__version__ = "1.0.0"
__author__ = "Equipe EVIL_JWT_FORCE"
__license__ = "MIT"

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("EVIL_JWT_FORCE.core")

def _safe_import(module_name, symbol_name):
    try:
        module = importlib.import_module(f"core.{module_name}")
        symbol = getattr(module, symbol_name)
        logger.info(f"Importado: {symbol_name} de {module_name}")
        return symbol
    except Exception as e:
        logger.warning(f"Falha ao importar {symbol_name} de {module_name}: {e}")
        return None

Authenticator = _safe_import("auth", "Authenticator")
parse_args = _safe_import("cli", "parse_args")
generate_report = _safe_import("report", "generate_report")
JWTBruteforcer = _safe_import("bruteforce", "JWTBruteforcer")
SQLInjector = _safe_import("sql_injector", "SQLInjector")
generate_wordlist = _safe_import("wordlist_generator", "generate_wordlist")

__all__ = [
    "Authenticator",
    "JWTBruteforcer",
    "SQLInjector",
    "generate_report",
    "parse_args",
    "generate_wordlist"
]