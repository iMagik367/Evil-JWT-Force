"""
EVIL_JWT_FORCE Config Module
Configurações e constantes globais do projeto
"""

from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
LOG_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = BASE_DIR / "reports"

# Configurações de timeout
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Cores para logging
COLORS = {
    'SUCCESS': '\033[92m',
    'WARNING': '\033[93m',
    'ERROR': '\033[91m',
    'INFO': '\033[94m',
    'RESET': '\033[0m'
}

__version__ = "1.0.0"