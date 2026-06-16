"""
EVIL_JWT_FORCE - Reports Package

Responsável pela manipulação e estruturação dos relatórios gerados.
Oferece utilidades para salvar, listar, buscar e remover relatórios HTML/JSON.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Union

REPORT_DIR = Path(__file__).resolve().parent

def get_report_path(filename: str = "report.html") -> str:
    """Retorna o caminho absoluto de um relatório pelo nome."""
    return str(REPORT_DIR / filename)

def list_existing_reports(exts: Optional[List[str]] = None) -> List[str]:
    """
    Lista todos os relatórios existentes no diretório de relatórios.
    Args:
        exts: Lista de extensões a filtrar (ex: ['.html', '.json'])
    Returns:
        Lista de nomes de arquivos de relatório.
    """
    exts = exts or [".html", ".json"]
    return [f.name for f in REPORT_DIR.iterdir() if f.is_file() and f.suffix in exts]

def remove_report(filename: str) -> bool:
    """
    Remove um relatório específico do diretório.
    Args:
        filename: Nome do arquivo a ser removido.
    Returns:
        True se removido com sucesso, False caso contrário.
    """
    path = REPORT_DIR / filename
    if path.exists() and path.is_file():
        path.unlink()
        return True
    return False

def save_report(content: Union[str, bytes], filename: str = "report.html", mode: str = "w") -> str:
    """
    Salva conteúdo em um arquivo de relatório.
    Args:
        content: Conteúdo a ser salvo (str ou bytes)
        filename: Nome do arquivo de relatório
        mode: Modo de escrita ('w' para texto, 'wb' para binário)
    Returns:
        Caminho absoluto do arquivo salvo
    """
    path = REPORT_DIR / filename
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        mode = "wb"
    with open(path, mode, encoding=None if "b" in mode else "utf-8") as f:
        f.write(content)
    return str(path)

def copy_report(src: str, dest: Optional[str] = None) -> str:
    """
    Copia um relatório para outro local/nome.
    Args:
        src: Nome do arquivo de origem
        dest: Nome do arquivo de destino (opcional)
    Returns:
        Caminho absoluto do novo arquivo
    """
    src_path = REPORT_DIR / src
    if not src_path.exists():
        raise FileNotFoundError(f"Relatório não encontrado: {src}")
    dest_path = REPORT_DIR / (dest or f"copy_{src}")
    shutil.copy2(src_path, dest_path)
    return str(dest_path)

__all__ = [
    "get_report_path",
    "list_existing_reports",
    "remove_report",
    "save_report",
    "copy_report"
]