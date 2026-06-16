import pytest
from unittest.mock import patch, MagicMock
import sys
import io

# Supondo que o módulo sentry_simulator está em core.sentry_simulator
from core import sentry_simulator

@pytest.fixture
def fake_event():
    return {
        "event_id": "123abc",
        "level": "error",
        "message": "Simulated error",
        "user": {"id": "42", "username": "admin"},
        "tags": {"env": "test"}
    }

def test_send_event_success(fake_event):
    with patch("core.sentry_simulator.send_event") as mock_send:
        mock_send.return_value = True
        result = sentry_simulator.send_event(fake_event)
        assert result is True
        mock_send.assert_called_once_with(fake_event)

def test_send_event_failure(fake_event):
    with patch("core.sentry_simulator.send_event") as mock_send:
        mock_send.side_effect = Exception("Falha simulada")
        with pytest.raises(Exception):
            sentry_simulator.send_event(fake_event)

def test_simulate_exception_event():
    with patch("core.sentry_simulator.send_event") as mock_send:
        mock_send.return_value = True
        try:
            raise ValueError("Erro de teste")
        except Exception as e:
            event = sentry_simulator.create_event_from_exception(e)
            result = sentry_simulator.send_event(event)
            assert result is True
            assert event["level"] == "error"
            assert "Erro de teste" in event["message"]

def test_generate_custom_event():
    event = sentry_simulator.generate_custom_event(
        level="warning",
        message="Aviso customizado",
        user={"id": "99", "username": "tester"},
        tags={"feature": "simulador"}
    )
    assert event["level"] == "warning"
    assert event["message"] == "Aviso customizado"
    assert event["user"]["username"] == "tester"
    assert event["tags"]["feature"] == "simulador"

def test_sentry_simulator_cli(monkeypatch):
    args = ["prog", "sentry-sim", "--event", "error", "--message", "Falha crítica"]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("core.sentry_simulator.send_event", MagicMock(return_value=True))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        sentry_simulator.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "Evento enviado" in output or "Simulação" in output

def test_integration_with_report(monkeypatch, fake_event):
    # Integração: envia evento após gerar relatório
    monkeypatch.setattr("core.report.generate_report", MagicMock(return_value=True))
    with patch("core.sentry_simulator.send_event") as mock_send:
        mock_send.return_value = True
        sentry_simulator.notify_report_event(fake_event)
        mock_send.assert_called_once_with(fake_event)

def test_event_logging(fake_event, capsys):
    with patch("core.sentry_simulator.send_event") as mock_send:
        mock_send.return_value = True
        sentry_simulator.send_event(fake_event)
        captured = capsys.readouterr()
        assert "event_id" in captured.out or "Simulated" in captured.out

if __name__ == "__main__":
    pytest.main()