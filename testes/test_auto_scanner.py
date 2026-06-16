import pytest
from unittest.mock import patch, MagicMock
import sys
import io

# Supondo que o módulo auto_scanner está em core.auto_scanner
from core import auto_scanner

@pytest.fixture
def target_url():
    return "http://localhost/api"

@pytest.fixture
def fake_wordlist():
    return ["admin", "root", "senha123"]

@pytest.fixture
def fake_scan_results():
    return [
        {"endpoint": "/login", "vulnerable": True, "type": "SQLi"},
        {"endpoint": "/user", "vulnerable": False}
    ]

def test_auto_scan_basic_success(target_url, fake_wordlist, fake_scan_results):
    with patch("core.auto_scanner.scan_endpoints") as mock_scan:
        mock_scan.return_value = fake_scan_results
        results = auto_scanner.scan_endpoints(target_url, wordlist=fake_wordlist)
        assert isinstance(results, list)
        assert any(r["vulnerable"] for r in results)

def test_auto_scan_no_vulnerabilities(target_url, fake_wordlist):
    with patch("core.auto_scanner.scan_endpoints") as mock_scan:
        mock_scan.return_value = [{"endpoint": "/login", "vulnerable": False}]
        results = auto_scanner.scan_endpoints(target_url, wordlist=fake_wordlist)
        assert all(not r["vulnerable"] for r in results)

def test_auto_scan_error_handling(target_url, fake_wordlist):
    with patch("core.auto_scanner.scan_endpoints", side_effect=Exception("Erro simulado")):
        with pytest.raises(Exception):
            auto_scanner.scan_endpoints(target_url, wordlist=fake_wordlist)

def test_auto_scan_with_custom_rules(target_url, fake_wordlist):
    rules = {"methods": ["GET", "POST"], "depth": 2}
    with patch("core.auto_scanner.scan_endpoints") as mock_scan:
        mock_scan.return_value = [{"endpoint": "/custom", "vulnerable": True, "type": "XSS"}]
        results = auto_scanner.scan_endpoints(target_url, wordlist=fake_wordlist, rules=rules)
        assert any(r["type"] == "XSS" for r in results)

def test_auto_scan_delay_simulation(target_url, fake_wordlist):
    import time
    with patch("core.auto_scanner.scan_endpoints") as mock_scan:
        def slow_scan(*args, **kwargs):
            time.sleep(0.1)
            return [{"endpoint": "/slow", "vulnerable": True}]
        mock_scan.side_effect = slow_scan
        results = auto_scanner.scan_endpoints(target_url, wordlist=fake_wordlist)
        assert any(r["vulnerable"] for r in results)

def test_auto_scanner_cli(monkeypatch):
    args = ["prog", "auto-scan", "--url", "http://localhost/api", "--wordlist", "admin,root"]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("core.auto_scanner.scan_endpoints", MagicMock(return_value=[{"endpoint": "/login", "vulnerable": True}]))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        auto_scanner.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "Vulnerável" in output or "/login" in output

def test_auto_scanner_integration_with_report(monkeypatch, target_url, fake_wordlist):
    monkeypatch.setattr("core.report.generate_report", MagicMock(return_value=True))
    with patch("core.auto_scanner.scan_endpoints") as mock_scan:
        mock_scan.return_value = [{"endpoint": "/login", "vulnerable": True}]
        results = auto_scanner.scan_endpoints(target_url, wordlist=fake_wordlist)
        assert any(r["vulnerable"] for r in results)

def test_auto_scanner_multiple_targets(fake_wordlist):
    targets = ["http://localhost/api", "http://localhost/admin"]
    with patch("core.auto_scanner.scan_endpoints") as mock_scan:
        mock_scan.side_effect = lambda url, **kwargs: [{"endpoint": url, "vulnerable": True}]
        results = []
        for t in targets:
            results.extend(auto_scanner.scan_endpoints(t, wordlist=fake_wordlist))
        assert any("admin" in r["endpoint"] for r in results)

def test_auto_scanner_custom_parser():
    with patch("core.auto_scanner.custom_parser") as mock_parser:
        mock_parser.return_value = [{"endpoint": "/custom", "vulnerable": True}]
        results = auto_scanner.custom_parser("raw data")
        assert any(r["vulnerable"] for r in results)

if __name__ == "__main__":
    pytest.main()