#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - Wordlist Generator Test Script
This script tests the wordlist generation functionality.
"""

import os
import sys
from core.wordlist_generator import generate_wordlist

def main():
    """Main test function"""
    print("=== EVIL_JWT_FORCE - Wordlist Generator Test ===")
    
    # Make sure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Generate a test wordlist
    wordlist_file = generate_wordlist(count=50, output_file="output/test_wordlist.txt")
    
    # Print the generated wordlist
    print(f"\nWordlist generated at: {wordlist_file}")
    
    # Read and display a sample of the wordlist
    with open(wordlist_file, 'r', encoding='utf-8') as f:
        words = f.read().splitlines()
    
    print(f"\nGenerated {len(words)} words. Sample:")
    for i, word in enumerate(words[:10]):
        print(f"  {i+1}. {word}")
    
    if len(words) > 10:
        print(f"  ... and {len(words) - 10} more words")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 