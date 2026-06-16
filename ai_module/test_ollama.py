#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - Teste de Ollama
Script para verificar a instalação do Ollama e auxiliar o usuário a configurá-lo.
"""

import os
import subprocess
import webbrowser
import platform
import sys
import tempfile
import requests
import time

def print_header():
    """Imprime o cabeçalho do script"""
    print("\n" + "="*80)
    print(" "*30 + "TESTE DE OLLAMA")
    print("="*80 + "\n")
    print("Este script verifica a instalação do Ollama e ajuda a configurá-lo para uso com Evil Force JWT.\n")

def check_ollama_installed():
    """Verifica se o Ollama está instalado"""
    print("Verificando se o Ollama está instalado...")
    
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['where', 'ollama'], capture_output=True, text=True)
        else:  # Linux/macOS
            result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Ollama encontrado em: " + result.stdout.strip())
            return True
        else:
            print("❌ Ollama não está instalado.")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar instalação do Ollama: {str(e)}")
        return False

def check_ollama_running():
    """Verifica se o servidor Ollama está rodando"""
    print("\nVerificando se o servidor Ollama está rodando...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✅ Servidor Ollama está rodando.")
            return True
        else:
            print(f"❌ Servidor Ollama retornou código de erro: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Servidor Ollama não está rodando ou não está acessível.")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar se o servidor Ollama está rodando: {str(e)}")
        return False

def download_ollama():
    """Baixa o Ollama e guia o usuário pela instalação"""
    print("\n" + "="*80)
    print("DOWNLOAD E INSTALAÇÃO DO OLLAMA")
    print("="*80 + "\n")
    
    system = platform.system()
    
    if system == "Windows":
        print("Baixando o instalador do Ollama para Windows...")
        url = "https://ollama.com/download/windows"
        
        try:
            # Abrir página de download
            print("Abrindo página de download do Ollama...")
            webbrowser.open(url)
            
            print("\n" + "="*80)
            print("INSTRUÇÕES DE INSTALAÇÃO:")
            print("="*80)
            print("1. Baixe o instalador do site que foi aberto.")
            print("2. Execute o instalador e siga as instruções.")
            print("3. Após a instalação, reinicie este script para verificar.")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"❌ Erro ao abrir página de download: {str(e)}")
            print(f"Por favor, visite manualmente: {url}")
    
    elif system == "Darwin":  # macOS
        print("Baixando e instalando Ollama para macOS...")
        cmd = 'curl -fsSL https://ollama.com/install.sh | sh'
        
        try:
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if process.returncode == 0:
                print("✅ Ollama instalado com sucesso!")
            else:
                print(f"❌ Erro ao instalar Ollama: {process.stderr}")
                print("\nPor favor, visite https://ollama.com para instruções de instalação manual.")
        except Exception as e:
            print(f"❌ Erro ao executar instalação: {str(e)}")
    
    elif system == "Linux":
        print("Baixando e instalando Ollama para Linux...")
        cmd = 'curl -fsSL https://ollama.com/install.sh | sh'
        
        try:
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if process.returncode == 0:
                print("✅ Ollama instalado com sucesso!")
            else:
                print(f"❌ Erro ao instalar Ollama: {process.stderr}")
                print("\nPor favor, visite https://ollama.com para instruções de instalação manual.")
        except Exception as e:
            print(f"❌ Erro ao executar instalação: {str(e)}")
    
    else:
        print(f"Sistema operacional não reconhecido: {system}")
        print("Por favor, visite https://ollama.com para instruções de instalação manual.")

def start_ollama_server():
    """Inicia o servidor Ollama"""
    print("\nIniciando servidor Ollama...")
    
    try:
        if os.name == 'nt':  # Windows
            # No Windows, executar em um novo processo sem janela
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
            if check_ollama_running():
                return True
            time.sleep(1)
            print(".", end="", flush=True)
        
        print("\n❌ Timeout ao iniciar o servidor Ollama.")
        return False
    
    except Exception as e:
        print(f"❌ Erro ao iniciar o servidor Ollama: {str(e)}")
        return False

def check_llama_model():
    """Verifica se o modelo Llama está disponível"""
    print("\nVerificando se o modelo Llama está disponível...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            if "llama3:latest" in model_names:
                print("✅ Modelo llama3 já está disponível.")
                return True
            else:
                print("❌ Modelo llama3 não encontrado.")
                print("Modelos disponíveis:", model_names)
                return False
        else:
            print(f"❌ Erro ao verificar modelos: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar modelos: {str(e)}")
        return False

def download_llama_model():
    """Baixa o modelo Llama"""
    print("\n" + "="*80)
    print("DOWNLOAD DO MODELO LLAMA 3")
    print("="*80 + "\n")
    
    print("Este processo vai baixar aproximadamente 4GB de dados.")
    print("O download será feito em background quando você usar a aplicação.")
    print("Alternativamente, você pode iniciar o download agora.\n")
    
    choice = input("Deseja iniciar o download agora? (s/n): ").lower()
    
    if choice != 's' and choice != 'sim':
        print("\nO download será iniciado automaticamente quando você usar a aplicação.")
        return
    
    print("\nIniciando download do modelo llama3...")
    
    try:
        response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": "llama3"},
            stream=True
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    print(line.decode('utf-8'))
            print("\n✅ Modelo llama3 baixado com sucesso!")
        else:
            print(f"❌ Erro ao baixar modelo: {response.text}")
    except Exception as e:
        print(f"❌ Erro ao baixar modelo: {str(e)}")

def test_ollama_response():
    """Testa a resposta do Ollama com uma pergunta simples"""
    print("\n" + "="*80)
    print("TESTE DE RESPOSTA")
    print("="*80 + "\n")
    
    print("Enviando uma pergunta de teste para o Ollama...\n")
    
    try:
        # Mensagens para o teste
        messages = [
            {"role": "system", "content": "Você é um assistente útil e conciso."},
            {"role": "user", "content": "O que é um token JWT e para que serve?"}
        ]
        
        # Enviar requisição
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3",
                "messages": messages,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if "message" in result and "content" in result["message"]:
                answer = result["message"]["content"]
                print("Pergunta: O que é um token JWT e para que serve?")
                print("\nResposta do Ollama:")
                print("-"*40)
                print(answer)
                print("-"*40)
                print("\n✅ Teste concluído com sucesso!")
                return True
            else:
                print("❌ Resposta do Ollama não contém o campo 'message.content'")
                return False
        else:
            print(f"❌ Erro na requisição: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar resposta: {str(e)}")
        return False

def main():
    """Função principal"""
    print_header()
    
    # Verificar se o Ollama está instalado
    ollama_installed = check_ollama_installed()
    if not ollama_installed:
        download_ollama()
        print("\nPor favor, reinicie este script após instalar o Ollama.")
        return
    
    # Verificar se o servidor Ollama está rodando
    ollama_running = check_ollama_running()
    if not ollama_running:
        success = start_ollama_server()
        if not success:
            print("\nPor favor, inicie o servidor Ollama manualmente e tente novamente.")
            if os.name == 'nt':  # Windows
                print("No Windows, procure por 'Ollama' no menu Iniciar.")
            else:  # Linux/macOS
                print("Em Linux/macOS, execute 'ollama serve' em um terminal.")
            return
    
    # Verificar se o modelo está disponível
    model_available = check_llama_model()
    if not model_available:
        download_llama_model()
    
    # Testar resposta do Ollama
    if model_available or input("\nDeseja testar a resposta mesmo sem o modelo? (s/n): ").lower() in ['s', 'sim']:
        test_ollama_response()
    
    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print(f"Ollama instalado: {'✅ Sim' if ollama_installed else '❌ Não'}")
    print(f"Servidor rodando: {'✅ Sim' if check_ollama_running() else '❌ Não'}")
    print(f"Modelo disponível: {'✅ Sim' if check_llama_model() else '❌ Não'}")
    print("="*80)
    
    print("\nSe todos os itens estiverem marcados com ✅, o Ollama está pronto para uso com Evil Force JWT!")
    print("Caso contrário, resolva os problemas indicados e execute este script novamente.")
    print("\nObrigado por usar Evil Force JWT!")

if __name__ == "__main__":
    main() 