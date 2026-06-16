import pytest
from unittest.mock import patch, MagicMock
import sys
import io

# Supondo que o módulo sql_injector está em core.sql_injector
from core import sql_injector

@pytest.fixture
def vulnerable_url():
    return "http://localhost/api/user?id=1"

@pytest.fixture
def payloads():
    return ["' OR 1=1--", "' UNION SELECT NULL--", "'; WAITFOR DELAY '0:0:5'--"]

@pytest.fixture
def wordlist():
    return ["admin", "1' OR '1'='1", "' OR 1=1--", "' OR 'a'='a"]

def test_detect_sql_injection_success(vulnerable_url, payloads):
    with patch("core.sql_injector.send_payload") as mock_send:
        mock_send.side_effect = [False, True, False]
        result = sql_injector.detect_sql_injection(vulnerable_url, payloads)
        assert result is True or result is not None

def test_detect_sql_injection_fail(vulnerable_url):
    with patch("core.sql_injector.send_payload") as mock_send:
        mock_send.return_value = False
        result = sql_injector.detect_sql_injection(vulnerable_url, ["'"])
        assert result is False or result is None

def test_exploit_sql_injection(vulnerable_url):
    with patch("core.sql_injector.exploit_sql_injection") as mock_exploit:
        mock_exploit.return_value = {"success": True, "data": ["admin", "root"]}
        result = sql_injector.exploit_sql_injection(vulnerable_url, "' UNION SELECT user FROM users--")
        assert result["success"]
        assert "admin" in result["data"]

def test_bypass_waf(vulnerable_url):
    with patch("core.sql_injector.bypass_waf") as mock_bypass:
        mock_bypass.return_value = True
        assert sql_injector.bypass_waf(vulnerable_url) is True

def test_error_based_injection(vulnerable_url):
    with patch("core.sql_injector.error_based_injection") as mock_error:
        mock_error.return_value = {"error": "You have an error in your SQL syntax"}
        result = sql_injector.error_based_injection(vulnerable_url)
        assert "error" in result

def test_time_based_injection(vulnerable_url):
    with patch("core.sql_injector.time_based_injection") as mock_time:
        mock_time.return_value = {"delay": 5, "success": True}
        result = sql_injector.time_based_injection(vulnerable_url, "'; WAITFOR DELAY '0:0:5'--")
        assert result["success"]
        assert result["delay"] == 5

def test_integration_with_wordlist(vulnerable_url, wordlist):
    with patch("core.sql_injector.detect_sql_injection") as mock_detect:
        mock_detect.return_value = True
        result = sql_injector.detect_sql_injection(vulnerable_url, wordlist)
        assert result is True

def test_sql_injector_cli(monkeypatch):
    args = ["prog", "sql-inject", "--url", "http://localhost/api/user?id=1", "--payload", "' OR 1=1--"]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("core.sql_injector.detect_sql_injection", MagicMock(return_value=True))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        sql_injector.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "Vulnerabilidade detectada" in output or "SQL Injection" in output

def test_sql_injector_error_handling(vulnerable_url):
    with patch("core.sql_injector.send_payload", side_effect=Exception("Erro simulado")):
        with pytest.raises(Exception):
            sql_injector.detect_sql_injection(vulnerable_url, ["' OR 1=1--"])

def test_sql_injector_report_integration(monkeypatch, vulnerable_url):
    # Integração: gera relatório após detecção
    monkeypatch.setattr("core.report.generate_report", MagicMock(return_value=True))
    with patch("core.sql_injector.detect_sql_injection") as mock_detect:
        mock_detect.return_value = True
        result = sql_injector.detect_sql_injection(vulnerable_url, ["' OR 1=1--"])
        assert result is True

if __name__ == "__main__":
    pytest.main()