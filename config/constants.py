"""
Constantes globais e avançadas do projeto EVIL_JWT_FORCE
"""

import os
from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
LOG_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
REPORT_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"
MODULES_DIR = BASE_DIR / "modules"
SCRIPTS_DIR = BASE_DIR / "scripts"
TEMP_DIR = BASE_DIR / "temp"

# Arquivos principais
VALID_CREDS_FILE = OUTPUT_DIR / "valid_credentials.txt"
INVALID_CREDS_FILE = OUTPUT_DIR / "invalid_credentials.txt"
WORDLIST_FILE = OUTPUT_DIR / "wordlist.txt"
TESTED_WORDS_FILE = OUTPUT_DIR / "wordlist_tested.txt"
LOG_FILE = LOG_DIR / "jwt_force.log"
REPORT_FILE = REPORT_DIR / "report.html"
INTERCEPTED_TOKENS_FILE = OUTPUT_DIR / "intercepted_tokens.txt"
DISCOVERED_ENDPOINTS_FILE = OUTPUT_DIR / "discovered_endpoints.txt"
PROXY_FILE = CONFIG_DIR / "proxies.txt"
CONFIG_YAML = CONFIG_DIR / "config.yaml"

# Configurações de logging avançado
LOG_FORMAT = "[%(asctime)s] %(levelname)s %(module)s: %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = "INFO"

# Cores para logging e terminal
COLORS = {
    "SUCCESS": "\033[92m",
    "WARNING": "\033[93m",
    "ERROR": "\033[91m",
    "INFO": "\033[94m",
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m"
}

# Configurações de timeout e threads
DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3
DEFAULT_THREADS = 10

# Configurações de proxy
DEFAULT_PROXY = "http://127.0.0.1:8082"
USE_PROXY = True
ROTATE_PROXIES = True

# Configurações HTTP
DEFAULT_USER_AGENT = "Mozilla/5.0 (EVIL_JWT_FORCE v1.2.0)"
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "application/json"
}

# JWT Configurações
JWT_ALGORITHMS = ["HS256", "RS256", "ES256", "PS256"]
JWT_DEFAULT_ALGORITHM = "HS256"
JWT_EXP_DELTA = 3600  # segundos
JWT_MODE = "bruteforce"

# AES Configurações
AES_MODES = ["CBC", "ECB", "CFB", "OFB"]
AES_DEFAULT_MODE = "CBC"
AES_KEY_LENGTH = 16
AES_PADDING_SCHEMES = ["PKCS7", "ISO10126", "ZeroPadding", "ANSIX923"]

# Auto Discovery
AUTO_DISCOVERY_ENABLED = True
AUTO_DISCOVERY_SCAN_DEPTH = 3
AUTO_DISCOVERY_TIMEOUT = 5
AUTO_DISCOVERY_COMMON_ENDPOINTS = [
    "/api/auth", "/api/login", "/auth/token", "/oauth/token",
    "/api/v1/auth", "/api/v2/auth", "/auth/jwt", "/login",
    "/admin/login", "/user/login"
]
AUTO_DISCOVERY_METHODS = ["GET", "POST"]

# Relatórios
REPORT_TEMPLATES = ["HTML", "PDF", "TXT"]

# Função utilitária para garantir diretórios essenciais
def ensure_directories():
    for d in [LOG_DIR, OUTPUT_DIR, REPORT_DIR, DATA_DIR, TEMP_DIR]:
        os.makedirs(d, exist_ok=True)

# Chame ensure_directories() ao importar para garantir estrutura
ensure_directories()