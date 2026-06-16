import pytest
from unittest.mock import patch, MagicMock
import sys
import io
import base64
import json

# Supondo que o módulo fuzz_jwt está em core.fuzz_jwt
from core import fuzz_jwt

@pytest.fixture
def jwt_token():
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"user": "admin"}).encode()).rstrip(b"=").decode()
    signature = "signature"
    return f"{header}.{payload}.{signature}"

@pytest.fixture
def wordlist():
    return ["admin", "root", "test", "jwt"]

def test_fuzz_jwt_basic_success(jwt_token):
    with patch("core.fuzz_jwt.send_fuzzed_jwt") as mock_send:
        mock_send.return_value = {"vulnerable": True, "alg": "none"}
        result = fuzz_jwt.fuzz(jwt_token)
        assert result["vulnerable"]
        assert result["alg"] == "none"

def test_fuzz_jwt_fail(jwt_token):
    with patch("core.fuzz_jwt.send_fuzzed_jwt") as mock_send:
        mock_send.return_value = {"vulnerable": False}
        result = fuzz_jwt.fuzz(jwt_token)
        assert not result["vulnerable"]

def test_fuzz_jwt_with_wordlist(jwt_token, wordlist):
    with patch("core.fuzz_jwt.fuzz_with_wordlist") as mock_fuzz:
        mock_fuzz.return_value = {"found": True, "key": "admin"}
        result = fuzz_jwt.fuzz_with_wordlist(jwt_token, wordlist)
        assert result["found"]
        assert result["key"] in wordlist

def test_fuzz_jwt_header_manipulation(jwt_token):
    with patch("core.fuzz_jwt.fuzz_header") as mock_fuzz:
        mock_fuzz.return_value = {"alg": "none", "bypass": True}
        result = fuzz_jwt.fuzz_header(jwt_token)
        assert result["bypass"]

def test_fuzz_jwt_payload_manipulation(jwt_token):
    with patch("core.fuzz_jwt.fuzz_payload") as mock_fuzz:
        mock_fuzz.return_value = {"escalation": True}
        result = fuzz_jwt.fuzz_payload(jwt_token)
        assert result["escalation"]

def test_fuzz_jwt_signature_manipulation(jwt_token):
    with patch("core.fuzz_jwt.fuzz_signature") as mock_fuzz:
        mock_fuzz.return_value = {"signature_bypass": True}
        result = fuzz_jwt.fuzz_signature(jwt_token)
        assert result["signature_bypass"]

def test_fuzz_jwt_error_handling(jwt_token):
    with patch("core.fuzz_jwt.send_fuzzed_jwt", side_effect=Exception("Erro simulado")):
        with pytest.raises(Exception):
            fuzz_jwt.fuzz(jwt_token)

def test_fuzz_jwt_cli(monkeypatch, jwt_token):
    args = ["prog", "fuzz-jwt", "--token", jwt_token]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("core.fuzz_jwt.fuzz", MagicMock(return_value={"vulnerable": True, "alg": "none"}))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        fuzz_jwt.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "vulnerável" in output.lower() or "alg" in output

def test_fuzz_jwt_multiple_tokens(wordlist):
    tokens = [
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4ifQ.signature",
        "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoicm9vdCJ9."
    ]
    with patch("core.fuzz_jwt.fuzz") as mock_fuzz:
        mock_fuzz.side_effect = [{"vulnerable": True}, {"vulnerable": False}]
        results = [fuzz_jwt.fuzz(t) for t in tokens]
        assert any(r["vulnerable"] for r in results)

def test_fuzz_jwt_custom_parser(jwt_token):
    with patch("core.fuzz_jwt.custom_parser") as mock_parser:
        mock_parser.return_value = {"parsed": True}
        result = fuzz_jwt.custom_parser(jwt_token)
        assert result["parsed"]

if __name__ == "__main__":
    pytest.main()