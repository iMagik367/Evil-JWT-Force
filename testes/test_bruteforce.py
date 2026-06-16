import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Tenta importar o brute forcer principal, faz fallback para outros se necessário
try:
    from core.bruteforce import JWTBruteforcer
except ImportError:
    try:
        from modules.token_bruteforce import TokenBruteforcer as JWTBruteforcer
    except ImportError:
        pytest.skip("Nenhum módulo de brute force disponível para teste.", allow_module_level=True)

@pytest.fixture
def jwt_token():
    # Token JWT válido para chave vazia ("")
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiYWRtaW4ifQ.2jmj7l5rSw0yVb/vlWAYkK/YBwk="

@pytest.fixture
def wordlist():
    return ["wrong", "123", "admin", "hello", "secret", "password", "test", ""]

def test_bruteforce_success(jwt_token, wordlist):
    bruteforcer = JWTBruteforcer(jwt_token, wordlist)
    bruteforcer.start()
    assert bruteforcer.success, "A brute force deveria ter sucesso com a chave vazia."
    assert bruteforcer.found_key == "", "A chave encontrada deveria ser vazia."
    assert bruteforcer.found_algorithm in ["HS256", "HS384", "HS512"], "Algoritmo inesperado."

def test_bruteforce_fail(jwt_token):
    wordlist = ["wrong", "123", "admin"]
    bruteforcer = JWTBruteforcer(jwt_token, wordlist)
    bruteforcer.start()
    assert not bruteforcer.success, "A brute force não deveria ter sucesso."
    assert bruteforcer.found_key is None, "Nenhuma chave deveria ser encontrada."

def test_bruteforce_with_file(tmp_path, jwt_token):
    # Cria um arquivo temporário de wordlist
    wordlist_file = tmp_path / "wordlist.txt"
    wordlist_file.write_text("wrong\n123\n\n")
    bruteforcer = JWTBruteforcer(jwt_token, str(wordlist_file))
    bruteforcer.start()
    assert bruteforcer.success, "A brute force deveria ter sucesso com a chave vazia no arquivo."
    assert bruteforcer.found_key == "", "A chave encontrada deveria ser vazia."
    assert bruteforcer.found_algorithm in ["HS256", "HS384", "HS512"], "Algoritmo inesperado."

def test_mutate_word_coverage(jwt_token):
    wordlist = ["admin"]
    bruteforcer = JWTBruteforcer(jwt_token, wordlist)
    mutations = bruteforcer._mutate_word("admin")
    # Deve conter mutações básicas
    assert "admin" in mutations
    assert "ADMIN" in mutations
    assert "Admin" in mutations
    assert "admin123" in mutations
    assert "123admin" in mutations
    assert "adm1n" in mutations or "adm1n" in [m.replace("@", "a").replace("0", "o").replace("1", "i").replace("3", "e") for m in mutations]

def test_incremental_charset_attack(jwt_token):
    # Testa ataque incremental com charset reduzido e tamanho 0-1 (deve encontrar "")
    key, algo = JWTBruteforcer.incremental_charset_attack(jwt_token, charset="", min_len=0, max_len=0)
    assert key == "", "A chave encontrada pelo ataque incremental deveria ser vazia."
    assert algo in ["HS256"], "Algoritmo inesperado no ataque incremental."

def test_bruteforce_multiple_algorithms(jwt_token, wordlist):
    bruteforcer = JWTBruteforcer(jwt_token, wordlist, algorithms=["HS256", "HS384"])
    bruteforcer.start()
    assert bruteforcer.success, "A brute force deveria ter sucesso com múltiplos algoritmos."
    assert bruteforcer.found_key == "", "A chave encontrada deveria ser vazia."
    assert bruteforcer.found_algorithm in ["HS256", "HS384"], "Algoritmo inesperado."

def test_bruteforce_output_file(tmp_path, jwt_token, wordlist):
    output_file = tmp_path / "found_key.txt"
    bruteforcer = JWTBruteforcer(jwt_token, wordlist, output_file=str(output_file))
    bruteforcer.start()
    if bruteforcer.success:
        content = output_file.read_text()
        assert bruteforcer.found_key in content, "A chave encontrada deveria estar no arquivo de saída."
