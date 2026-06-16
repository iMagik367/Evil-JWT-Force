"""
EVIL_JWT_FORCE Utils Module
Centraliza e expõe utilitários avançados para todo o projeto.
"""

import importlib
import sys

# Importação explícita dos utilitários principais
from .helpers import (
    save_to_file,
    read_lines,
    write_lines,
    generate_nonce,
    get_current_timestamp,
    formatted_time,
    log_format,
    ensure_dir,
    clean_string,
    is_valid_url,
    safe_write_file,
    random_string,
    slugify,
    human_size,
    atomic_write,
    touch,
    remove_file,
    list_files
)
from .logger import setup_logger, logger, log_structured, set_log_level
from .constants import *
from .wordlist_engine import generate_wordlist

# Importação dinâmica e segura dos módulos de rede
def _safe_import(module_path, symbol=None):
    try:
        mod = importlib.import_module(module_path, __package__)
        if symbol:
            return getattr(mod, symbol)
        return mod
    except Exception as e:
        logger.warning(f"Falha ao importar {module_path}: {e}")
        return None

# Network utils (lazy loading)
ProxyRotator = _safe_import("utils.network.proxy_rotator", "ProxyRotator")
RequestBuilder = _safe_import("utils.network.request_builder", "RequestBuilder")
build_headers = _safe_import("utils.network.request_builder", "build_headers")
build_payload = _safe_import("utils.network.request_builder", "build_payload")

# OSINT Scraper (opcional)
OSINTScraper = _safe_import("utils.osint_scraper", "OSINTScraper")

# Exposição de todos os utilitários no __all__
__all__ = [
    # helpers
    "save_to_file", "read_lines", "write_lines", "generate_nonce", "get_current_timestamp",
    "formatted_time", "log_format", "ensure_dir", "clean_string", "is_valid_url", "safe_write_file",
    "random_string", "slugify", "human_size", "atomic_write", "touch", "remove_file", "list_files",
    # logger
    "setup_logger", "logger", "log_structured", "set_log_level",
    # constants (importa tudo)
    # wordlist
    "generate_wordlist",
    # network
    "ProxyRotator", "RequestBuilder", "build_headers", "build_payload",
    # osint
    "OSINTScraper"
]

__version__ = "1.1.0"
__author__ = "EVIL_JWT_FORCE Team"
__license__ = "MIT"