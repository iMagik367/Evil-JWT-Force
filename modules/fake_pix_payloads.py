# -*- coding: utf-8 -*-
"""
Fake Pix Payloads - Modelos padrão e avançados para requests e responses de endpoints Pix (BACEN/PSP)
Inclui: Cobrança Imediata, CobV, LoteCobV, Devolução, Erros, Edge Cases
"""

def payload_criacao_cobranca(valor, chave_pix, info_adicional=None, cpf=None, cnpj=None, pagador_nome=None, txid=None):
    """
    Payload de Requisição de Criação de Cobrança (Charge Creation Request) - Avançado
    """
    payload = {
        "calendario": {"expiracao": 3600},
        "valor": {"original": f"{valor:.2f}"},
        "chave": chave_pix,
        "solicitacaoPagador": info_adicional or "Pagamento via Pix"
    }
    if cpf or cnpj or pagador_nome:
        payload["devedor"] = {}
        if cpf:
            payload["devedor"]["cpf"] = cpf
        if cnpj:
            payload["devedor"]["cnpj"] = cnpj
        if pagador_nome:
            payload["devedor"]["nome"] = pagador_nome
    if txid:
        payload["txid"] = txid
    return payload

def payload_resposta_criacao_cobranca(txid, location, qr_code, status="ATIVA", expiracao="2025-12-31T23:59:59Z", revisao=0, pagador=None):
    """
    Payload de Resposta da Criação de Cobrança (Charge Creation Response) - Avançado
    """
    resp = {
        "txid": txid,
        "loc": {"id": location, "location": f"https://pix.psp/loc/{location}"},
        "status": status,
        "calendario": {"expiracao": expiracao},
        "valor": {"original": "100.00"},
        "chave": "chave-pix-exemplo",
        "qr_code": qr_code,
        "imagemQrcode": f"data:image/png;base64,FAKEBASE64...",
        "revisao": revisao
    }
    if pagador:
        resp["pagador"] = pagador
    return resp

def payload_consulta_cobranca(txid=None, chave_pix=None, cpf=None, cnpj=None, status=None, inicio=None, fim=None):
    """
    Payload de Requisição de Consulta de Cobrança (Charge Inquiry Request) - Avançado
    """
    req = {}
    if txid:
        req["txid"] = txid
    if chave_pix:
        req["chave"] = chave_pix
    if cpf:
        req["cpf"] = cpf
    if cnpj:
        req["cnpj"] = cnpj
    if status:
        req["status"] = status
    if inicio:
        req["inicio"] = inicio
    if fim:
        req["fim"] = fim
    return req

def payload_resposta_consulta_cobranca(txid, status, valor, pagador=None, revisao=0, location=None, qr_code=None, devolucoes=None):
    """
    Payload de Resposta da Consulta de Cobrança (Charge Inquiry Response) - Avançado
    """
    resp = {
        "txid": txid,
        "status": status,
        "valor": {"original": f"{valor:.2f}"},
        "pagador": pagador or {"nome": "Pagador Exemplo", "cpf": "00000000191"},
        "horario": "2025-06-13T00:00:00Z",
        "revisao": revisao
    }
    if location:
        resp["loc"] = {"id": location, "location": f"https://pix.psp/loc/{location}"}
    if qr_code:
        resp["qr_code"] = qr_code
    if devolucoes:
        resp["devolucoes"] = devolucoes  # lista de devoluções/refunds
    return resp

# --- Cobrança com vencimento (CobV) ---
def payload_criacao_cobv(txid, valor, chave_pix, vencimento, info_adicional=None, pagador=None):
    """
    Payload de Criação de Cobrança com Vencimento (CobV)
    """
    payload = {
        "txid": txid,
        "calendario": {"dataDeVencimento": vencimento},
        "valor": {"original": f"{valor:.2f}"},
        "chave": chave_pix,
        "solicitacaoPagador": info_adicional or "Pagamento via Pix com vencimento"
    }
    if pagador:
        payload["devedor"] = pagador
    return payload

def payload_resposta_cobv(txid, valor, chave_pix, vencimento, status="ATIVA", revisao=0, location=None, qr_code=None, pagador=None):
    """
    Payload de Resposta da Cobrança com Vencimento (CobV)
    """
    resp = {
        "txid": txid,
        "status": status,
        "calendario": {"dataDeVencimento": vencimento},
        "valor": {"original": f"{valor:.2f}"},
        "chave": chave_pix,
        "revisao": revisao
    }
    if location:
        resp["loc"] = {"id": location, "location": f"https://pix.psp/loc/{location}"}
    if qr_code:
        resp["qr_code"] = qr_code
    if pagador:
        resp["devedor"] = pagador
    return resp

# --- Lote de Cobranças com Vencimento (LoteCobV) ---
def payload_lote_cobv(lote_id, cobrancas):
    """
    Payload de Lote de Cobranças com Vencimento (LoteCobV)
    cobrancas: lista de dicts (cada um igual ao payload_criacao_cobv)
    """
    return {
        "id": lote_id,
        "cobrancas": cobrancas
    }

# --- Payload de Devolução/Refund ---
def payload_devolucao(txid, valor, id_devolucao, status="EM_PROCESSAMENTO", motivo=None):
    """
    Payload de Devolução Pix (Refund)
    """
    payload = {
        "id": id_devolucao,
        "txid": txid,
        "valor": {"devolucao": f"{valor:.2f}"},
        "status": status
    }
    if motivo:
        payload["motivo"] = motivo
    return payload

# --- Exemplos de Erro/Compliance ---
def payload_erro_pix(tipo="RequisicaoInvalida", detalhe="Erro de validação", status=400, instancia="/cob/123456"):
    """
    Payload de erro padrão Pix (compliance BACEN)
    """
    return {
        "type": f"https://pix.bcb.gov.br/api/v2/errors/{tipo}",
        "title": tipo,
        "status": status,
        "detail": detalhe,
        "instance": instancia
    }
