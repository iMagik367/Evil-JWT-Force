"""
Módulo de logging customizado e avançado para EVIL_JWT_FORCE
"""

import os
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Configurações de cores cross-platform
try:
    import colorama
    colorama.init()
    COLORS = {
        'SUCCESS': colorama.Fore.GREEN,
        'WARNING': colorama.Fore.YELLOW,
        'ERROR': colorama.Fore.RED,
        'INFO': colorama.Fore.CYAN,
        'RESET': colorama.Style.RESET_ALL
    }
except ImportError:
    COLORS = {
        'SUCCESS': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'INFO': '\033[94m',
        'RESET': '\033[0m'
    }

# Diretório de logs
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: COLORS['INFO'],
        logging.INFO: COLORS['SUCCESS'],
        logging.WARNING: COLORS['WARNING'],
        logging.ERROR: COLORS['ERROR'],
        logging.CRITICAL: COLORS['ERROR'],
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, COLORS['RESET'])
        reset = COLORS['RESET']
        msg = super().format(record)
        return f"{color}{msg}{reset}"

def setup_logger(
    name: str = "EVIL_JWT_FORCE",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Logger:
    """
    Configura e retorna um logger avançado com suporte a rotação, cores e múltiplos handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    color_formatter = ColorFormatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Evita handlers duplicados
    if not logger.handlers:
        if log_to_file:
            log_file = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(color_formatter)
            logger.addHandler(console_handler)

    logger.propagate = False
    return logger

# Logger global padrão
logger = setup_logger()

def log_structured(level: str, message: str, **kwargs):
    """
    Logging estruturado com contexto extra (útil para automação, SIEM, etc).
    """
    extra = {"context": kwargs}
    if hasattr(logger, level.lower()):
        getattr(logger, level.lower())(f"{message} | {kwargs}")
    else:
        logger.info(f"{message} | {kwargs}")

def set_log_level(level: str):
    """
    Altera dinamicamente o nível do logger global.
    """
    numeric_level = getattr(logging, level.upper(), None)
    if isinstance(numeric_level, int):
        logger.setLevel(numeric_level)
        for handler in logger.handlers:
            handler.setLevel(numeric_level)
        logger.info(f"Nível de log alterado para {level.upper()}")
    else:
        logger.error(f"Nível de log inválido: {level}")

def get_logger(name=None):
    return logging.getLogger(name)