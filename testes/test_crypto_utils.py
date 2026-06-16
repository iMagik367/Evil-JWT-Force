import pytest
from unittest.mock import patch, MagicMock
import sys
import io
import base64

# Supondo que o módulo crypto_utils está em utils.crypto_utils
from utils import crypto_utils

@pytest.fixture
def plaintext():
    return b"Mensagem secreta para teste!"

@pytest.fixture
def key():
    return b"0123456789abcdef"  # 16 bytes para AES-128

@pytest.fixture
def iv():
    return b"abcdef9876543210"  # 16 bytes para CBC

@pytest.fixture
def rsa_keys():
    # Geração de chaves RSA para teste
    from Crypto.PublicKey import RSA
    key = RSA.generate(2048)
    return key.export_key(), key.publickey().export_key()

def test_aes_encrypt_decrypt(plaintext, key, iv):
    ciphertext = crypto_utils.aes_encrypt(plaintext, key, iv=iv, mode="CBC")
    decrypted = crypto_utils.aes_decrypt(ciphertext, key, iv=iv, mode="CBC")
    assert plaintext in decrypted

def test_aes_encrypt_decrypt_ecb(plaintext, key):
    ciphertext = crypto_utils.aes_encrypt(plaintext, key, mode="ECB")
    decrypted = crypto_utils.aes_decrypt(ciphertext, key, mode="ECB")
    assert plaintext in decrypted

def test_aes_encrypt_base64(plaintext, key, iv):
    ciphertext = crypto_utils.aes_encrypt(plaintext, key, iv=iv, mode="CBC", base64_output=True)
    assert isinstance(ciphertext, str)
    decrypted = crypto_utils.aes_decrypt(ciphertext, key, iv=iv, mode="CBC", base64_input=True)
    assert plaintext in decrypted

def test_rsa_encrypt_decrypt(plaintext, rsa_keys):
    priv, pub = rsa_keys
    ciphertext = crypto_utils.rsa_encrypt(plaintext, pub)
    decrypted = crypto_utils.rsa_decrypt(ciphertext, priv)
    assert plaintext == decrypted

def test_generate_random_key():
    key = crypto_utils.generate_random_key(16)
    assert isinstance(key, bytes)
    assert len(key) == 16

def test_hashing(plaintext):
    digest = crypto_utils.hash_data(plaintext, algorithm="sha256")
    assert isinstance(digest, str)
    assert len(digest) == 64

def test_crypto_utils_cli(monkeypatch, key, iv, plaintext):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(plaintext, AES.block_size))
    b64_ct = base64.b64encode(ct).decode()
    args = [
        "prog", "crypto", "--decrypt", "--ciphertext", b64_ct,
        "--key", key.hex(), "--iv", iv.hex(), "--mode", "CBC", "--base64"
    ]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("utils.crypto_utils.aes_decrypt", MagicMock(return_value=plaintext))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        crypto_utils.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "Mensagem secreta" in output or "Decriptografado" in output

def test_crypto_utils_error_handling(key):
    with pytest.raises(Exception):
        crypto_utils.aes_decrypt(b"", key, mode="ECB")

def test_file_encryption_decryption(tmp_path, plaintext, key, iv):
    file_path = tmp_path / "plain.txt"
    file_path.write_bytes(plaintext)
    enc_path = tmp_path / "enc.bin"
    dec_path = tmp_path / "dec.txt"
    crypto_utils.encrypt_file(str(file_path), str(enc_path), key, iv=iv, mode="CBC")
    crypto_utils.decrypt_file(str(enc_path), str(dec_path), key, iv=iv, mode="CBC")
    assert plaintext == dec_path.read_bytes()

if __name__ == "__main__":
    pytest.main()