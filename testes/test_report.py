import pytest
from unittest.mock import patch, MagicMock
import sys
import io

# Supondo que o módulo report está em core.report
from core import report

@pytest.fixture
def sample_data():
    return [
        {"user": "admin", "status": "success", "token": "abc.def.ghi"},
        {"user": "user", "status": "fail", "token": None}
    ]

def test_generate_report_json(sample_data, tmp_path):
    output_file = tmp_path / "report.json"
    result = report.generate_report(sample_data, output=str(output_file), format="json")
    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "\"user\": \"admin\"" in content
        assert "\"status\": \"fail\"" in content

def test_generate_report_csv(sample_data, tmp_path):
    output_file = tmp_path / "report.csv"
    result = report.generate_report(sample_data, output=str(output_file), format="csv")
    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "user,status,token" in content
        assert "admin,success,abc.def.ghi" in content

def test_generate_report_txt(sample_data, tmp_path):
    output_file = tmp_path / "report.txt"
    result = report.generate_report(sample_data, output=str(output_file), format="txt")
    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "user: admin" in content
        assert "status: fail" in content

def test_report_export_email(sample_data):
    with patch("core.report.send_report_email") as mock_send:
        mock_send.return_value = True
        result = report.export_report(sample_data, method="email", recipient="test@example.com")
        assert result is True
        mock_send.assert_called_once()

def test_report_export_slack(sample_data):
    with patch("core.report.send_report_slack") as mock_slack:
        mock_slack.return_value = True
        result = report.export_report(sample_data, method="slack", channel="#test")
        assert result is True
        mock_slack.assert_called_once()

def test_report_summary(sample_data):
    summary = report.generate_summary(sample_data)
    assert "success" in summary.lower()
    assert "fail" in summary.lower()

def test_report_error_handling(sample_data, tmp_path):
    # Simula erro ao salvar arquivo
    with patch("builtins.open", side_effect=PermissionError("Simulado")):
        with pytest.raises(PermissionError):
            report.generate_report(sample_data, output=str(tmp_path / "fail.json"), format="json")

def test_report_cli_integration(monkeypatch, sample_data):
    # Simula execução via CLI
    args = ["prog", "report", "--input", "input.json", "--output", "out.json", "--format", "json"]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("core.report.generate_report", MagicMock(return_value=True))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        report.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "Relatório gerado" in output or "Report" in output

def test_report_integration_with_bruteforce(monkeypatch):
    # Integração: gera relatório a partir do resultado do brute force
    fake_results = [
        {"user": "admin", "status": "success", "token": "abc.def.ghi"},
        {"user": "user", "status": "fail", "token": None}
    ]
    monkeypatch.setattr("core.bruteforce.run_bruteforce", MagicMock(return_value=fake_results))
    result = report.generate_report(fake_results, format="json")
    assert result is not None

if __name__ == "__main__":
    pytest.main()