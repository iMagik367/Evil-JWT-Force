#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - Simple Test Script
This script tests the basic functionality of the JWT utilities.
"""

import os
import sys
import json
from modules.jwt_utils_simple import (
    decode_jwt, 
    extract_parts, 
    generate_token, 
    generate_test_token,
    is_jwt, 
    decode_token_parts, 
    check_tools_availability
)

def test_generate_token():
    """Test token generation"""
    print("\n=== Testing Token Generation ===")
    
    # Generate a test token
    token = generate_test_token()
    print(f"Generated Token: {token}")
    
    # Create a custom token
    payload = {
        "sub": "user123",
        "name": "Test User",
        "role": "admin",
        "iat": 1516239022
    }
    
    custom_token = generate_token(payload, "mysecretkey", "HS256")
    print(f"Custom Token: {custom_token}")
    
    return token, custom_token

def test_decode_token(token):
    """Test token decoding"""
    print("\n=== Testing Token Decoding ===")
    
    # Decode without verification
    decoded = decode_jwt(token)
    print(f"Decoded token (without verification): {json.dumps(decoded, indent=2)}")
    
    # Try to decode with verification (should fail with wrong key)
    try:
        verified = decode_jwt(token, verify_signature=True, key="wrongkey", algorithm="HS256")
        print(f"Verified with wrong key (should fail): {verified}")
    except Exception as e:
        print(f"Verification failed as expected: {e}")
    
    # Extract parts
    parts = extract_parts(token)
    print(f"Token parts:")
    print(f"  Header: {json.dumps(parts['header'], indent=2)}")
    print(f"  Payload: {json.dumps(parts['payload'], indent=2)}")
    print(f"  Signature: {parts['signature']}")
    
    return decoded, parts

def test_token_analysis(token):
    """Test token analysis"""
    print("\n=== Testing Token Analysis ===")
    
    # Analyze token
    analysis = decode_token_parts(token)
    print(f"Token analysis:")
    print(f"  Algorithm: {analysis['analysis']['algorithm']}")
    print(f"  Is admin: {analysis['analysis']['is_admin']}")
    print(f"  Is expired: {analysis['analysis']['expired']}")
    
    # Test JWT validation
    is_valid = is_jwt(token)
    print(f"Is valid JWT: {is_valid}")
    
    # Test invalid token
    is_invalid = is_jwt("not.a.jwt")
    print(f"Invalid token check: {is_invalid}")
    
    return analysis

def test_tools_availability():
    """Test tools availability"""
    print("\n=== Testing Tools Availability ===")
    
    tools = check_tools_availability()
    print(f"Available tools:")
    for tool, available in tools.items():
        status = "Available" if available else "Not Available"
        print(f"  {tool}: {status}")
    
    return tools

def main():
    """Main test function"""
    print("=== EVIL_JWT_FORCE - Simple Test Script ===")
    
    # Make sure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Run all tests
    token, custom_token = test_generate_token()
    decoded, parts = test_decode_token(token)
    analysis = test_token_analysis(token)
    tools = test_tools_availability()
    
    # Save test results
    results = {
        "token": token,
        "custom_token": custom_token,
        "decoded": decoded,
        "parts": parts,
        "analysis": analysis,
        "tools": tools
    }
    
    with open("output/test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n=== Tests Completed ===")
    print(f"Results saved to: output/test_results.json")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 