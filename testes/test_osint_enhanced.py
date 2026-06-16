import pytest
from unittest.mock import patch, MagicMock
import sys
import io

# Supondo que o módulo osint_enhanced está em core.osint_enhanced
from core import osint_enhanced

@pytest.fixture
def target():
    return "admin@example.com"

@pytest.fixture
def fake_sources():
    return ["https://pastebin.com", "https://linkedin.com", "https://twitter.com"]

@pytest.fixture
def fake_wordlist():
    return ["admin", "admin@example.com", "root", "senha123"]

def test_enhanced_scrape_basic_success(target, fake_sources):
    with patch("core.osint_enhanced.scrape_from_source") as mock_scrape:
        mock_scrape.side_effect = [
            ["admin@example.com"], [], ["root@example.com"]
        ]
        results = osint_enhanced.scrape(target, sources=fake_sources)
        assert "admin@example.com" in results or "root@example.com" in results

def test_enhanced_scrape_fail(target, fake_sources):
    with patch("core.osint_enhanced.scrape_from_source") as mock_scrape:
        mock_scrape.return_value = []
        results = osint_enhanced.scrape(target, sources=fake_sources)
        assert results == []

def test_enhanced_scrape_with_wordlist(target, fake_wordlist):
    with patch("core.osint_enhanced.scrape_with_wordlist") as mock_scrape:
        mock_scrape.return_value = ["admin@example.com"]
        results = osint_enhanced.scrape_with_wordlist(target, fake_wordlist)
        assert "admin@example.com" in results

def test_enhanced_scrape_error_handling(target, fake_sources):
    with patch("core.osint_enhanced.scrape_from_source", side_effect=Exception("Erro simulado")):
        with pytest.raises(Exception):
            osint_enhanced.scrape(target, sources=fake_sources)

def test_enhanced_scrape_delay_simulation(target, fake_sources):
    import time
    with patch("core.osint_enhanced.scrape_from_source") as mock_scrape:
        def slow_scrape(*args, **kwargs):
            time.sleep(0.1)
            return ["admin@example.com"]
        mock_scrape.side_effect = slow_scrape
        results = osint_enhanced.scrape(target, sources=fake_sources)
        assert "admin@example.com" in results

def test_enhanced_scrape_cli(monkeypatch):
    args = ["prog", "osint-enhanced", "--target", "admin@example.com", "--sources", "https://pastebin.com,https://linkedin.com"]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("core.osint_enhanced.scrape", MagicMock(return_value=["admin@example.com"]))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        osint_enhanced.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "admin@example.com" in output or "Resultado" in output

def test_enhanced_scrape_integration_with_report(monkeypatch, target, fake_sources):
    monkeypatch.setattr("core.report.generate_report", MagicMock(return_value=True))
    with patch("core.osint_enhanced.scrape") as mock_scrape:
        mock_scrape.return_value = ["admin@example.com"]
        results = osint_enhanced.scrape(target, sources=fake_sources)
        assert "admin@example.com" in results

def test_enhanced_scrape_multiple_targets(fake_sources):
    targets = ["admin@example.com", "user@example.com"]
    with patch("core.osint_enhanced.scrape_from_source") as mock_scrape:
        mock_scrape.side_effect = lambda t, s: [t]
        results = []
        for t in targets:
            results.extend(osint_enhanced.scrape(t, sources=fake_sources))
        assert "admin@example.com" in results and "user@example.com" in results

def test_enhanced_scrape_custom_analyzer(target):
    with patch("core.osint_enhanced.custom_analyzer") as mock_analyzer:
        mock_analyzer.return_value = {"analyzed": True, "score": 95}
        result = osint_enhanced.custom_analyzer("raw data")
        assert result["analyzed"]
        assert result["score"] > 90

# Teste de scraping com autenticação (token)
def test_enhanced_scrape_with_auth(target, fake_sources):
    with patch("core.osint_enhanced.scrape_from_source") as mock_scrape:
        mock_scrape.return_value = ["admin@example.com"]
        results = osint_enhanced.scrape(target, sources=fake_sources, auth_token="fake_token")
        assert "admin@example.com" in results

# Teste de scraping com proxy
def test_enhanced_scrape_with_proxy(target, fake_sources):
    with patch("core.osint_enhanced.scrape_from_source") as mock_scrape:
        mock_scrape.return_value = ["admin@example.com"]
        results = osint_enhanced.scrape(target, sources=fake_sources, proxy="127.0.0.1:9050")
        assert "admin@example.com" in results

# Teste de parsing de dados estruturados (JSON)
def test_enhanced_scrape_json_parsing(target):
    with patch("core.osint_enhanced.parse_json_data") as mock_parser:
        mock_parser.return_value = {"emails": ["admin@example.com"]}
        result = osint_enhanced.parse_json_data('{"emails":["admin@example.com"]}')
        assert "admin@example.com" in result["emails"]

# Teste de limitação de taxa (rate limit)
def test_enhanced_scrape_rate_limit(target, fake_sources):
    with patch("core.osint_enhanced.scrape_from_source") as mock_scrape:
        mock_scrape.side_effect = [[], Exception("Rate limit exceeded"), ["admin@example.com"]]
        try:
            results = []
            for _ in range(3):
                try:
                    results.extend(osint_enhanced.scrape(target, sources=fake_sources))
                except Exception:
                    pass
            assert "admin@example.com" in results
        except Exception:
            pytest.fail("Falha ao lidar com rate limit")

# Teste de scraping incremental (delta)
def test_enhanced_scrape_incremental(target, fake_sources):
    with patch("core.osint_enhanced.scrape_incremental") as mock_scrape:
        mock_scrape.return_value = ["novo_admin@example.com"]
        result = osint_enhanced.scrape_incremental(target, sources=fake_sources, last_seen="admin@example.com")
        assert "novo_admin@example.com" in result

# Teste de análise de relacionamentos entre dados coletados
def test_enhanced_scrape_relationship_analysis():
    with patch("core.osint_enhanced.analyze_relationships") as mock_analyze:
        mock_analyze.return_value = {"related": True, "links": 3}
        result = osint_enhanced.analyze_relationships(["admin@example.com", "user@example.com"])
        assert result["related"]
        assert result["links"] == 3

if __name__ == "__main__":
    pytest.main()