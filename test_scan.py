#!/usr/bin/env python3
"""
Script de teste para verificar o funcionamento do módulo de escaneamento.
"""

import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('TEST_SCAN')

# Adicionar o diretório raiz ao path para importações relativas
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def test_scan():
    """Testa o escaneamento de um site"""
    try:
        from modules.scan_target import TargetScanner
        
        # URL de teste
        url = "https://example.com"
        print(f"Escaneando {url}...")
        
        # Criar scanner e executar escaneamento
        scanner = TargetScanner(url)
        results = scanner.scan()
        
        # Exibir resultados
        print("\n===== RESULTADOS DO ESCANEAMENTO =====\n")
        
        if results.get('error'):
            print(f"ERRO: {results['error']}")
            return False
        
        # Exibir endpoints
        print(f"Endpoints detectados ({len(results.get('endpoints', []))}):")
        for endpoint in results.get('endpoints', []):
            print(f"  • {endpoint}")
        
        # Exibir tokens
        tokens = results.get('tokens', [])
        jwt_cookies = results.get('jwt_cookies', [])
        print(f"\nTokens JWT encontrados: {len(tokens)}")
        print(f"Cookies JWT encontrados: {len(jwt_cookies)}")
        
        # Exibir vulnerabilidades
        vulnerabilities = results.get('vulnerabilities', [])
        print(f"\nVulnerabilidades encontradas: {len(vulnerabilities)}")
        for vuln in vulnerabilities:
            print(f"  • {vuln.get('type')}: {vuln.get('description')}")
        
        print("\n✅ Teste de escaneamento concluído com sucesso!")
        return True
    except Exception as e:
        print(f"\n❌ Erro durante o teste de escaneamento: {e}")
        return False

if __name__ == "__main__":
    print("\n===== TESTE DO MÓDULO DE ESCANEAMENTO =====\n")
    test_scan() 