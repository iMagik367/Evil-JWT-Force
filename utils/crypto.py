"""
Módulo utilitário para operações criptográficas avançadas, integrando crypto_utils.
"""

import logging
from modules.crypto_utils import (
    derive_key,
    generate_aes_key,
    encrypt_aes,
    decrypt_aes,
    hash_sha256,
    hash_sha512,
    hash_md5,
    brute_force_aes,
    generate_iv,
    is_printable
)

logger = logging.getLogger("utils.crypto")

def aes_encrypt(plaintext: str, password: str, salt: bytes = None, mode: str = "CBC", iv: bytes = None, key_length: int = 32) -> dict:
    """
    Criptografa um texto usando AES com derivação de chave robusta.
    """
    try:
        if not salt:
            salt = generate_iv(16)
        key = derive_key(password, salt, length=key_length)
        if not key:
            logger.error("Falha na derivação da chave AES.")
            return None
        if not iv and mode != "ECB":
            iv = generate_iv(16)
        result = encrypt_aes(plaintext, key, iv=iv, mode=mode)
        if result:
            result["salt"] = salt.hex()
        return result
    except Exception as e:
        logger.error(f"Erro ao criptografar AES: {e}")
        return None

def aes_decrypt(ciphertext_b64: str, password: str, salt: bytes, iv: bytes = None, mode: str = "CBC", key_length: int = 32) -> str:
    """
    Descriptografa um texto cifrado em base64 usando AES e derivação de chave robusta.
    """
    try:
        key = derive_key(password, salt, length=key_length)
        if not key:
            logger.error("Falha na derivação da chave AES.")
            return None
        plaintext = decrypt_aes(ciphertext_b64, key, iv=iv, mode=mode)
        if plaintext and is_printable(plaintext):
            return plaintext
        return None
    except Exception as e:
        logger.error(f"Erro ao descriptografar AES: {e}")
        return None

def aes_bruteforce(ciphertext_b64: str, passphrases: list, salts: list, ivs: list, mode: str = "CBC", key_lengths=(16, 24, 32)):
    """
    Realiza brute force AES usando lista de senhas, sais e IVs.
    """
    try:
        return brute_force_aes(ciphertext_b64, passphrases, salts, ivs, mode=mode, key_lengths=key_lengths)
    except Exception as e:
        logger.error(f"Erro no brute force AES: {e}")
        return []

def sha256_hash(data):
    return hash_sha256(data)

def sha512_hash(data):
    return hash_sha512(data)

def md5_hash(data):
    return hash_md5(data)