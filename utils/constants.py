import os
import platform
from pathlib import Path

# === Platform and Environment Detection ===
IS_LINUX = platform.system() == "Linux"
IS_KALI = IS_LINUX and (os.path.exists("/etc/os-release") and any("kali" in line.lower() for line in open("/etc/os-release")))

# === Directory Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

# === File Definitions ===
DEFAULT_CREDS_FILE = CONFIG_DIR / "default_creds.txt"
WORDLIST_FILE = OUTPUT_DIR / "data" / "wordlist" / "wordlist_final.txt"
INTERCEPTED_TOKENS_FILE = OUTPUT_DIR / "intercepted_tokens.txt"
FOUND_SECRETS_FILE = OUTPUT_DIR / "found_secrets.txt"
FAIL_CREDENTIALS_FILE = OUTPUT_DIR / "fail_credentials.txt"
VALID_CREDENTIALS_FILE = OUTPUT_DIR / "valid_credentials.txt"

# === Logging Settings ===
LOG_LEVEL = "DEBUG"
LOG_FILE = LOGS_DIR / "evil_jwt_force.log"

# === Terminal Colors (Linux Only) ===
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# === Timeout and Threading ===
DEFAULT_TIMEOUT = 10
MAX_THREADS = 32
RETRY_COUNT = 3

# === Proxy Settings ===
USE_PROXY = True
PROXY_LIST = ['http://localhost:8080']
PROXY_TYPE = 'http'
MAX_PROXY_FAILURES = 5
ROTATE_PROXIES = False

# === Linux User-Agent Definitions ===
LINUX_USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]
DEFAULT_USER_AGENT = LINUX_USER_AGENTS[0]

# === HTTP Headers ===
DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# === JWT and AES Settings ===
JWT_ALGORITHMS = ["HS256", "RS256", "ES256", "PS256"]
# Supported algorithms: exclude PS256 for compatibility tests
SUPPORTED_ALGORITHMS = ["HS256", "RS256", "ES256"]
DEFAULT_WORDLIST = str(WORDLIST_FILE)
JWT_MODE = "bruteforce"
JWT_WORDLIST = WORDLIST_FILE
JWT_MAX_TOKEN_LENGTH = 4096
JWT_MIN_TOKEN_LENGTH = 32
AES_MODES = ["CBC", "ECB", "CFB", "OFB", "CTR"]
AES_KEY_LENGTHS = [128, 192, 256]
AES_PADDING = ["PKCS7", "ISO10126", "ANSIX923", "ZeroPadding"]
AES_IV_LENGTH = 16

# === Output and Wordlist Configurations ===
REPORT_HTML = REPORTS_DIR / "report.html"
WORDLISTS = {
    "default": WORDLIST_FILE,
    "rockyou": "/usr/share/wordlists/rockyou.txt",
    "custom": OUTPUT_DIR / "data" / "wordlist" / "custom_wordlist.txt"
}

# === Common Endpoints and Payloads ===
COMMON_ENDPOINTS = [
    "/api/v1/auth/login",
    "/api/v1/auth/token",
    "/api/v1/user",
    "/api/v1/admin",
    "/login",
    "/auth",
    "/token",
    "/jwt",
    "/session"
]
SQL_PAYLOADS = [
    "' OR '1'='1' -- ",
    '" OR "1"="1" -- ',
    "' OR 1=1 -- ",
    '" OR 1=1 -- ',
    "' OR 'a'='a' -- ",
    '" OR "a"="a" -- '
]

# === HTTP Status Codes ===
HTTP_STATUS_SUCCESS = [200, 201, 202, 204]
HTTP_STATUS_REDIRECT = [301, 302, 303, 307, 308]
HTTP_STATUS_CLIENT_ERROR = [400, 401, 403, 404, 405, 429]
HTTP_STATUS_SERVER_ERROR = [500, 501, 502, 503, 504]

# === Advanced Security and Miscellaneous ===
ENABLE_COLOR_OUTPUT = True
SAVE_SESSION = True
LINUX_ONLY = True

# === Utility Functions ===
def get_random_user_agent():
    import random
    return random.choice(LINUX_USER_AGENTS)

def get_headers(custom_headers=None):
    headers = DEFAULT_HEADERS.copy()
    if custom_headers:
        headers.update(custom_headers)
    return headers

# === Exported Symbols ===
__all__ = [
    "IS_LINUX", "IS_KALI", "BASE_DIR", "CONFIG_DIR", "OUTPUT_DIR", "REPORTS_DIR", "LOGS_DIR", "DATA_DIR",
    "DEFAULT_CREDS_FILE", "WORDLIST_FILE", "INTERCEPTED_TOKENS_FILE", "FOUND_SECRETS_FILE", "FAIL_CREDENTIALS_FILE", "VALID_CREDENTIALS_FILE",
    "LOG_LEVEL", "LOG_FILE", "Colors", "DEFAULT_TIMEOUT", "MAX_THREADS", "RETRY_COUNT",
    "USE_PROXY", "PROXY_LIST", "PROXY_TYPE", "MAX_PROXY_FAILURES", "ROTATE_PROXIES",
    "LINUX_USER_AGENTS", "DEFAULT_USER_AGENT", "DEFAULT_HEADERS", "JWT_ALGORITHMS", "JWT_MODE", "JWT_WORDLIST", "JWT_MAX_TOKEN_LENGTH", "JWT_MIN_TOKEN_LENGTH",
    "AES_MODES", "AES_KEY_LENGTHS", "AES_PADDING", "AES_IV_LENGTH", "REPORT_HTML", "WORDLISTS",
    "COMMON_ENDPOINTS", "SQL_PAYLOADS", "HTTP_STATUS_SUCCESS", "HTTP_STATUS_REDIRECT", "HTTP_STATUS_CLIENT_ERROR", "HTTP_STATUS_SERVER_ERROR",
    "ENABLE_COLOR_OUTPUT", "SAVE_SESSION", "LINUX_ONLY", "get_random_user_agent", "get_headers",
    "SUPPORTED_ALGORITHMS", "DEFAULT_WORDLIST",
]

FUZZ_PAYLOADS = [
    "{{user}}",
    "{{pass}}",
    "{{email}}",
    "{{id}}",
    "{{token}}",
    "{{jwt}}",
    "{{sql}}",
    "{{xss}}",
    "{{lfi}}",
    "{{rfi}}",
]