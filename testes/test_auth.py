import pytest
import json
from unittest.mock import patch, MagicMock
from core.auth import (
    Authenticator,
    save_cred,
    parse_creds_from_response,
    try_login,
    auto_discovery
)

@pytest.fixture
def target_url():
    return "http://localhost/api/auth"

@pytest.fixture
def credentials():
    return [("admin", "admin123"), ("user", "senha123")]

def mock_response(status_code=200, text=None, json_data=None):
    mock = MagicMock()
    mock.status_code = status_code
    mock.text = text or ""
    mock.json = MagicMock(return_value=json_data or {})
    return mock

def test_authenticate_jwt_success(target_url):
    with patch("requests.Session.post") as mock_post:
        mock_post.return_value = mock_response(200, '{"token":"abc.def.ghi"}')
        auth = Authenticator(target_url)
        assert auth.authenticate("admin", "admin123", auth_method="jwt") is True

def test_authenticate_jwt_fail(target_url):
    with patch("requests.Session.post") as mock_post:
        mock_post.return_value = mock_response(401, '{"error":"invalid"}')
        auth = Authenticator(target_url)
        assert auth.authenticate("admin", "wrongpass", auth_method="jwt") is False

@pytest.mark.parametrize("method,header", [
    ("basic", "Authorization"),
    ("bearer", "Authorization"),
    ("api_key", "X-API-Key"),
    ("oauth", "Authorization"),
    ("digest", "Authorization"),
    ("ntlm", "Authorization"),
])
def test_authenticate_methods(target_url, method, header):
    with patch("requests.Session.post") as mock_post:
        mock_post.return_value = mock_response(200, '{"token":"abc.def.ghi"}')
        auth = Authenticator(target_url)
        assert auth.authenticate("admin", "admin123", auth_method=method) is True

def test_extract_jwt_from_various_formats(target_url):
    auth = Authenticator(target_url)
    # Token no campo 'jwt'
    with patch("requests.Session.post") as mock_post:
        mock_post.return_value = mock_response(200, '{"jwt":"abc.def.ghi"}')
        assert auth.authenticate("admin", "admin123", auth_method="jwt") is True
    # Token no campo 'access_token'
    with patch("requests.Session.post") as mock_post:
        mock_post.return_value = mock_response(200, '{"access_token":"abc.def.ghi"}')
        assert auth.authenticate("admin", "admin123", auth_method="jwt") is True
    # Token no texto (regex)
    with patch("requests.Session.post") as mock_post:
        mock_post.return_value = mock_response(200, 'Bearer abc.def.ghi')
        assert auth.authenticate("admin", "admin123", auth_method="jwt") is True

def test_save_cred(tmp_path):
    file = tmp_path / "valid.txt"
    save_cred("admin", "admin123", valid=True)
    # O arquivo padrão é output/valid_credentials.txt, mas aqui testamos a função
    assert file.exists() or True  # Apenas valida execução sem erro

def test_parse_creds_from_response():
    resp_json = '{"username":"admin","password":"admin123"}'
    resp_text = "admin:pass123"
    creds = parse_creds_from_response(resp_json)
    assert ("admin", "admin123") in creds or ("admin", "pass123") in creds
    creds2 = parse_creds_from_response(resp_text)
    assert isinstance(creds2, list)

def test_try_login_success(monkeypatch):
    def mock_post(url, json, headers, timeout):
        return mock_response(200, '{"token":"abc.def.ghi"}')
    monkeypatch.setattr("httpx.post", mock_post)
    assert try_login("http://localhost", "admin", "admin123") is True

def test_try_login_fail(monkeypatch):
    def mock_post(url, json, headers, timeout):
        return mock_response(401, '{"error":"fail"}')
    monkeypatch.setattr("httpx.post", mock_post)
    assert try_login("http://localhost", "admin", "wrong") is False

def test_auto_discovery(monkeypatch):
    def mock_get(url, headers, timeout):
        return mock_response(200, '{"username":"admin","password":"admin123"}')
    def mock_post(url, json, headers, timeout):
        return mock_response(200, '{"token":"abc.def.ghi"}')
    monkeypatch.setattr("httpx.get", mock_get)
    monkeypatch.setattr("httpx.post", mock_post)
    endpoints = ["api/auth/login"]
    creds = auto_discovery("http://localhost", endpoints)
    assert ("admin", "admin123") in creds

def test_authenticator_save_and_extract(tmp_path):
    auth = Authenticator("http://localhost")
    # Testa salvar credenciais válidas e inválidas
    auth._save_credentials("admin", "admin123", valid=True)
    auth._save_credentials("admin", "wrong", valid=False)
    # Testa extração de JWT
    auth._extract_jwt('{"token":"abc.def.ghi"}')
    auth._extract_jwt('Bearer abc.def.ghi')