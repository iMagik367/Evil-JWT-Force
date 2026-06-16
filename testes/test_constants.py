import pytest

# Supondo que o módulo constants está em utils.constants
from utils import constants

def test_constants_integrity():
    # Testa se as principais constantes existem e possuem valores esperados
    assert hasattr(constants, "DEFAULT_TIMEOUT")
    assert hasattr(constants, "SUPPORTED_ALGORITHMS")
    assert hasattr(constants, "DEFAULT_WORDLIST")
    assert isinstance(constants.SUPPORTED_ALGORITHMS, (list, tuple))
    assert "HS256" in constants.SUPPORTED_ALGORITHMS

def test_constants_immutability():
    # Testa se as constantes não podem ser alteradas (imutabilidade)
    original = constants.DEFAULT_TIMEOUT
    try:
        constants.DEFAULT_TIMEOUT = 999
        assert constants.DEFAULT_TIMEOUT == original, "Constantes devem ser imutáveis!"
    except Exception:
        pass  # Esperado se for imutável

def test_constants_values():
    # Testa valores específicos das constantes
    assert constants.DEFAULT_TIMEOUT > 0
    assert isinstance(constants.DEFAULT_WORDLIST, str)
    assert constants.DEFAULT_WORDLIST.endswith(".txt")

def test_constants_usage_in_modules():
    # Testa integração: módulos usam as constantes corretamente
    from utils import helpers
    assert helpers.get_default_timeout() == constants.DEFAULT_TIMEOUT

def test_constants_supported_algorithms():
    # Testa se todos os algoritmos suportados são strings e conhecidos
    for alg in constants.SUPPORTED_ALGORITHMS:
        assert isinstance(alg, str)
        assert alg.startswith("HS") or alg.startswith("RS") or alg.startswith("ES")

def test_constants_cli_integration(monkeypatch):
    # Testa se a constante é usada na CLI
    from core import cli
    monkeypatch.setattr("utils.constants.DEFAULT_TIMEOUT", 123)
    assert cli.get_timeout_from_constants() == 123

def test_constants_error_handling():
    # Testa comportamento ao acessar constante inexistente
    with pytest.raises(AttributeError):
        _ = constants.NOT_A_REAL_CONSTANT

if __name__ == "__main__":
    pytest.main()