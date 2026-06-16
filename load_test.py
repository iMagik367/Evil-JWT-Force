import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import requests
from tqdm import tqdm

# Configuração
API_URL = "http://localhost:8000"
NUM_REQUESTS = 1000
CONCURRENT_REQUESTS = 10
TEST_TOKENS = [
    # Token válido
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    # Token com algoritmo 'none'
    "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.",
    # Token expirado
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    # Token com header injection
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJraWQiOiJodHRwOi8vZXZpbC5jb20va2V5In0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    # Token com jku injection
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJqa3UiOiJodHRwOi8vZXZpbC5jb20va2V5cyJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    # Token com x5u injection
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJ4NXUiOiJodHRwOi8vZXZpbC5jb20vY2VydCJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
]

def analyze_single_token(token: str) -> Dict:
    """Analisa um único token."""
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json={"token": token, "metadata": {"load_test": True}}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"\nErro ao analisar token: {e}")
        return {}

def analyze_batch_tokens(tokens: List[str]) -> Dict:
    """Analisa múltiplos tokens."""
    try:
        response = requests.post(
            f"{API_URL}/analyze/batch",
            json={"tokens": tokens, "metadata": {"load_test": True}}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"\nErro ao analisar tokens em lote: {e}")
        return {}

def worker():
    """Função executada por cada thread."""
    results = []
    for _ in range(NUM_REQUESTS // CONCURRENT_REQUESTS):
        # Escolhe aleatoriamente entre análise individual ou em lote
        if random.random() < 0.7:  # 70% de chance de análise individual
            token = random.choice(TEST_TOKENS)
            result = analyze_single_token(token)
        else:  # 30% de chance de análise em lote
            num_tokens = random.randint(2, 5)
            tokens = random.sample(TEST_TOKENS, num_tokens)
            result = analyze_batch_tokens(tokens)
        
        if result:
            results.append(result)
        
        # Pequeno delay para não sobrecarregar a API
        time.sleep(random.uniform(0.1, 0.5))
    
    return results

def main():
    """Função principal do teste de carga."""
    print(f"Iniciando teste de carga com {NUM_REQUESTS} requisições...")
    print(f"Requisições concorrentes: {CONCURRENT_REQUESTS}")
    
    start_time = time.time()
    all_results = []
    
    # Executa requisições concorrentes
    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(worker) for _ in range(CONCURRENT_REQUESTS)]
        
        # Coleta resultados
        for future in tqdm(futures, desc="Progresso"):
            results = future.result()
            all_results.extend(results)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Análise dos resultados
    total_requests = len(all_results)
    successful_requests = sum(1 for r in all_results if r)
    total_tokens = sum(
        r.get('total_tokens', 1) if isinstance(r, dict) and 'total_tokens' in r else 1
        for r in all_results
    )
    vulnerable_tokens = sum(
        r.get('vulnerable_tokens', 1) if isinstance(r, dict) and 'vulnerable_tokens' in r else 0
        for r in all_results
    )
    
    # Exibe estatísticas
    print("\nEstatísticas do teste de carga:")
    print(f"Tempo total: {total_time:.2f} segundos")
    print(f"Requisições por segundo: {total_requests / total_time:.2f}")
    print(f"Taxa de sucesso: {(successful_requests / total_requests) * 100:.2f}%")
    print(f"Total de tokens analisados: {total_tokens}")
    print(f"Tokens vulneráveis detectados: {vulnerable_tokens}")
    print(f"Taxa de vulnerabilidade: {(vulnerable_tokens / total_tokens) * 100:.2f}%")
    
    # Salva resultados
    with open('load_test_results.json', 'w') as f:
        json.dump({
            'total_time': total_time,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'total_tokens': total_tokens,
            'vulnerable_tokens': vulnerable_tokens,
            'results': all_results
        }, f, indent=2)
    
    print("\nResultados salvos em 'load_test_results.json'")

if __name__ == "__main__":
    main() 