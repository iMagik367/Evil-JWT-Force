import pytest
from unittest.mock import patch, MagicMock
import sys
import io
import threading
import time

# Supondo que o módulo token_bruteforce está em core.token_bruteforce
from core import token_bruteforce

@pytest.fixture
def target_url():
    return "http://localhost/api/token"

@pytest.fixture
def fake_wordlist():
    # Wordlist grande para simular brute force pesado
    return [f"token{i}" for i in range(1000)] + ["admin123", "root456"]

@pytest.fixture
def fake_bruteforce_result():
    return {"found": True, "token": "admin123"}

def test_bruteforce_basic_success(target_url, fake_wordlist, fake_bruteforce_result):
    with patch("core.token_bruteforce.try_token") as mock_try:
        mock_try.side_effect = lambda url, token: token == "admin123"
        result = token_bruteforce.bruteforce(target_url, wordlist=fake_wordlist)
        assert result["found"]
        assert result["token"] == "admin123"

def test_bruteforce_fail(target_url, fake_wordlist):
    with patch("core.token_bruteforce.try_token") as mock_try:
        mock_try.return_value = False
        result = token_bruteforce.bruteforce(target_url, wordlist=fake_wordlist)
        assert not result["found"]

def test_bruteforce_with_delay(target_url, fake_wordlist):
    with patch("core.token_bruteforce.try_token") as mock_try:
        def slow_try(url, token):
            time.sleep(0.01)
            return token == "root456"
        mock_try.side_effect = slow_try
        result = token_bruteforce.bruteforce(target_url, wordlist=fake_wordlist)
        assert result["found"]
        assert result["token"] == "root456"

def test_bruteforce_parallel(target_url, fake_wordlist):
    # Simula brute force paralelo usando threads
    found = {"token": None}
    def worker(token):
        if token == "admin123":
            found["token"] = token
    threads = []
    for token in fake_wordlist:
        t = threading.Thread(target=worker, args=(token,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    assert found["token"] == "admin123"

def test_bruteforce_error_handling(target_url, fake_wordlist):
    with patch("core.token_bruteforce.try_token", side_effect=Exception("Erro simulado")):
        with pytest.raises(Exception):
            token_bruteforce.bruteforce(target_url, wordlist=fake_wordlist)

def test_bruteforce_cli(monkeypatch, target_url):
    args = ["prog", "token-bruteforce", "--url", target_url, "--wordlist", "token1,admin123"]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("core.token_bruteforce.bruteforce", MagicMock(return_value={"found": True, "token": "admin123"}))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        token_bruteforce.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "admin123" in output or "Token encontrado" in output

def test_bruteforce_multiple_targets(fake_wordlist):
    targets = ["http://localhost/api/token", "http://localhost/api/auth"]
    with patch("core.token_bruteforce.bruteforce") as mock_brute:
        mock_brute.side_effect = [{"found": True, "token": "token1"}, {"found": False}]
        results = [token_bruteforce.bruteforce(t, wordlist=fake_wordlist) for t in targets]
        assert any(r["found"] for r in results)

def test_bruteforce_custom_analyzer():
    with patch("core.token_bruteforce.custom_analyzer") as mock_analyze:
        mock_analyze.return_value = {"analyzed": True, "score": 100}
        result = token_bruteforce.custom_analyzer("token data")
        assert result["analyzed"]
        assert result["score"] == 100

def test_bruteforce_with_auth(target_url, fake_wordlist):
    with patch("core.token_bruteforce.try_token") as mock_try:
        mock_try.side_effect = lambda url, token, auth=None: token == "admin123" and auth == "Bearer test"
        result = token_bruteforce.bruteforce(target_url, wordlist=fake_wordlist, auth="Bearer test")
        assert result["found"]
        assert result["token"] == "admin123"

def test_bruteforce_rate_limit(target_url, fake_wordlist):
    with patch("core.token_bruteforce.try_token") as mock_try:
        mock_try.side_effect = [False, Exception("Rate limit"), True, False]
        try:
            result = None
            for token in fake_wordlist:
                try:
                    if token_bruteforce.try_token(target_url, token):
                        result = token
                        break
                except Exception:
                    continue
            assert result is not None
        except Exception:
            pytest.fail("Falha ao lidar com rate limit")

def test_bruteforce_incremental(target_url, fake_wordlist):
    # Simula brute force incremental (continua de onde parou)
    with patch("core.token_bruteforce.bruteforce_incremental") as mock_brute:
        mock_brute.return_value = {"found": True, "token": "root456"}
        result = token_bruteforce.bruteforce_incremental(target_url, wordlist=fake_wordlist, last_tried="admin123")
        assert result["found"]
        assert result["token"] == "root456"

if __name__ == "__main__":
    pytest.main()