import pytest
from unittest.mock import patch, MagicMock
import logging
import sys
import io

# Supondo que o módulo logger está em utils.logger
from utils import logger

@pytest.fixture
def log_message():
    return "Mensagem de teste para o logger"

def test_logger_info_level(log_message, capsys):
    logger.set_level("INFO")
    logger.info(log_message)
    captured = capsys.readouterr()
    assert "INFO" in captured.out
    assert log_message in captured.out

def test_logger_warning_level(log_message, capsys):
    logger.set_level("WARNING")
    logger.warning(log_message)
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
    assert log_message in captured.out

def test_logger_error_level(log_message, capsys):
    logger.set_level("ERROR")
    logger.error(log_message)
    captured = capsys.readouterr()
    assert "ERROR" in captured.out
    assert log_message in captured.out

def test_logger_debug_level(log_message, capsys):
    logger.set_level("DEBUG")
    logger.debug(log_message)
    captured = capsys.readouterr()
    assert "DEBUG" in captured.out
    assert log_message in captured.out

def test_logger_formatting(log_message, capsys):
    logger.set_format("[%(levelname)s] %(message)s")
    logger.info(log_message)
    captured = capsys.readouterr()
    assert "[" in captured.out and "]" in captured.out

def test_logger_file_output(tmp_path, log_message):
    log_file = tmp_path / "test.log"
    logger.set_file(str(log_file))
    logger.info(log_message)
    with open(log_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert log_message in content

def test_logger_rotation(tmp_path, log_message):
    log_file = tmp_path / "rotate.log"
    logger.set_file(str(log_file), rotation="1 KB")
    for _ in range(100):
        logger.info(log_message)
    # Verifica se o arquivo existe e se há rotação (pode variar conforme implementação)
    assert log_file.exists()

def test_logger_exception_handling(capsys):
    try:
        raise ValueError("Erro simulado")
    except Exception as e:
        logger.exception("Exceção capturada")
    captured = capsys.readouterr()
    assert "Exceção capturada" in captured.out or "Traceback" in captured.out

def test_logger_integration_with_module(capsys):
    # Supondo que outro módulo use o logger
    from utils import helpers
    helpers.log_something("Teste integração")
    captured = capsys.readouterr()
    assert "Teste integração" in captured.out

def test_logger_cli(monkeypatch):
    args = ["prog", "log", "--level", "INFO", "--message", "Mensagem CLI"]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("utils.logger.info", MagicMock())
    try:
        logger.main()
    except SystemExit:
        pass
    finally:
        sys.argv = sys_argv_backup
    logger.info.assert_called_with("Mensagem CLI")

def test_logger_invalid_level():
    with pytest.raises(ValueError):
        logger.set_level("INVALID")

if __name__ == "__main__":
    pytest.main()