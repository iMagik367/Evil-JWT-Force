#!/usr/bin/env python3
"""
Script para verificar e instalar as dependências necessárias para o Evil Force JWT.
"""

import os
import sys
import subprocess
import importlib
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('CHECK_DEPENDENCIES')

# Lista de dependências necessárias
DEPENDENCIES = {
    "jwt": "PyJWT",
    "requests": "requests",
    "cryptography": "cryptography",
    "pillow": "Pillow",
    "termcolor": "termcolor"
}

def check_dependency(module_name):
    """Verifica se um módulo está instalado"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def install_dependency(package_name):
    """Instala uma dependência usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao instalar {package_name}: {e}")
        return False

def check_and_install_dependencies():
    """Verifica e instala todas as dependências necessárias"""
    print("\n===== VERIFICAÇÃO DE DEPENDÊNCIAS =====\n")
    
    missing_deps = []
    for module_name, package_name in DEPENDENCIES.items():
        if check_dependency(module_name):
            print(f"✅ {module_name} está instalado")
        else:
            print(f"❌ {module_name} não está instalado")
            missing_deps.append((module_name, package_name))
    
    if not missing_deps:
        print("\n✅ Todas as dependências estão instaladas!")
        return True
    
    print("\n===== INSTALAÇÃO DE DEPENDÊNCIAS =====\n")
    
    for module_name, package_name in missing_deps:
        print(f"Instalando {package_name}...")
        if install_dependency(package_name):
            print(f"✅ {package_name} instalado com sucesso")
        else:
            print(f"❌ Falha ao instalar {package_name}")
            return False
    
    print("\n✅ Todas as dependências foram instaladas com sucesso!")
    return True

def create_logs_directory():
    """Cria o diretório de logs se não existir"""
    try:
        os.makedirs("logs", exist_ok=True)
        print("✅ Diretório de logs criado/verificado")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar diretório de logs: {e}")
        print(f"❌ Erro ao criar diretório de logs: {e}")
        return False

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    major, minor = sys.version_info[:2]
    if major >= 3 and minor >= 6:
        print(f"✅ Versão do Python {major}.{minor} é compatível")
        return True
    else:
        print(f"❌ Versão do Python {major}.{minor} não é compatível. É necessário Python 3.6 ou superior.")
        return False

if __name__ == "__main__":
    print("Verificando ambiente para o Evil Force JWT...")
    
    if not check_python_version():
        print("\n❌ Por favor, atualize o Python para a versão 3.6 ou superior.")
        sys.exit(1)
    
    if not create_logs_directory():
        print("\n❌ Não foi possível criar o diretório de logs.")
        sys.exit(1)
    
    if check_and_install_dependencies():
        print("\n===== AMBIENTE CONFIGURADO COM SUCESSO =====")
        print("\nAgora você pode executar o Evil Force JWT com:")
        print("  python gui/interface.py")
        print("\nOu aplicar as correções à interface de IA com:")
        print("  python gui/ai_interface_fix.py")
        sys.exit(0)
    else:
        print("\n❌ Falha ao configurar o ambiente. Verifique os erros acima.")
        sys.exit(1) 