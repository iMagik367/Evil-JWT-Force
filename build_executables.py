#!/usr/bin/env python3
"""
Script para gerar executáveis do Evil-Force-JWT para Windows, Linux e macOS.
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

# Diretório do projeto
PROJECT_ROOT = Path(__file__).resolve().parent
BUILD_DIR = PROJECT_ROOT / "dist"
ICON_PATH = PROJECT_ROOT / "gui" / "assets" / "icon.ico"
SPEC_FILE = PROJECT_ROOT / "evil_jwt_force.spec"

def log(message):
    print(f"[BUILD] {message}")

def run_command(command, shell=True):
    log(f"Executando: {command}")
    result = subprocess.run(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        log(f"ERRO: {result.stderr}")
        return False
    return True

def check_dependencies():
    log("Verificando dependências...")
    try:
        import PyInstaller
        log("PyInstaller encontrado.")
    except ImportError:
        log("PyInstaller não encontrado. Instalando...")
        if not run_command("pip install pyinstaller"):
            log("Falha ao instalar PyInstaller. Abortando.")
            sys.exit(1)
    
    # Verificar se todas as dependências estão instaladas
    req_file = PROJECT_ROOT / "requirements.txt"
    if req_file.exists():
        log("Instalando dependências do requirements.txt...")
        if not run_command(f"pip install -r {req_file}"):
            log("Aviso: Algumas dependências podem não ter sido instaladas corretamente.")

def clean_build_dir():
    log("Limpando diretórios de build anteriores...")
    build_dir = PROJECT_ROOT / "build"
    dist_dir = PROJECT_ROOT / "dist"
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    if SPEC_FILE.exists():
        SPEC_FILE.unlink()

def create_windows_executable():
    log("Criando executável para Windows...")
    icon_param = f"--icon={ICON_PATH}" if ICON_PATH.exists() else ""
    
    # Usar caminhos completos para evitar problemas com paths no Windows
    gui_assets_path = str(PROJECT_ROOT / "gui" / "assets").replace("\\", "/")
    config_path = str(PROJECT_ROOT / "config").replace("\\", "/")
    
    # Usar aspas duplas em vez de simples para os caminhos no Windows
    command = f'pyinstaller --clean --name Evil_JWT_Force --windowed --onefile {icon_param} --add-data "{gui_assets_path}/*;gui/assets/" --add-data "{config_path}/*;config/" --hidden-import=tkinter --hidden-import=PIL main.py'
    
    if not run_command(command):
        log("Falha ao criar executável para Windows.")
        return False
    
    log("Executável para Windows criado com sucesso!")
    return True

def create_linux_executable():
    log("Criando executável para Linux...")
    # Usar caminhos completos para evitar problemas
    gui_assets_path = str(PROJECT_ROOT / "gui" / "assets").replace("\\", "/")
    config_path = str(PROJECT_ROOT / "config").replace("\\", "/")
    
    command = f'pyinstaller --clean --name Evil_JWT_Force --onefile --add-data "{gui_assets_path}/*:gui/assets/" --add-data "{config_path}/*:config/" --hidden-import=tkinter --hidden-import=PIL main.py'
    
    if not run_command(command):
        log("Falha ao criar executável para Linux.")
        return False
    
    log("Executável para Linux criado com sucesso!")
    return True

def create_macos_executable():
    log("Criando executável para macOS...")
    icon_param = ""
    mac_icon = PROJECT_ROOT / "gui" / "assets" / "icon.icns"
    if mac_icon.exists():
        icon_param = f"--icon={mac_icon}"
    
    # Usar caminhos completos para evitar problemas
    gui_assets_path = str(PROJECT_ROOT / "gui" / "assets").replace("\\", "/")
    config_path = str(PROJECT_ROOT / "config").replace("\\", "/")
    
    command = f'pyinstaller --clean --name Evil_JWT_Force --windowed --onefile {icon_param} --add-data "{gui_assets_path}/*:gui/assets/" --add-data "{config_path}/*:config/" --hidden-import=tkinter --hidden-import=PIL main.py'
    
    if not run_command(command):
        log("Falha ao criar executável para macOS.")
        return False
    
    log("Executável para macOS criado com sucesso!")
    return True

def create_readme_file():
    log("Criando arquivo README para os executáveis...")
    readme_content = """# Evil JWT Force - Executável

Este é o executável da ferramenta Evil JWT Force, uma suíte avançada para testes de segurança em sistemas JWT.

## Instruções de Uso

1. Execute o arquivo apropriado para seu sistema operacional:
   - Windows: Evil_JWT_Force.exe
   - Linux: Evil_JWT_Force
   - macOS: Evil_JWT_Force.app

2. A interface gráfica será iniciada automaticamente.

3. Para operação via linha de comando:
   - Windows: Evil_JWT_Force.exe --cli
   - Linux/macOS: ./Evil_JWT_Force --cli

## Requisitos

- Windows 10/11 ou mais recente
- Ubuntu 20.04/22.04 ou distribuição Linux equivalente
- macOS 11 (Big Sur) ou mais recente

## Observações

Esta ferramenta deve ser usada apenas para fins éticos e legais de teste de segurança.
"""
    
    readme_path = BUILD_DIR / "README.md"
    try:
        os.makedirs(BUILD_DIR, exist_ok=True)
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        log(f"README criado em: {readme_path}")
    except Exception as e:
        log(f"Erro ao criar README: {str(e)}")

def main():
    log("Iniciando processo de build...")
    
    # Verificar dependências
    check_dependencies()
    
    # Limpar builds anteriores
    clean_build_dir()
    
    # Detectar sistema operacional atual
    current_os = platform.system()
    
    success = False
    
    if current_os == "Windows":
        success = create_windows_executable()
    elif current_os == "Linux":
        success = create_linux_executable()
    elif current_os == "Darwin":  # macOS
        success = create_macos_executable()
    else:
        log(f"Sistema operacional não suportado: {current_os}")
        sys.exit(1)
    
    if success:
        create_readme_file()
        log(f"Build completo! Executável disponível em: {BUILD_DIR}")
    else:
        log("Falha no processo de build.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Build interrompido pelo usuário.")
        sys.exit(130)
    except Exception as e:
        log(f"Erro fatal: {e}")
        sys.exit(1) 