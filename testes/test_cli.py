import pytest
from unittest.mock import patch, MagicMock
import sys
import io

from core import cli
from core.auth import Authenticator

@pytest.fixture
def fake_args_login():
    return ["prog", "login", "--url", "http://localhost/api/auth", "--user", "admin", "--password", "admin123"]

@pytest.fixture
def fake_args_bruteforce():
    return ["prog", "bruteforce", "--url", "http://localhost/api/auth", "--wordlist", "config/default_creds.txt"]

@pytest.fixture
def fake_args_invalid():
    return ["prog", "invalidcmd"]

def run_cli_with_args(args):
    sys_argv_backup = sys.argv
    sys.argv = args
    captured = io.StringIO()
    sys.stdout = captured
    try:
        cli.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    return captured.getvalue()

def test_cli_login_success(fake_args_login):
    with patch("core.auth.Authenticator.authenticate") as mock_auth:
        mock_auth.return_value = True
        output = run_cli_with_args(fake_args_login)
        assert "Login realizado com sucesso" in output or "Autenticação bem-sucedida" in output

def test_cli_login_fail(fake_args_login):
    with patch("core.auth.Authenticator.authenticate") as mock_auth:
        mock_auth.return_value = False
        output = run_cli_with_args(fake_args_login)
        assert "Falha na autenticação" in output or "Login falhou" in output

def test_cli_bruteforce(fake_args_bruteforce):
    with patch("core.bruteforce.run_bruteforce") as mock_brute:
        mock_brute.return_value = [("admin", "admin123")]
        output = run_cli_with_args(fake_args_bruteforce)
        assert "admin:admin123" in output or "Credenciais válidas encontradas" in output

def test_cli_invalid_command(fake_args_invalid):
    output = run_cli_with_args(fake_args_invalid)
    assert "Comando inválido" in output or "Uso:" in output

def test_cli_help():
    output = run_cli_with_args(["prog", "--help"])
    assert "Uso:" in output or "help" in output

def test_cli_auto_discovery():
    args = ["prog", "autodiscover", "--url", "http://localhost", "--endpoints", "api/auth/login,api/user/info"]
    with patch("core.auth.auto_discovery") as mock_auto:
        mock_auto.return_value = [("admin", "admin123")]
        output = run_cli_with_args(args)
        assert "admin:admin123" in output or "Credenciais descobertas" in output

def test_cli_token_extraction():
    args = ["prog", "extract-token", "--response", '{"token":"abc.def.ghi"}']
    with patch("core.auth.Authenticator._extract_jwt") as mock_extract:
        mock_extract.return_value = None
        output = run_cli_with_args(args)
        assert "Token extraído" in output or "abc.def.ghi" in output

def test_cli_error_handling(monkeypatch):
    args = ["prog", "login", "--url", "http://localhost/api/auth", "--user", "admin", "--password", "admin123"]
    with patch("core.auth.Authenticator.authenticate", side_effect=Exception("Erro simulado")):
        output = run_cli_with_args(args)
        assert "Erro" in output or "Exception" in output

if __name__ == "__main__":
    pytest.main()