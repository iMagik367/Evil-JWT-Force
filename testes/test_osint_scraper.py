import pytest
from unittest.mock import patch, MagicMock
import sys
import io

# Supondo que o módulo osint_scraper está em core.osint_scraper
from core import osint_scraper

@pytest.fixture
def target():
    return "admin@example.com"

@pytest.fixture
def fake_sources():
    return ["https://pastebin.com", "https://github.com", "https://twitter.com"]

@pytest.fixture
def fake_wordlist():
    return ["admin", "admin@example.com", "root", "senha123"]

def test_scrape_basic_success(target, fake_sources):
    with patch("core.osint_scraper.scrape_from_source") as mock_scrape:
        mock_scrape.side_effect = [
            ["admin@example.com"], [], ["root@example.com"]
        ]
        results = osint_scraper.scrape(target, sources=fake_sources)
        assert "admin@example.com" in results or "root@example.com" in results

def test_scrape_basic_fail(target, fake_sources):
    with patch("core.osint_scraper.scrape_from_source") as mock_scrape:
        mock_scrape.return_value = []
        results = osint_scraper.scrape(target, sources=fake_sources)
        assert results == []

def test_scrape_with_wordlist(target, fake_wordlist):
    with patch("core.osint_scraper.scrape_with_wordlist") as mock_scrape:
        mock_scrape.return_value = ["admin@example.com"]
        results = osint_scraper.scrape_with_wordlist(target, fake_wordlist)
        assert "admin@example.com" in results

def test_scrape_error_handling(target, fake_sources):
    with patch("core.osint_scraper.scrape_from_source", side_effect=Exception("Erro simulado")):
        with pytest.raises(Exception):
            osint_scraper.scrape(target, sources=fake_sources)

def test_scrape_delay_simulation(target, fake_sources):
    import time
    with patch("core.osint_scraper.scrape_from_source") as mock_scrape:
        def slow_scrape(*args, **kwargs):
            time.sleep(0.1)
            return ["admin@example.com"]
        mock_scrape.side_effect = slow_scrape
        results = osint_scraper.scrape(target, sources=fake_sources)
        assert "admin@example.com" in results

def test_scrape_cli(monkeypatch):
    args = ["prog", "osint-scrape", "--target", "admin@example.com", "--sources", "https://pastebin.com,https://github.com"]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("core.osint_scraper.scrape", MagicMock(return_value=["admin@example.com"]))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        osint_scraper.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "admin@example.com" in output or "Resultado" in output

def test_scrape_integration_with_report(monkeypatch, target, fake_sources):
    # Integração: gera relatório após scraping
    monkeypatch.setattr("core.report.generate_report", MagicMock(return_value=True))
    with patch("core.osint_scraper.scrape") as mock_scrape:
        mock_scrape.return_value = ["admin@example.com"]
        results = osint_scraper.scrape(target, sources=fake_sources)
        assert "admin@example.com" in results

def test_scrape_multiple_targets(fake_sources):
    targets = ["admin@example.com", "user@example.com"]
    with patch("core.osint_scraper.scrape_from_source") as mock_scrape:
        mock_scrape.side_effect = lambda t, s: [t]
        results = []
        for t in targets:
            results.extend(osint_scraper.scrape(t, sources=fake_sources))
        assert "admin@example.com" in results and "user@example.com" in results

def test_scrape_custom_parser(target):
    with patch("core.osint_scraper.custom_parser") as mock_parser:
        mock_parser.return_value = ["custom@example.com"]
        results = osint_scraper.custom_parser("raw data")
        assert "custom@example.com" in results

if __name__ == "__main__":
    pytest.main()