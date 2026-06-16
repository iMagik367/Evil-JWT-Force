#!/usr/bin/env python3
"""
Script de teste para verificar se os módulos do Evil Force JWT estão funcionando corretamente.
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('TEST_MODULES')

# Adicionar o diretório raiz ao path para importações relativas
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def test_jwt_utils_simple():
    """Testa as funções básicas de jwt_utils_simple"""
    try:
        from modules.jwt_utils_simple import generate_token, decode_token_parts, is_jwt
        
        # Gerar um token de teste
        payload = {
            "sub": "1234567890",
            "name": "Test User",
            "admin": True
        }
        token = generate_token(payload, 'test_secret', 'HS256')
        
        print(f"Token gerado: {token}")
        
        # Verificar se é um JWT válido
        if not is_jwt(token):
            print("ERRO: O token gerado não é um JWT válido!")
            return False
        
        # Decodificar o token
        parts = decode_token_parts(token)
        if not parts or "error" in parts:
            print(f"ERRO: Falha ao decodificar o token: {parts.get('error', 'Erro desconhecido')}")
            return False
        
        print(f"Header: {parts['header']}")
        print(f"Payload: {parts['payload']}")
        print("✅ Teste de jwt_utils_simple passou com sucesso!")
        return True
    except ImportError as e:
        print(f"ERRO: Módulo jwt_utils_simple não encontrado: {e}")
        return False
    except Exception as e:
        print(f"ERRO: Falha no teste de jwt_utils_simple: {e}")
        return False

def test_jwt_decrypt():
    """Testa a classe JWTDecrypt"""
    try:
        from modules.jwt_decrypt import JWTDecrypt
        from modules.jwt_utils_simple import generate_token
        
        # Gerar um token de teste
        payload = {
            "sub": "1234567890",
            "name": "Test User",
            "admin": True
        }
        secret = "test_secret"
        token = generate_token(payload, secret, 'HS256')
        
        # Criar instância do JWTDecrypt
        decryptor = JWTDecrypt()
        
        # Testar parse_token
        parsed = decryptor.parse_token(token)
        if not parsed.get('valid', False):
            print(f"ERRO: Falha ao analisar o token: {parsed.get('error', 'Erro desconhecido')}")
            return False
        
        # Testar decrypt_token
        decrypted = decryptor.decrypt_token(token, secret)
        if not decrypted.get('success', False):
            print(f"ERRO: Falha ao decriptar o token: {decrypted.get('error', 'Erro desconhecido')}")
            return False
        
        print(f"Token decriptado: {decrypted['decoded']}")
        print("✅ Teste de JWTDecrypt passou com sucesso!")
        return True
    except ImportError as e:
        print(f"ERRO: Módulo jwt_decrypt não encontrado: {e}")
        return False
    except Exception as e:
        print(f"ERRO: Falha no teste de JWTDecrypt: {e}")
        return False

def test_token_bruteforce():
    """Testa a classe TokenBruteforcer"""
    try:
        from modules.token_bruteforce import TokenBruteforcer
        from modules.jwt_utils_simple import generate_token
        import tempfile
        
        # Gerar um token de teste
        payload = {
            "sub": "1234567890",
            "name": "Test User",
            "admin": True
        }
        secret = "test_secret"
        token = generate_token(payload, secret, 'HS256')
        
        # Criar uma wordlist temporária
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("wrong_secret1\n")
            f.write("wrong_secret2\n")
            f.write("test_secret\n")  # Segredo correto
            f.write("wrong_secret3\n")
            wordlist_path = f.name
        
        # Criar instância do TokenBruteforcer
        bruteforcer = TokenBruteforcer(token)
        
        # Testar bruteforce
        result = bruteforcer.bruteforce_with_timeout(wordlist_path, timeout=10)
        
        # Limpar arquivo temporário
        os.unlink(wordlist_path)
        
        if not result.get('success', False):
            print(f"ERRO: Falha no bruteforce: {result.get('error', 'Erro desconhecido')}")
            return False
        
        print(f"Segredo encontrado: {result['secret']}")
        print(f"Testados {result['tested']} segredos em {result['time']:.2f} segundos")
        print("✅ Teste de TokenBruteforcer passou com sucesso!")
        return True
    except ImportError as e:
        print(f"ERRO: Módulo token_bruteforce não encontrado: {e}")
        return False
    except Exception as e:
        print(f"ERRO: Falha no teste de TokenBruteforcer: {e}")
        return False

def test_all():
    """Executa todos os testes"""
    print("\n===== TESTE DE MÓDULOS DO EVIL FORCE JWT =====\n")
    
    # Verificar dependências
    try:
        from modules import check_dependencies
        dependencies = check_dependencies()
        missing = [dep for dep, installed in dependencies.items() if not installed]
        if missing:
            print(f"AVISO: As seguintes dependências estão faltando: {', '.join(missing)}")
            print("Alguns testes podem falhar. Instale as dependências com 'pip install -r requirements.txt'")
    except ImportError:
        print("AVISO: Não foi possível verificar dependências")
    
    # Executar testes
    results = {
        "jwt_utils_simple": test_jwt_utils_simple(),
        "jwt_decrypt": test_jwt_decrypt(),
        "token_bruteforce": test_token_bruteforce()
    }
    
    # Mostrar resultados
    print("\n===== RESULTADOS DOS TESTES =====\n")
    for module, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{module}: {status}")
    
    # Verificar se todos os testes passaram
    if all(results.values()):
        print("\n✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
        return 0
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        return 1

if __name__ == "__main__":
    sys.exit(test_all()) 