#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - JWT Bruteforce Test Script
This script tests the JWT bruteforce functionality.
"""

import os
import sys
import json
import time
from datetime import datetime
from modules.jwt_utils_simple import generate_token

def create_test_wordlist(filename, include_secret=True):
    """Create a test wordlist file with various password candidates"""
    words = [
        "password",
        "123456",
        "admin",
        "secret",
        "qwerty",
        "letmein",
        "test",
        "welcome",
        "password123",
        "12345678",
        "111111",
        "1234567890",
        "master",
        "access",
        "login",
        "passw0rd",
        "shadow",
        "michael",
        "superman",
        "iloveyou",
    ]
    
    # Add test_secret to ensure we have a match
    if include_secret:
        words.append("test_secret")
    
    # Write wordlist to file
    with open(filename, 'w') as f:
        for word in words:
            f.write(f"{word}\n")
    
    print(f"Created test wordlist with {len(words)} entries at {filename}")
    return filename

def main():
    """Main test function"""
    print("=== EVIL_JWT_FORCE - JWT Bruteforce Test ===")
    
    # Make sure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Create test wordlist
    wordlist_file = "output/test_bruteforce_wordlist.txt"
    create_test_wordlist(wordlist_file)
    
    # Generate a JWT token with a known secret for testing
    payload = {
        "sub": "1234567890",
        "name": "Test User",
        "iat": int(datetime.now().timestamp()),
        "exp": int(datetime.now().timestamp()) + 3600  # Valid for 1 hour
    }
    
    secret = "test_secret"
    token = generate_token(payload, secret)
    
    print(f"\nGenerated test token with secret '{secret}':")
    print(token)
    
    # Test bruteforce using python-jwt's built-in functionality
    print("\nTesting basic JWT bruteforce...")
    
    # Load wordlist
    with open(wordlist_file, 'r') as f:
        wordlist = [line.strip() for line in f]
    
    found = False
    start_time = time.time()
    attempts = 0
    
    print(f"Starting bruteforce with {len(wordlist)} candidates...")
    
    for word in wordlist:
        attempts += 1
        try:
            import jwt
            decoded = jwt.decode(token, word, algorithms=["HS256"])
            # If we get here, the signature verified successfully
            found = True
            print(f"\n[SUCCESS] Secret found after {attempts} attempts: '{word}'")
            print(f"Decoded payload: {json.dumps(decoded, indent=2)}")
            break
        except jwt.InvalidTokenError:
            # This error means wrong key/signature
            if attempts % 5 == 0:
                print(f"Tried {attempts} keys...", end="\r")
        except Exception as e:
            print(f"Error during bruteforce: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    if not found:
        print("\n[FAILED] Could not find the correct secret in wordlist.")
    
    print(f"\nBruteforce completed in {duration:.2f} seconds")
    print(f"Attempts: {attempts}")
    print(f"Speed: {attempts/duration:.2f} attempts/second")
    
    # Save results
    results = {
        "token": token,
        "secret": secret,
        "wordlist_size": len(wordlist),
        "attempts": attempts,
        "duration": duration,
        "success": found,
        "attempts_per_second": attempts/duration
    }
    
    output_file = "output/jwt_bruteforce_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 