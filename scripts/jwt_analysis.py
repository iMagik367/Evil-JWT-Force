#!/usr/bin/env python3
"""
Script de análise completa de JWT usando todas as ferramentas disponíveis
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Importa componentes necessários
try:
    from modules.jwt_tools_integrator import JWTToolsIntegrator
    from utils.logger import setup_logger
    from utils.helpers import save_to_file
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de estar executando este script a partir do diretório raiz do projeto.")
    sys.exit(1)

# Configuração de logging
logger = setup_logger("EVIL_JWT_FORCE.jwt_analysis")

def banner():
    """Exibe o banner do programa"""
    print("""
 ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
 ┃ ███████╗██╗   ██╗██╗██╗           ██╗██╗    ██╗████████╗ ┃
 ┃ ██╔════╝██║   ██║██║██║           ██║██║    ██║╚══██╔══╝ ┃
 ┃ █████╗  ██║   ██║██║██║     █████╗██║██║ █╗ ██║   ██║    ┃
 ┃ ██╔══╝  ╚██╗ ██╔╝██║██║     ╚════╝██║██║███╗██║   ██║    ┃
 ┃ ███████╗ ╚████╔╝ ██║███████╗     ██╔╝╚███╔███╔╝   ██║    ┃
 ┃ ╚══════╝  ╚═══╝  ╚═╝╚══════╝     ╚═╝  ╚══╝╚══╝    ╚═╝    ┃
 ┃                                                           ┃
 ┃       EVIL-JWT-FORCE - Multi-tool JWT Analysis           ┃
 ┃                    versão 2.0                            ┃
 ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    """)

def parse_args():
    """Analisa os argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description="Análise e cracking avançado de JWT usando múltiplas ferramentas"
    )
    parser.add_argument("-t", "--token", help="Token JWT para analisar")
    parser.add_argument("-f", "--token-file", help="Arquivo contendo o token JWT")
    parser.add_argument("-w", "--wordlist", help="Caminho para a wordlist")
    parser.add_argument("-o", "--output", help="Arquivo de saída para os resultados")
    parser.add_argument("--crack", action="store_true", help="Tentar quebrar o token")
    parser.add_argument("--analyze", action="store_true", help="Analisar o token")
    parser.add_argument("--bruteforce", action="store_true", help="Usar força bruta para quebrar o token")
    parser.add_argument("--tools", nargs="+", help="Ferramentas específicas a serem utilizadas")
    parser.add_argument("--list-tools", action="store_true", help="Listar todas as ferramentas disponíveis")
    parser.add_argument("--setup", action="store_true", help="Configurar as ferramentas JWT")
    
    return parser.parse_args()

def list_available_tools():
    """Lista todas as ferramentas disponíveis"""
    from modules.jwt_tools_integrator import TOOLS, check_tools_availability
    
    print("\n=== Ferramentas JWT Suportadas ===\n")
    
    available = check_tools_availability()
    
    for name, info in TOOLS.items():
        status = "✅ Disponível" if available.get(name, False) else "❌ Não disponível"
        print(f"{name.ljust(25)} - {info['description']} [{status}]")
    
    print("\nPara instalar as ferramentas ausentes, execute: python scripts/setup_jwt_tools.py")
    print("Ou use a opção --setup neste script.\n")

def setup_tools():
    """Configura as ferramentas JWT"""
    try:
        print("Configurando ferramentas JWT...")
        setup_script = Path(__file__).resolve().parent / "setup_jwt_tools.py"
        
        if not setup_script.exists():
            print("Erro: Script de configuração não encontrado.")
            return False
        
        import subprocess
        result = subprocess.run([sys.executable, str(setup_script)], check=True)
        
        if result.returncode == 0:
            print("Ferramentas configuradas com sucesso!")
            return True
        else:
            print("Erro ao configurar ferramentas.")
            return False
    
    except Exception as e:
        print(f"Erro durante a configuração: {e}")
        return False

def get_token(args):
    """Obtém o token JWT das opções fornecidas"""
    token = None
    
    if args.token:
        token = args.token
    elif args.token_file:
        try:
            with open(args.token_file, 'r') as f:
                token = f.read().strip()
        except Exception as e:
            logger.error(f"Erro ao ler arquivo de token: {e}")
            sys.exit(1)
    else:
        token = input("Digite o token JWT: ").strip()
    
    if not token:
        logger.error("Token JWT não fornecido.")
        sys.exit(1)
    
    return token

def analyze_token(token, wordlist=None, specific_tools=None):
    """Analisa um token JWT"""
    integrator = JWTToolsIntegrator(token, wordlist)
    
    if specific_tools:
        logger.info(f"Analisando token com ferramentas específicas: {specific_tools}")
        results = integrator.run_specific_tools(specific_tools)
    else:
        logger.info("Analisando token com todas as ferramentas disponíveis...")
        results = integrator.run_all_tools()
    
    combined_results = integrator.get_combined_results()
    
    return combined_results

def crack_token(token, wordlist):
    """Tenta quebrar um token JWT"""
    integrator = JWTToolsIntegrator(token, wordlist)
    logger.info(f"Tentando quebrar token com wordlist: {wordlist}")
    
    if not wordlist:
        logger.error("Wordlist não especificada para cracking.")
        return {"error": "Wordlist não especificada"}
    
    results = integrator.crack_token(wordlist)
    
    return results

def display_results(results):
    """Exibe os resultados da análise/cracking"""
    print("\n" + "="*60)
    print(" RESULTADOS DA ANÁLISE ".center(60, "="))
    print("="*60 + "\n")
    
    # Informações básicas
    print(f"Token analisado: {results.get('token', 'N/A')[:30]}...\n")
    
    # Vulnerabilidades encontradas
    vulnerabilities = results.get("vulnerabilities", [])
    if vulnerabilities:
        print("VULNERABILIDADES ENCONTRADAS:")
        for vuln in vulnerabilities:
            print(f"  - {vuln}")
    else:
        print("Nenhuma vulnerabilidade encontrada.")
    
    # Possíveis segredos
    secrets = results.get("possible_secrets", [])
    if secrets:
        print("\nPOSSÍVEIS SEGREDOS:")
        for secret in secrets:
            if isinstance(secret, dict):
                print(f"  - {secret.get('secret')} (via {secret.get('tool')})")
            else:
                print(f"  - {secret}")
    else:
        print("\nNenhum segredo encontrado.")
    
    # Findings
    findings = results.get("findings", [])
    if findings:
        print("\nDESCOBERTAS:")
        for finding in findings:
            if isinstance(finding, dict):
                print(f"  - {finding.get('finding')} (via {finding.get('tool')})")
            else:
                print(f"  - {finding}")
    
    # Recomendações
    recommendations = results.get("recommendations", [])
    if recommendations:
        print("\nRECOMENDAÇÕES:")
        for rec in recommendations:
            print(f"  - {rec}")
    
    print("\n" + "="*60)

def main():
    """Função principal"""
    args = parse_args()
    
    # Exibe banner
    banner()
    
    # Lista ferramentas disponíveis
    if args.list_tools:
        list_available_tools()
        return 0
    
    # Configura ferramentas
    if args.setup:
        if setup_tools():
            print("Ferramentas configuradas com sucesso!")
        else:
            print("Falha na configuração das ferramentas.")
        return 0
    
    # Obtém o token
    token = None
    if not (args.list_tools or args.setup):
        token = get_token(args)
    
    # Define o arquivo de saída padrão
    output_file = args.output or "output/jwt_analysis_results.json"
    
    # Modos de execução
    if args.crack or args.bruteforce:
        if not args.wordlist:
            args.wordlist = input("Digite o caminho para a wordlist: ")
        
        results = crack_token(token, args.wordlist)
        display_results(results)
        
        # Salva resultados
        if output_file:
            try:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                print(f"Resultados salvos em: {output_file}")
            except Exception as e:
                logger.error(f"Erro ao salvar resultados: {e}")
    
    elif args.analyze or not (args.crack or args.bruteforce or args.list_tools or args.setup):
        # Se nenhum modo especificado, assume análise
        results = analyze_token(token, args.wordlist, args.tools)
        display_results(results)
        
        # Salva resultados
        if output_file:
            try:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                print(f"Resultados salvos em: {output_file}")
            except Exception as e:
                logger.error(f"Erro ao salvar resultados: {e}")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1) 