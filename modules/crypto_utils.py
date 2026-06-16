"""
Funções avançadas de criptografia e descriptografia para suporte AES, hashes e manipulação de chaves.
"""

import os
import base64
import logging
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from hashlib import sha256, sha512, md5

logging.basicConfig(filename='logs/crypto_utils.log', level=logging.INFO, format='[%(asctime)s] %(message)s')

MODES = {
    "CBC": AES.MODE_CBC,
    "CFB": AES.MODE_CFB,
    "OFB": AES.MODE_OFB,
    "ECB": AES.MODE_ECB,
    "CTR": AES.MODE_CTR
}

def derive_key(password, salt, length=32, iterations=200000, hashmod=sha256):
    try:
        return PBKDF2(password, salt, dkLen=length, count=iterations, hmac_hash_module=hashmod)
    except Exception as e:
        logging.error(f"Falha na derivação de chave: {e}")
        return None

def generate_aes_key(length=32):
    return get_random_bytes(length)

def encrypt_aes(plaintext, key, iv=None, mode="CBC"):
    try:
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        mode_val = MODES.get(mode, AES.MODE_CBC)
        if mode_val == AES.MODE_ECB:
            cipher = AES.new(key, mode_val)
            ct_bytes = cipher.encrypt(pad(plaintext, AES.block_size))
        elif mode_val == AES.MODE_CTR:
            cipher = AES.new(key, mode_val)
            ct_bytes = cipher.encrypt(plaintext)
        else:
            if iv is None:
                iv = get_random_bytes(16)
            cipher = AES.new(key, mode_val, iv=iv)
            ct_bytes = cipher.encrypt(pad(plaintext, AES.block_size))
        return {
            "ciphertext": base64.b64encode(ct_bytes).decode(),
            "iv": base64.b64encode(iv).decode() if iv else None,
            "mode": mode
        }
    except Exception as e:
        logging.error(f"Falha na criptografia AES: {e}")
        return None

def decrypt_aes(ciphertext_b64, key, iv=None, mode="CBC"):
    try:
        ciphertext = base64.b64decode(ciphertext_b64)
        mode_val = MODES.get(mode, AES.MODE_CBC)
        if mode_val == AES.MODE_ECB:
            cipher = AES.new(key, mode_val)
            decrypted = cipher.decrypt(ciphertext)
            plaintext = unpad(decrypted, AES.block_size).decode('utf-8', errors='ignore')
        elif mode_val == AES.MODE_CTR:
            cipher = AES.new(key, mode_val)
            decrypted = cipher.decrypt(ciphertext)
            plaintext = decrypted.decode('utf-8', errors='ignore')
        else:
            if iv is None:
                raise ValueError("IV é obrigatório para este modo")
            cipher = AES.new(key, mode_val, iv=iv)
            decrypted = cipher.decrypt(ciphertext)
            try:
                plaintext = unpad(decrypted, AES.block_size).decode('utf-8', errors='ignore')
            except Exception:
                plaintext = decrypted.decode('utf-8', errors='ignore')
        return plaintext
    except Exception as e:
        logging.error(f"Falha na descriptografia AES: {e}")
        return None

def hash_sha256(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return sha256(data).hexdigest()

def hash_sha512(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return sha512(data).hexdigest()

def hash_md5(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return md5(data).hexdigest()

def brute_force_aes(ciphertext_b64, passphrases, salts, ivs, mode="CBC", key_lengths=(16, 24, 32)):
    resultados = []
    for passphrase in passphrases:
        for salt in salts:
            for key_len in key_lengths:
                key = derive_key(passphrase, salt, length=key_len)
                for iv in ivs:
                    plaintext = decrypt_aes(ciphertext_b64, key, iv, mode)
                    if plaintext and is_printable(plaintext):
                        resultados.append({
                            "passphrase": passphrase,
                            "salt": salt.hex(),
                            "iv": iv.hex(),
                            "mode": mode,
                            "key_length": key_len,
                            "plaintext": plaintext
                        })
    return resultados

def is_printable(s):
    return all(32 <= ord(c) < 127 or c in '\r\n\t' for c in s)

def generate_iv(length=16):
    return get_random_bytes(length)

class CryptoAnalyzer:
    def __init__(self):
        pass
    def analyze_encryption(self, token):
        # Implementação placeholder para análise de criptografia
        return {'algorithm': 'unknown', 'strength': 'unknown'}