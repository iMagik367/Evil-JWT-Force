import requests
import json
from utils.scan_utils import (
    discover_endpoints,
    fingerprint_headers,
    find_sqli_params,
    extract_pix_txids,
    guess_webhook_endpoints,
    test_jwt_tokens
)

def run_full_scan(target_url, vuln_types, dry_run=True):
    """Executa varredura completa de reconhecimento e vulnerabilidades."""
    endpoints = discover_endpoints(target_url)
    headers = fingerprint_headers(target_url)
    sqli_params = []
    jwt_test_results = {}
    pix_txids = []
    fakepix_endpoints = []

    if 'SQLi' in vuln_types:
        sqli_params = find_sqli_params(target_url)

    if 'JWT' in vuln_types:
        jwt_test_results = test_jwt_tokens(target_url)

    if 'Scan Pix / Webhooks' in vuln_types:
        pix_txids = extract_pix_txids(target_url)
        fakepix_endpoints = guess_webhook_endpoints(endpoints)

    result = {
        "endpoints": endpoints,
        "headers": headers,
        "sqli_params": sqli_params,
        "jwt_test": jwt_test_results,
        "pix_txids": pix_txids,
        "webhook_candidates": fakepix_endpoints
    }

    if not dry_run:
        import os
        os.makedirs('output', exist_ok=True)
        with open("output/scan_results.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        with open("output/fakepix_scan_cache.json", "w", encoding="utf-8") as f:
            json.dump({
                "pix_txids": pix_txids,
                "webhook_candidates": fakepix_endpoints
            }, f, indent=2)
    return result 