"""
Headers HTTP avançados usados para requisições automatizadas e fuzzing (Kali Linux Edition).
"""

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0 EVIL_JWT_FORCE/1.2.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

AJAX_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0 EVIL_JWT_FORCE/1.2.0",
    "Accept": "*/*",
    "Referer": "https://example.com/",
    "Origin": "https://example.com",
    "Content-Type": "application/json",
    "Sec-Fetch-Mode": "cors"
}

API_HEADERS = {
    "User-Agent": "EVIL_JWT_FORCE-API/1.2.0 (Linux)",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer <TOKEN>",
    "X-API-KEY": "<API_KEY>",
    "X-Requested-With": "XMLHttpRequest"
}

AUTH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; EVIL_JWT_FORCE Auth)",
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": "Basic <BASE64_CREDENTIALS>"
}

SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "X-Content-Type-Options": "nosniff",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "no-referrer"
}

BYPASS_HEADERS = {
    "X-Original-URL": "/admin",
    "X-Rewrite-URL": "/admin",
    "X-Custom-IP-Authorization": "127.0.0.1",
    "X-Forwarded-For": "127.0.0.1",
    "X-Remote-IP": "127.0.0.1",
    "X-Originating-IP": "127.0.0.1",
    "X-Remote-Addr": "127.0.0.1",
    "X-Client-IP": "127.0.0.1",
    "X-Host": "localhost",
    "X-Forwarded-Host": "localhost"
}

FUZZ_HEADERS = {
    "User-Agent": "EVIL_JWT_FORCE-FUZZ/1.2.0 (Linux)",
    "X-Fuzz": "FUZZ",
    "X-Api-Version": "v1",
    "X-Request-ID": "<RANDOM_UUID>",
    "X-Forwarded-Proto": "https"
}