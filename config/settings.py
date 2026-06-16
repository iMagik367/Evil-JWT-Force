"""Configurações avançadas e dinâmicas do EVIL_JWT_FORCE."""

import os
import json
import yaml
from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"

# Arquivos de configuração
CONFIG_YAML = CONFIG_DIR / "config.yaml"
CONFIG_JSON = CONFIG_DIR / "config.json"

# Configuração padrão
DEFAULT_CONFIG = {
    "target_url": "",
    "threads": 10,
    "proxy": "http://127.0.0.1:8082",
    "timeout": 10,
    "user_agent": "EVIL-JWT-FORCE/1.0",
    "wordlist": str(DATA_DIR / "wordlist.txt"),
    "output_dir": str(OUTPUT_DIR),
    "log_level": "INFO"
}

def load_yaml_config():
    if CONFIG_YAML.exists():
        with open(CONFIG_YAML, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def load_json_config():
    if CONFIG_JSON.exists():
        with open(CONFIG_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def merge_configs(*configs):
    """Mescla múltiplos dicionários de configuração (ordem: prioridade maior primeiro)."""
    result = {}
    for conf in reversed(configs):
        result.update(conf)
    return result

def get_env_overrides():
    """Obtém variáveis de ambiente relevantes para sobrescrever configs."""
    env_map = {
        "target_url": os.getenv("EVIL_TARGET_URL"),
        "threads": os.getenv("EVIL_THREADS"),
        "proxy": os.getenv("EVIL_PROXY"),
        "timeout": os.getenv("EVIL_TIMEOUT"),
        "user_agent": os.getenv("EVIL_USER_AGENT"),
        "wordlist": os.getenv("EVIL_WORDLIST"),
        "output_dir": os.getenv("EVIL_OUTPUT_DIR"),
        "log_level": os.getenv("EVIL_LOG_LEVEL")
    }
    # Remove None
    return {k: v for k, v in env_map.items() if v is not None}

def get_config():
    """Carrega a configuração final, considerando YAML, JSON, padrão e variáveis de ambiente."""
    yaml_conf = load_yaml_config()
    json_conf = load_json_config()
    env_conf = get_env_overrides()
    # Ordem de prioridade: ENV > YAML > JSON > DEFAULT
    return merge_configs(DEFAULT_CONFIG, json_conf, yaml_conf, env_conf)

def save_json_config(config):
    """Salva configuração em JSON."""
    with open(CONFIG_JSON, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def save_yaml_config(config):
    """Salva configuração em YAML."""
    with open(CONFIG_YAML, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True)

# Configuração global pronta para uso em qualquer módulo
config = get_config()

# Função utilitária para acessar valores de configuração
def get_setting(key, default=None):
    return config.get(key, default)

# Exemplo de uso:
# url = get_setting("target_url")
# threads = get_setting("threads", 5)

# Garante que diretórios essenciais existem
for d in [OUTPUT_DIR, LOGS_DIR, REPORTS_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)