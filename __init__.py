import os
import sys
import importlib
from pathlib import Path

# Diretório raiz do projeto
PROJECT_ROOT = Path(__file__).parent.resolve()

# Pastas relevantes para o PYTHONPATH
SUBDIRS = ["core", "utils", "modules", "config", "scripts", "external/theHarvester"]

# Adiciona cada subdiretório ao sys.path se ainda não estiver presente
for subdir in SUBDIRS:
    subdir_path = PROJECT_ROOT / subdir
    if subdir_path.exists() and str(subdir_path) not in sys.path:
        sys.path.insert(0, str(subdir_path))

# Adiciona o próprio diretório raiz ao sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Importação dinâmica de todos os módulos Python em cada subdiretório relevante
def import_all_modules_from_subdirs(subdirs):
    for subdir in subdirs:
        dir_path = PROJECT_ROOT / subdir
        if not dir_path.exists():
            continue
        for file in dir_path.glob("*.py"):
            if file.name.startswith("_"):
                continue  # Ignora arquivos __init__.py e privados
            module_name = f"{subdir}.{file.stem}"
            try:
                importlib.import_module(module_name)
            except Exception as e:
                # Loga o erro, mas não interrompe a inicialização do pacote
                print(f"[EVIL_JWT_FORCE][WARN] Falha ao importar {module_name}: {e}")

import_all_modules_from_subdirs(SUBDIRS)

# Exporte explícito dos principais subpacotes para facilitar importações externas
__all__ = SUBDIRS

# Opcional: Exporte helpers globais para facilitar importação direta
try:
    from utils.helpers import *
except Exception:
    pass

# Opcional: Setup de logging global para o pacote
try:
    from utils.logger import setup_logger
    logger = setup_logger("EVIL_JWT_FORCE")
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("EVIL_JWT_FORCE_Fallback")

logger.info("Pacote EVIL_JWT_FORCE inicializado com sucesso.")