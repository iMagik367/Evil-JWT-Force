# Este arquivo foi descontinuado.
# Utilize core/wordlist_generator.py para geração de wordlists. 

# Wrapper para compatibilidade retroativa. Use core/wordlist_generator.py para lógica principal.
from core.wordlist_generator import generate_wordlist as core_generate_wordlist

import requests
import json
import os
from typing import List, Optional
from pathlib import Path

def load_wordlist(filepath: str) -> List[str]:
    """Load a wordlist from a file."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return [line.strip() for line in f if line.strip()]

def save_wordlist(wordlist: List[str], filepath: str) -> None:
    """Save a wordlist to a file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        for word in wordlist:
            f.write(f"{word}\n")

def generate_wordlist(
    base_words: Optional[List[str]] = None,
    min_length: int = 4,
    max_length: int = 32,
    include_numbers: bool = True,
    include_special: bool = True
) -> List[str]:
    """Generate a wordlist based on input parameters."""
    wordlist = []
    
    # Add base words if provided
    if base_words:
        wordlist.extend(base_words)
    
    # Add common patterns
    patterns = [
        "admin", "root", "user", "password", "secret",
        "token", "key", "jwt", "bearer", "auth"
    ]
    wordlist.extend(patterns)
    
    # Add variations with numbers
    if include_numbers:
        for word in wordlist[:]:
            for i in range(10):
                wordlist.append(f"{word}{i}")
                wordlist.append(f"{i}{word}")
    
    # Add variations with special characters
    if include_special:
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        for word in wordlist[:]:
            for char in special_chars:
                wordlist.append(f"{word}{char}")
                wordlist.append(f"{char}{word}")
    
    # Filter by length
    wordlist = [w for w in wordlist if min_length <= len(w) <= max_length]
    
    # Remove duplicates
    return list(set(wordlist)) 