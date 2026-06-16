"""
EVIL_JWT_FORCE Scripts Package
Scripts utilitários para tarefas específicas (.sh)
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional

SCRIPTS_DIR = Path(__file__).resolve().parent

def listar_scripts_sh() -> List[str]:
    """Lista todos os scripts .sh disponíveis na pasta scripts."""
    return [f.name for f in SCRIPTS_DIR.iterdir() if f.is_file() and f.suffix == ".sh"]

def executar_script_sh(nome_script: str, argumentos: Optional[List[str]] = None) -> int:
    """
    Executa um script .sh da pasta scripts de forma segura.
    Args:
        nome_script: Nome do arquivo .sh (ex: 'reset_logs.sh')
        argumentos: Lista de argumentos para passar ao script
    Returns:
        Código de retorno do processo (0 = sucesso)
    """
    script_path = SCRIPTS_DIR / nome_script
    if not script_path.exists() or not script_path.is_file():
        print(f"[ERRO] Script não encontrado: {nome_script}")
        return 1

    argumentos = argumentos or []
    if os.name == "nt":
        # Windows: tenta usar o WSL/bash se disponível
        bash_path = os.environ.get("WSL_BASH_PATH", "bash")
        cmd = [bash_path, str(script_path)] + argumentos
    else:
        # Linux/Mac
        cmd = ["bash", str(script_path)] + argumentos

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Falha ao executar {nome_script}: {e}")
        return e.returncode
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
        return 2

__all__ = [
    "listar_scripts_sh",
    "executar_script_sh"
]

__version__ = "1.1.0"
__author__ = "EVIL_JWT_FORCE Team"
__license__ = "MIT"