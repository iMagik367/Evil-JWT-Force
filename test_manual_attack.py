#!/usr/bin/env python3
"""
Script de teste para verificar o funcionamento do módulo de ataque manual.
"""

import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('TEST_MANUAL_ATTACK')

# Adicionar o diretório raiz ao path para importações relativas
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def test_bruteforce():
    """Testa o ataque de força bruta"""
    try:
        from modules.token_bruteforce import TokenBruteforcer
        
        # Token de teste (com senha "test")
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.XbPfbIHMI6arZ3Y922BhjWgQzWXcXNrz0ogtVhfEd2o"
        
        # Criar wordlist temporária
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("password\n")
            f.write("123456\n")
            f.write("test\n")  # Senha correta
            f.write("admin\n")
            wordlist_path = f.name
        
        print(f"Testando ataque de força bruta com token: {token[:20]}...")
        
        # Criar bruteforcer e executar ataque
        bruteforcer = TokenBruteforcer(token)
        result = bruteforcer.bruteforce_with_timeout(wordlist_path, timeout=10)
        
        # Exibir resultados
        print("\n===== RESULTADOS DO ATAQUE DE FORÇA BRUTA =====\n")
        
        if result.get('success'):
            print(f"✅ Senha encontrada: {result.get('secret')}")
            print(f"Testados {result.get('tested')} segredos em {result.get('time'):.2f} segundos")
            print(f"Taxa: {result.get('rate'):.2f} senhas/segundo")
        else:
            print(f"❌ Falha ao encontrar senha: {result.get('error', 'Senha não encontrada')}")
            print(f"Testados {result.get('tested')} segredos em {result.get('time'):.2f} segundos")
        
        # Limpar arquivo temporário
        import os
        os.unlink(wordlist_path)
        
        return result.get('success', False)
    except Exception as e:
        print(f"\n❌ Erro durante o teste de força bruta: {e}")
        return False

def test_algorithm_confusion():
    """Testa o ataque de confusão de algoritmo"""
    try:
        from modules.jwt_decrypt import JWTDecrypt
        
        # Token de teste vulnerável a confusão de algoritmo
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.XbPfbIHMI6arZ3Y922BhjWgQzWXcXNrz0ogtVhfEd2o"
        
        print(f"Testando ataque de confusão de algoritmo com token: {token[:20]}...")
        
        # Criar decryptor e verificar vulnerabilidade
        decryptor = JWTDecrypt()
        result = decryptor.check_key_confusion(token)
        
        # Exibir resultados
        print("\n===== RESULTADOS DO ATAQUE DE CONFUSÃO DE ALGORITMO =====\n")
        
        if result.get('vulnerable'):
            print(f"✅ Token é vulnerável a confusão de algoritmo!")
            for variant in result.get('results', []):
                if variant.get('vulnerable'):
                    print(f"  • Variante: {variant.get('variant')}")
                    print(f"  • Token modificado: {variant.get('modified_token')[:30]}...")
        else:
            print(f"❌ Token não é vulnerável a confusão de algoritmo")
            if result.get('message'):
                print(f"  • {result.get('message')}")
        
        return result.get('vulnerable', False)
    except Exception as e:
        print(f"\n❌ Erro durante o teste de confusão de algoritmo: {e}")
        return False

def test_none_algorithm():
    """Testa o ataque de algoritmo none"""
    try:
        from modules.jwt_decrypt import JWTDecrypt
        
        # Token de teste
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.XbPfbIHMI6arZ3Y922BhjWgQzWXcXNrz0ogtVhfEd2o"
        
        print(f"Testando ataque de algoritmo none com token: {token[:20]}...")
        
        # Criar decryptor e verificar vulnerabilidade
        decryptor = JWTDecrypt()
        result = decryptor.check_none_algorithm(token)
        
        # Exibir resultados
        print("\n===== RESULTADOS DO ATAQUE DE ALGORITMO NONE =====\n")
        
        if result.get('vulnerable'):
            print(f"✅ Token é vulnerável a algoritmo none!")
            for variant in result.get('results', []):
                if variant.get('vulnerable'):
                    print(f"  • Variante: {variant.get('variant')}")
                    print(f"  • Token modificado: {variant.get('modified_token')[:30]}...")
        else:
            print(f"❌ Token não é vulnerável a algoritmo none")
        
        return result.get('vulnerable', False)
    except Exception as e:
        print(f"\n❌ Erro durante o teste de algoritmo none: {e}")
        return False

if __name__ == "__main__":
    print("\n===== TESTE DOS MÓDULOS DE ATAQUE MANUAL =====\n")
    
    bruteforce_success = test_bruteforce()
    print("\n" + "-" * 50 + "\n")
    
    algorithm_confusion_success = test_algorithm_confusion()
    print("\n" + "-" * 50 + "\n")
    
    none_algorithm_success = test_none_algorithm()
    
    print("\n===== RESUMO DOS TESTES =====\n")
    print(f"Ataque de força bruta: {'✅ Sucesso' if bruteforce_success else '❌ Falha'}")
    print(f"Ataque de confusão de algoritmo: {'✅ Sucesso' if algorithm_confusion_success else '❌ Falha'}")
    print(f"Ataque de algoritmo none: {'✅ Sucesso' if none_algorithm_success else '❌ Falha'}")
    
    if bruteforce_success or algorithm_confusion_success or none_algorithm_success:
        print("\n✅ Pelo menos um módulo de ataque funcionou corretamente!")
    else:
        print("\n❌ Todos os módulos de ataque falharam!") 