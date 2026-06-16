import requests


def discover_endpoints(base_url):
    """Descobre endpoints comuns a partir de dicionário estático ou fuzzing básico."""
    # Testar dicionários e caminhos conhecidos
    return ["/api/pay", "/webhook/pix", "/api/saldo", "/pix/confirm"]


def fingerprint_headers(url):
    """Retorna headers retornados pelo servidor."""
    try:
        r = requests.get(url, timeout=5)
        return dict(r.headers)
    except:
        return {}


def find_sqli_params(url):
    """Identifica parâmetros potencialmente vulneráveis a SQLi."""
    # Simular parâmetros e testar respostas
    return ["user_id", "balance", "amount"]


def extract_pix_txids(url):
    """Extrai TXIDs de QR Code ou Copy-Paste Pix (simulação)."""
    return ["TX1234567890", "TXID_MOCKED"]


def guess_webhook_endpoints(endpoints):
    """Filtra endpoints relacionados a Pix/webhook."""
    return [e for e in endpoints if "pix" in e or "confirm" in e]


def test_jwt_tokens(url):
    """Testa JWTs válidos e inválidos contra o endpoint."""
    # Placeholder: implement real JWT testing
    return {"valid_jwt_sample": False} 