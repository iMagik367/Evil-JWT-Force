import json
import time
from typing import Dict, List

import requests
from tqdm import tqdm

# Configuração
API_URL = "http://localhost:8000"
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

def test_health() -> bool:
    """Testa o endpoint de saúde da API."""
    try:
        response = requests.get(f"{API_URL}/health")
        response.raise_for_status()
        data = response.json()
        print("\nStatus da API:")
        print(f"- Status: {data['status']}")
        print(f"- Modelo carregado: {data['model_loaded']}")
        print(f"- Uptime: {data['uptime']:.2f} segundos")
        return True
    except Exception as e:
        print(f"\nErro ao verificar saúde da API: {e}")
        return False

def test_single_token(token: str) -> Dict:
    """Testa a análise de um único token."""
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json={"token": token, "metadata": {"test": True}}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"\nErro ao analisar token: {e}")
        return {}

def test_batch_tokens(tokens: List[str]) -> Dict:
    """Testa a análise de múltiplos tokens."""
    try:
        response = requests.post(
            f"{API_URL}/analyze/batch",
            json={"tokens": tokens, "metadata": {"test": True}}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"\nErro ao analisar tokens em lote: {e}")
        return {}

def main():
    """Função principal de teste."""
    print("Iniciando testes da API...")
    
    # Testa saúde da API
    if not test_health():
        print("API não está saudável. Abortando testes.")
        return
    
    # Testa análise de tokens individuais
    print("\nTestando análise de tokens individuais:")
    for token in tqdm(TEST_TOKENS):
        result = test_single_token(token)
        if result:
            print(f"\nToken: {token[:30]}...")
            print(f"- Vulnerável: {result['is_vulnerable']}")
            print(f"- Probabilidade: {result['vulnerability_probability']:.2f}")
            print(f"- Tempo de processamento: {result['processing_time']:.3f}s")
    
    # Testa análise em lote
    print("\nTestando análise em lote:")
    result = test_batch_tokens(TEST_TOKENS)
    if result:
        print(f"\nTotal de tokens: {result['total_tokens']}")
        print(f"Tokens vulneráveis: {result['vulnerable_tokens']}")
        print(f"Tempo de processamento: {result['processing_time']:.3f}s")
        
        # Exibe detalhes de cada token
        print("\nDetalhes dos tokens:")
        for r in result['results']:
            print(f"\nToken: {r['token'][:30]}...")
            print(f"- Vulnerável: {r['is_vulnerable']}")
            print(f"- Probabilidade: {r['vulnerability_probability']:.2f}")
            print(f"- Tempo de processamento: {r['processing_time']:.3f}s")

if __name__ == "__main__":
    main() 