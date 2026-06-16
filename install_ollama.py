#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - Instalador do Ollama
Script para baixar, instalar e configurar o Ollama para uso com Evil Force JWT.
"""

import os
import sys
import subprocess
import platform
import webbrowser
import time
import tempfile
import requests
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/ollama_install.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('OLLAMA_INSTALLER')

# Criar pasta de logs se não existir
os.makedirs('logs', exist_ok=True)

def print_header():
    """Imprime o cabeçalho do script"""
    print("\n" + "="*80)
    print(" "*25 + "INSTALADOR DO OLLAMA")
    print("="*80 + "\n")
    print("Este script irá ajudá-lo a instalar e configurar o Ollama para uso com Evil Force JWT.\n")

def download_windows_installer():
    """Baixa o instalador do Ollama para Windows"""
    print("Baixando o instalador do Ollama para Windows...")
    
    try:
        # URL de download direto
        download_url = "https://ollama.com/download/windows"
        
        # Criar pasta temporária para o download
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "ollama-installer.exe")
        
        # Baixar o instalador
        print(f"Baixando de {download_url}...")
        print(f"Salvando em {installer_path}")
        
        # Usar requests para baixar o arquivo
        response = requests.get(download_url, stream=True)
        response.raise_for_status()  # Verificar se houve erro no download
        
        # Obter tamanho total do arquivo
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        # Salvar o arquivo com barra de progresso
        with open(installer_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Mostrar progresso
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        bar_length = 30
                        filled_length = int(bar_length * downloaded // total_size)
                        bar = '█' * filled_length + '-' * (bar_length - filled_length)
                        sys.stdout.write(f'\rProgresso: |{bar}| {percent:.1f}% ({downloaded/(1024*1024):.1f}MB/{total_size/(1024*1024):.1f}MB)')
                        sys.stdout.flush()
        
        print("\n\n✅ Download concluído com sucesso!")
        
        # Verificar se o arquivo foi baixado corretamente
        if os.path.exists(installer_path) and os.path.getsize(installer_path) > 1000000:  # Pelo menos 1MB
            return installer_path
        else:
            print("❌ O arquivo baixado parece estar corrompido ou incompleto.")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao baixar o instalador: {str(e)}")
        return None

def install_windows():
    """Instala o Ollama no Windows"""
    print("\n" + "="*80)
    print("INSTALAÇÃO DO OLLAMA NO WINDOWS")
    print("="*80 + "\n")
    
    # Baixar o instalador
    installer_path = download_windows_installer()
    
    if not installer_path:
        print("\nNão foi possível baixar o instalador automaticamente.")
        print("Por favor, visite https://ollama.com/download/windows para baixar manualmente.")
        webbrowser.open("https://ollama.com/download/windows")
        return False
    
    # Instruções para o usuário
    print("\n" + "="*80)
    print("INSTRUÇÕES DE INSTALAÇÃO:")
    print("="*80)
    print("1. O instalador será aberto automaticamente.")
    print("2. Siga as instruções na tela para instalar o Ollama.")
    print("3. Após a instalação, reinicie este script para verificar.")
    print("="*80 + "\n")
    
    # Perguntar ao usuário se deseja continuar
    choice = input("Deseja executar o instalador agora? (s/n): ").lower()
    
    if choice != 's' and choice != 'sim':
        print("\nVocê pode executar o instalador manualmente mais tarde em:")
        print(installer_path)
        
        # Abrir o explorador de arquivos no local do instalador
        os.system(f'explorer /select,"{installer_path}"')
        return False
    
    # Executar o instalador
    try:
        print("\nExecutando o instalador...")
        os.startfile(installer_path)
        
        # Aguardar a conclusão da instalação
        print("\nAguarde a conclusão da instalação e pressione Enter quando terminar...")
        input()
        
        # Verificar se a instalação foi bem-sucedida
        try:
            result = subprocess.run(['where', 'ollama'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Ollama instalado com sucesso!")
                return True
            else:
                print("❌ Ollama não foi encontrado após a instalação.")
                print("Talvez seja necessário reiniciar o computador.")
                return False
        except Exception as e:
            print(f"❌ Erro ao verificar instalação: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar o instalador: {str(e)}")
        return False

def install_linux_mac():
    """Instala o Ollama no Linux ou macOS"""
    system = platform.system()
    print(f"\n" + "="*80)
    print(f"INSTALAÇÃO DO OLLAMA NO {system.upper()}")
    print("="*80 + "\n")
    
    print(f"Baixando e instalando Ollama para {system}...")
    
    # Comando de instalação
    install_cmd = 'curl -fsSL https://ollama.com/install.sh | sh'
    
    # Perguntar ao usuário se deseja continuar
    choice = input(f"O comando '{install_cmd}' será executado. Continuar? (s/n): ").lower()
    
    if choice != 's' and choice != 'sim':
        print("\nInstalação cancelada pelo usuário.")
        return False
    
    try:
        print(f"\nExecutando: {install_cmd}")
        process = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
        
        if process.returncode == 0:
            print("✅ Ollama instalado com sucesso!")
            return True
        else:
            print(f"❌ Erro ao instalar Ollama: {process.stderr}")
            print("\nPor favor, visite https://ollama.com para instruções de instalação manual.")
            return False
    except Exception as e:
        print(f"❌ Erro ao executar instalação: {str(e)}")
        return False

def check_ollama_installed():
    """Verifica se o Ollama está instalado"""
    print("Verificando se o Ollama já está instalado...")
    
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['where', 'ollama'], capture_output=True, text=True)
        else:  # Linux/macOS
            result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Ollama já está instalado em: " + result.stdout.strip())
            return True
        else:
            print("❌ Ollama não está instalado.")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar instalação do Ollama: {str(e)}")
        return False

def start_ollama_server():
    """Inicia o servidor Ollama"""
    print("\nIniciando servidor Ollama...")
    
    try:
        if os.name == 'nt':  # Windows
            # No Windows, executar em um novo processo
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:  # Linux/macOS
            # Em sistemas Unix, executar em background
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        # Esperar o servidor iniciar
        print("Aguardando o servidor iniciar...")
        for i in range(10):
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    print("✅ Servidor Ollama iniciado com sucesso!")
                    return True
            except:
                pass
                
            time.sleep(1)
            print(".", end="", flush=True)
        
        print("\n❌ Timeout ao iniciar o servidor Ollama.")
        return False
    
    except Exception as e:
        print(f"❌ Erro ao iniciar o servidor Ollama: {str(e)}")
        return False

def download_model():
    """Baixa o modelo llama3"""
    print("\n" + "="*80)
    print("DOWNLOAD DO MODELO LLAMA 3")
    print("="*80 + "\n")
    
    print("Este processo vai baixar aproximadamente 4GB de dados.")
    print("O download pode levar alguns minutos, dependendo da sua conexão.\n")
    
    choice = input("Deseja baixar o modelo llama3 agora? (s/n): ").lower()
    
    if choice != 's' and choice != 'sim':
        print("\nVocê pode baixar o modelo mais tarde através da aplicação Evil Force JWT.")
        return False
    
    print("\nIniciando download do modelo llama3...")
    
    try:
        response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": "llama3"},
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ Erro ao iniciar download: {response.text}")
            return False
        
        print("Download iniciado. Isso pode levar alguns minutos...")
        print("Mostrando progresso do download:\n")
        
        for line in response.iter_lines():
            if line:
                try:
                    data = line.decode('utf-8')
                    print(data)
                except:
                    pass
        
        print("\n✅ Modelo llama3 baixado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao baixar modelo: {str(e)}")
        return False

def main():
    """Função principal"""
    try:
        logger.info("Iniciando script de instalação do Ollama")
        print_header()
        
        # Verificar se o Ollama já está instalado
        logger.info("Verificando se o Ollama já está instalado")
        ollama_installed = check_ollama_installed()
        
        # Se não estiver instalado, instalar
        if not ollama_installed:
            system = platform.system()
            logger.info(f"Ollama não está instalado. Sistema operacional: {system}")
            
            if system == "Windows":
                ollama_installed = install_windows()
            elif system in ["Linux", "Darwin"]:  # Linux ou macOS
                ollama_installed = install_linux_mac()
            else:
                logger.error(f"Sistema operacional não suportado: {system}")
                print(f"❌ Sistema operacional não suportado: {system}")
                return
        else:
            logger.info("Ollama já está instalado")
        
        # Se a instalação falhou, sair
        if not ollama_installed:
            logger.error("A instalação do Ollama não foi concluída")
            print("\nA instalação do Ollama não foi concluída. Por favor, tente novamente mais tarde.")
            return
        
        # Iniciar o servidor Ollama
        logger.info("Iniciando servidor Ollama")
        server_running = start_ollama_server()
        
        if not server_running:
            logger.error("Não foi possível iniciar o servidor Ollama")
            print("\nNão foi possível iniciar o servidor Ollama.")
            print("Por favor, inicie-o manualmente e tente novamente.")
            return
        
        # Baixar o modelo
        logger.info("Verificando/baixando o modelo llama3")
        download_model()
        
        logger.info("Instalação concluída com sucesso")
        print("\n" + "="*80)
        print("INSTALAÇÃO CONCLUÍDA")
        print("="*80)
        print("O Ollama foi instalado e configurado com sucesso!")
        print("Agora você pode usar o Evil Force JWT com recursos avançados de IA.")
        print("\nObrigado por usar Evil Force JWT!")
    except Exception as e:
        logger.error(f"Erro não tratado: {str(e)}")
        print(f"❌ Ocorreu um erro inesperado: {str(e)}")
        print("Por favor, verifique o arquivo logs/ollama_install.log para mais detalhes.")

if __name__ == "__main__":
    main() 