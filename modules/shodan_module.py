import os
import requests
import json
import warnings
import logging
from typing import List, Dict, Any, Callable
from utils.network.connection_manager import ConnectionManager

# Disable SSL certificate warnings for Shodan API calls over HTTPS
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Optional: inject PyOpenSSL into urllib3 on Windows to avoid TLS errors
try:
    from urllib3.contrib import pyopenssl
    pyopenssl.inject_into_urllib3()
except Exception:
    pass

# Configuração de logging
logger = logging.getLogger(__name__)

def search_shodan(query: str, limit: int, log_callback: Callable[[str], None]) -> List[Dict[str, Any]]:
    """
    Perform a real Shodan search via REST API and return a list of match dicts.
    """
    api_key = os.environ.get('SHODAN_API_KEY')
    log_callback(f'Usando chave Shodan: {api_key}')
    
    if not api_key:
        log_callback('Chave de API do Shodan não definida. Use "Conectar Shodan" para informar.')
        return []
        
    conn = ConnectionManager(
        base_url='https://api.shodan.io',
        timeout=30,
        verify_ssl=False
    )
    
    # Debug: show full request URL
    full_url = f"/shodan/host/search?key={api_key}&query={query}&limit={limit}"
    log_callback(f'Debug: Enviando requisição GET para Shodan: {full_url}')
    
    try:
        response = conn.get('/shodan/host/search', params={
            'key': api_key,
            'query': query,
            'limit': limit
        })
        
        if isinstance(response, dict) and "error" in response:
            log_callback(f'Erro na busca Shodan: {response["error"]}')
            return []
            
        data = response if isinstance(response, dict) else json.loads(response)
        total = data.get('total', 0)
        log_callback(f'Shodan retornou {total} resultados para "{query}".')
        return data.get('matches', [])
        
    except Exception as e:
        log_callback(f'Erro na busca Shodan: {str(e)}')
        return []


def host_info(ip: str, log_callback) -> dict:
    """
    Retrieve detailed host information via REST API for a given IP address.
    """
    api_key = os.environ.get('SHODAN_API_KEY')
    if not api_key:
        log_callback('Chave de API do Shodan não definida.')
        return {}
    url = f'https://api.shodan.io/shodan/host/{ip}'
    try:
        resp = requests.get(url, params={'key': api_key}, timeout=30, verify=False)
        if resp.status_code != 200:
            log_callback(f'Erro {resp.status_code} ao obter host info: {resp.text}')
            return {}
        info = resp.json()
        log_callback(f'Informações de host carregadas para {ip}.')
        return info
    except Exception as e:
        log_callback(f'Erro ao obter informações de host Shodan: {e}')
        return {}


def test_connection(api_key: str) -> (bool, str):
    """
    Test the validity of a Shodan API key via REST API.
    """
    if not api_key:
        return False, 'Chave de API vazia.'
        url = 'https://api.shodan.io/api-info'
    try:
        resp = requests.get(url, params={'key': api_key}, timeout=15, verify=False)
        if resp.status_code == 200:
            return True, 'Conectado com sucesso'
        return False, f'Status code {resp.status_code}: {resp.text}'
    except Exception as e:
        return False, f'Erro ao testar conexão: {e}'


def get_hosts_by_country(api_key: str, country_code: str, log_callback) -> str:
    """
    Retrieve hosts for a given country code.
    """
    try:
        url = 'https://api.shodan.io/shodan/host/search'
        query = f'country:{country_code}'
        resp = requests.get(url, params={'key': api_key, 'query': query, 'limit': 100}, timeout=15)
        data = resp.json()
        matches = data.get('matches', [])
        lines = []
        for m in matches:
            ip = m.get('ip_str', '')
            isp = m.get('isp', '')
            lines.append(f"{ip} - {isp}")
        return "\n".join(lines) if lines else 'Nenhum host encontrado.'
    except Exception as e:
        return f'Erro ao obter hosts por país: {e}'


def search_exploits(api_key: str, service_name: str, log_callback) -> str:
    """
    Search Shodan Exploits for a given service name.
    """
    try:
        url = 'https://exploits.shodan.io/api/search'
        resp = requests.get(url, params={'key': api_key, 'query': service_name}, timeout=15)
        data = resp.json()
        matches = data.get('matches', [])
        lines = []
        for ex in matches:
            desc = ex.get('description', '')
            cves = ex.get('cve', [])
            cve_str = ','.join(cves) if cves else 'N/A'
            lines.append(f"{desc} (CVE: {cve_str})")
        return "\n".join(lines) if lines else 'Nenhum exploit encontrado.'
    except Exception as e:
        return f'Erro ao buscar exploits: {e}'


def scan_ports(api_key: str, ip: str, log_callback) -> str:
    """
    Scan open ports for a given IP address.
    """
    try:
        url = f'https://api.shodan.io/shodan/host/{ip}'
        resp = requests.get(url, params={'key': api_key}, timeout=15)
        data = resp.json()
        ports = data.get('ports', [])
        if not ports:
            return 'Nenhuma porta aberta encontrada.'
        return '\n'.join([f'Porta {p} aberta' for p in sorted(ports)])
    except Exception as e:
        return f'Erro ao escanear portas: {e}'


def get_technologies(api_key: str, ip: str, log_callback) -> str:
    """
    Detect technologies (server headers) for a given IP address.
    """
    try:
        url = f'https://api.shodan.io/shodan/host/{ip}'
        resp = requests.get(url, params={'key': api_key}, timeout=15)
        data = resp.json()
        techs = set()
        for d in data.get('data', []):
            http = d.get('http', {})
            server = http.get('server')
            if server:
                techs.add(server)
        return '\n'.join(sorted(techs)) if techs else 'Nenhuma tecnologia detectada.'
    except Exception as e:
        return f'Erro ao detectar tecnologias: {e}'


def get_vulnerabilities(api_key: str, ip: str, log_callback) -> str:
    """
    Retrieve known vulnerabilities (CVEs) for a given IP.
    """
    try:
        url = f'https://api.shodan.io/shodan/host/{ip}'
        resp = requests.get(url, params={'key': api_key}, timeout=15)
        data = resp.json()
        vulns = data.get('vulns', [])
        return '\n'.join(vulns) if vulns else 'Nenhuma vulnerabilidade encontrada.'
    except Exception as e:
        return f'Erro ao obter vulnerabilidades: {e}' 