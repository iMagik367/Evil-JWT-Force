import os
import json
import requests
from pathlib import Path
from config.config_loader import load_config
import logging
from urllib.parse import quote
from requests.utils import requote_uri
import re

# Setup logger
logger = logging.getLogger('db_queries')
handler = logging.FileHandler('logs/db_queries.log')
formatter = logging.Formatter('[%(asctime)s] %(message)s', '%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Load API keys
config = load_config()
ext = config.get('external_apis', {})

def search_cnpj_receitaws(cnpj: str) -> dict:
    """Consulta informações de CNPJ na ReceitaWS."""
    # Input validation: must be 14 digits
    digits = re.sub(r'\D', '', cnpj)
    if len(digits) != 14:
        err = f"CNPJ inválido: deve conter 14 dígitos (recebido '{cnpj}')"
        logger.error(err)
        return {'error': err}
    key = ext.get('receitaws_key')
    url = f"https://www.receitaws.com.br/v1/cnpj/{digits}"
    headers = {'Authorization': f'Bearer {key}'} if key else {}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"ReceitaWS CNPJ search: {cnpj}")
        return data
    except Exception as e:
        logger.error(f"ReceitaWS error for CNPJ {cnpj}: {e}")
        return {'error': str(e)}

def query_brasilapi_cpf(cpf: str) -> dict:
    """Consulta informações de CPF na BrasilAPI."""
    # Input validation: must be 11 digits
    digits = re.sub(r'\D', '', cpf)
    if len(digits) != 11:
        err = f"CPF inválido: deve conter 11 dígitos (recebido '{cpf}')"
        logger.error(err)
        return {'error': err}
    # Quote CPF to handle special characters
    url = f"https://brasilapi.com.br/api/cpf/v1/{digits}"
    try:
        resp = requests.get(requote_uri(url), timeout=5)
        if resp.status_code == 404:
            error_msg = f"CPF {cpf} não encontrado"
            logger.error(f"BrasilAPI error: {error_msg}")
            return {'error': error_msg}
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"BrasilAPI CPF query: {cpf}")
        return data
    except requests.exceptions.HTTPError as e:
        error_msg = f"BrasilAPI HTTP error for CPF {cpf}: {e.response.status_code}"
        logger.error(error_msg)
        return {'error': error_msg}
    except Exception as e:
        logger.error(f"BrasilAPI error for CPF {cpf}: {e}")
        return {'error': str(e)}

def fetch_data_bacen_json(file_name: str):
    """Carrega dados abertos do Bacen a partir de arquivos JSON locais."""
    path = Path('APIs') / file_name
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded local JSON: {file_name}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON {file_name}: {e}")
        return []

def search_camara_deputados(term: str):
    """Busca registros na base da Câmara dos Deputados."""
    data = fetch_data_bacen_json('camara_deputados_2025.json')
    results = [item for item in data if any(term.lower() in str(v).lower() for v in item.values())] if isinstance(data, list) else []
    logger.info(f"Câmara Deputados search: {term}")
    return results

def query_census(term: str) -> dict:
    """Consulta dados do US Census via API."""
    key = ext.get('census_gov_key')
    # Build and quote URL to avoid invalid characters
    raw_url = f"https://api.census.gov/data/2020/acs/acs5?get=NAME&for=place:*&key={key}&in=state:*&search={quote(term)}"
    url = requote_uri(raw_url)
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 404:
            error_msg = f"Census.gov sem resultados para {term} (404)"
            logger.error(error_msg)
            return {'error': error_msg}
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"Census.gov query: {term}")
        return data
    except requests.exceptions.HTTPError as e:
        error_msg = f"Census.gov HTTP error for {term}: {e.response.status_code}"
        logger.error(error_msg)
        return {'error': error_msg}
    except Exception as e:
        logger.error(f"Census.gov error for {term}: {e}")
        return {'error': str(e)}

def check_phone_veriphone(phone: str) -> dict:
    """Valida número de telefone via Veriphone API."""
    key = ext.get('veriphone_key')
    # Validate key configuration
    if not key:
        err = 'Chave Veriphone não configurada'
        logger.error(err)
        return {'error': err}
    url = f"https://veriphone.io/v2/verify?phone={phone}&key={key}"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"Veriphone check: {phone}")
        return data
    except Exception as e:
        logger.error(f"Veriphone error for {phone}: {e}")
        return {'error': str(e)}

def check_leaks_hibp(email: str):
    """Verifica vazamentos de email via HaveIBeenPwned."""
    key = ext.get('haveibeenpwned_key')
    # Validate key configuration
    if not key or 'INSIRA' in key:
        err = 'Chave HaveIBeenPwned não configurada corretamente'
        logger.error(err)
        return {'error': err}
    headers = {'hibp-api-key': key}
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 404:
            # no breaches
            data = []
        elif resp.status_code == 401:
            err = 'Hibp.org: chave inválida ou sem permissão (401)'
            logger.error(err)
            return {'error': err}
        else:
            resp.raise_for_status()
            data = resp.json()
        logger.info(f"HIBP check: {email}")
        return data
    except Exception as e:
        logger.error(f"HIBP error for {email}: {e}")
        return {'error': str(e)}

def scrape_integration_hri_fi(term: str):
    """Busca dados de HRI.fi localmente."""
    data = fetch_data_bacen_json('hri_fi_integration.json')
    results = [item for item in data if term.lower() in json.dumps(item).lower()] if isinstance(data, list) else []
    logger.info(f"HRI.fi search: {term}")
    return results

def get_kijang_bank_data(term: str):
    """Busca dados do portal Kijang BNM."""
    data = fetch_data_bacen_json('kijang_bnm_api.json')
    results = [item for item in data if term.lower() in json.dumps(item).lower()] if isinstance(data, list) else []
    logger.info(f"Kijang BNM search: {term}")
    return results

def explore_data_gov_tw(keyword: str):
    """Explora datasets do governo de Taiwan."""
    data = fetch_data_bacen_json('data_gov_tw_datasets.json')
    results = [item for item in data if keyword.lower() in json.dumps(item).lower()] if isinstance(data, list) else []
    logger.info(f"DataGovTW search: {keyword}")
    return results 