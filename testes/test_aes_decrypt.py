import pytest
from unittest.mock import patch, MagicMock
import sys
import io
import base64

# Supondo que o módulo aes_decrypt está em utils.aes_decrypt
from utils import aes_decrypt

@pytest.fixture
def key():
    return b"0123456789abcdef"  # 16 bytes para AES-128

@pytest.fixture
def iv():
    return b"abcdef9876543210"  # 16 bytes para CBC

@pytest.fixture
def plaintext():
    return b"Mensagem secreta do teste!"

@pytest.fixture
def ciphertext(key, iv, plaintext):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(plaintext, AES.block_size))
    return ct

def test_aes_decrypt_cbc_success(ciphertext, key, iv, plaintext):
    decrypted = aes_decrypt.decrypt(ciphertext, key, iv=iv, mode="CBC")
    assert plaintext in decrypted

def test_aes_decrypt_ecb_success(key, plaintext):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    cipher = AES.new(key, AES.MODE_ECB)
    ct = cipher.encrypt(pad(plaintext, AES.block_size))
    decrypted = aes_decrypt.decrypt(ct, key, mode="ECB")
    assert plaintext in decrypted

def test_aes_decrypt_invalid_key(ciphertext, iv):
    wrong_key = b"0000000000000000"
    with pytest.raises(Exception):
        aes_decrypt.decrypt(ciphertext, wrong_key, iv=iv, mode="CBC")

def test_aes_decrypt_invalid_mode(ciphertext, key, iv):
    with pytest.raises(ValueError):
        aes_decrypt.decrypt(ciphertext, key, iv=iv, mode="INVALID")

def test_aes_decrypt_base64_input(key, iv, plaintext):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(plaintext, AES.block_size))
    b64_ct = base64.b64encode(ct).decode()
    decrypted = aes_decrypt.decrypt(b64_ct, key, iv=iv, mode="CBC", base64_input=True)
    assert plaintext in decrypted

def test_aes_decrypt_file(tmp_path, key, iv, plaintext):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(plaintext, AES.block_size))
    file_path = tmp_path / "cipher.bin"
    file_path.write_bytes(ct)
    decrypted = aes_decrypt.decrypt_file(str(file_path), key, iv=iv, mode="CBC")
    assert plaintext in decrypted

def test_aes_decrypt_cli(monkeypatch, tmp_path, key, iv, plaintext):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(plaintext, AES.block_size))
    b64_ct = base64.b64encode(ct).decode()
    args = [
        "prog", "aes-decrypt", "--ciphertext", b64_ct,
        "--key", key.hex(), "--iv", iv.hex(), "--mode", "CBC", "--base64"
    ]
    sys_argv_backup = sys.argv
    sys.argv = args
    monkeypatch.setattr("utils.aes_decrypt.decrypt", MagicMock(return_value=plaintext))
    captured = io.StringIO()
    sys.stdout = captured
    try:
        aes_decrypt.main()
    except SystemExit:
        pass
    finally:
        sys.stdout = sys.__stdout__
        sys.argv = sys_argv_backup
    output = captured.getvalue()
    assert "Mensagem secreta" in output or "Decriptografado" in output

def test_aes_decrypt_error_handling(ciphertext, key):
    # Falta IV para modo CBC
    with pytest.raises(Exception):
        aes_decrypt.decrypt(ciphertext, key, mode="CBC")

def test_aes_decrypt_empty_input(key):
    with pytest.raises(Exception):
        aes_decrypt.decrypt(b"", key, mode="ECB")

if __name__ == "__main__":
    pytest.main()