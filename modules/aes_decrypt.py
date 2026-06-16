import base64
import os
import logging
import json
from hashlib import pbkdf2_hmac, sha256, md5
from itertools import product, chain
from termcolor import colored
from Crypto.Util.Padding import unpad

# Importar biblioteca de criptografia com fallback
try:
    from Crypto.Cipher import AES
except ImportError:
    try:
        from Cryptodome.Cipher import AES
    except ImportError:
        print("Nem Crypto nem Cryptodome estão disponíveis. Usando implementação alternativa.")
        # Implementação simplificada para testes
        class AES:
            MODE_CBC = 2
            MODE_ECB = 1
            
            @staticmethod
            def new(key, mode, iv=None):
                return AESCipher(key, mode, iv)
        
        class AESCipher:
            def __init__(self, key, mode, iv=None):
                self.key = key
                self.mode = mode
                self.iv = iv
            
            def decrypt(self, data):
                # Simulação de decriptação para testes
                return b"decrypted_data_simulation"
            
            def encrypt(self, data):
                # Simulação de encriptação para testes
                return b"encrypted_data_simulation"

logging.basicConfig(filename='logs/aes_decrypt.log', level=logging.INFO, format='[%(asctime)s] %(message)s')

MODES = {
    "CBC": AES.MODE_CBC,
    "CFB": AES.MODE_CFB,
    "OFB": AES.MODE_OFB,
    "ECB": AES.MODE_ECB,
    "CTR": AES.MODE_CTR
}

def mutate_passphrases(passphrases):
    mutations = set()
    for p in passphrases:
        mutations.add(p)
        mutations.add(p.lower())
        mutations.add(p.upper())
        mutations.add(p.capitalize())
        mutations.add(p[::-1])
        mutations.add(p + "123")
        mutations.add("123" + p)
        mutations.add(p + "!")
        mutations.add(p + "@")
        mutations.add(p + "#")
        mutations.add(p + "$")
        mutations.add(p + "2024")
        mutations.add(p.replace("a", "@"))
        mutations.add(p.replace("o", "0"))
        mutations.add(p.replace("i", "1"))
        mutations.add(p.replace("e", "3"))
        mutations.add(sha256(p.encode()).hexdigest())
        mutations.add(md5(p.encode()).hexdigest())
    return list(mutations)

def try_decrypt(ciphertext_b64, passphrases, salts, ivs, modes=None, key_lengths=(16, 24, 32)):
    resultados = []
    try:
        ciphertext = base64.b64decode(ciphertext_b64)
    except Exception as e:
        logging.error(f"Erro ao decodificar Base64: {e}")
        return []

    if not modes:
        modes = ["CBC", "CFB", "OFB", "ECB"]

    passphrases = mutate_passphrases(passphrases)

    for passphrase in passphrases:
        for salt in salts:
            for key_len in key_lengths:
                try:
                    key = pbkdf2_hmac('sha256', passphrase.encode(), salt, 100000, dklen=key_len)
                except Exception as e:
                    logging.debug(f"Falha ao derivar chave: {e}")
                    continue
                for mode_name in modes:
                    mode = MODES.get(mode_name)
                    if not mode:
                        continue
                    iv_iter = ivs if mode != AES.MODE_ECB else [b'']
                    for iv in iv_iter:
                        try:
                            if mode == AES.MODE_ECB:
                                cipher = AES.new(key, mode)
                            elif mode == AES.MODE_CTR:
                                cipher = AES.new(key, mode, nonce=iv[:8])
                            else:
                                cipher = AES.new(key, mode, iv=iv)
                            decrypted = cipher.decrypt(ciphertext)
                            # Tenta diferentes paddings
                            try:
                                plaintext = unpad(decrypted, AES.block_size).decode('utf-8')
                            except Exception:
                                try:
                                    plaintext = decrypted.decode('utf-8')
                                except Exception:
                                    continue
                            if is_printable(plaintext):
                                resultados.append({
                                    'passphrase': passphrase,
                                    'salt': salt.hex(),
                                    'iv': iv.hex() if iv else "",
                                    'mode': mode_name,
                                    'key_length': key_len,
                                    'plaintext': plaintext
                                })
                                logging.info(f"Sucesso: senha={passphrase}, salt={salt.hex()}, iv={iv.hex() if iv else ''}, modo={mode_name}, keylen={key_len}")
                        except Exception as e:
                            logging.debug(f"Falha com senha={passphrase}, salt={salt.hex()}, iv={iv.hex() if iv else ''}, modo={mode_name}, keylen={key_len} -> {e}")
                            continue
    return resultados

def is_printable(s):
    return all(32 <= ord(c) < 127 or c in '\r\n\t' for c in s)

def load_wordlist(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return [line.strip() for line in f if line.strip()]

def brute_force_aes(ciphertext_b64, wordlist_files, salts, ivs, modes=None):
    all_passphrases = set()
    for file in wordlist_files:
        all_passphrases.update(load_wordlist(file))
    return try_decrypt(ciphertext_b64, list(all_passphrases), salts, ivs, modes)

def decrypt_with_known_key(ciphertext_b64, key, iv=None, mode="CBC"):
    try:
        ciphertext = base64.b64decode(ciphertext_b64)
        mode_val = MODES.get(mode, AES.MODE_CBC)
        if mode_val == AES.MODE_ECB:
            cipher = AES.new(key, mode_val)
        elif mode_val == AES.MODE_CTR:
            cipher = AES.new(key, mode_val, nonce=iv[:8])
        else:
            cipher = AES.new(key, mode_val, iv=iv)
        decrypted = cipher.decrypt(ciphertext)
        try:
            plaintext = unpad(decrypted, AES.block_size).decode('utf-8')
        except Exception:
            plaintext = decrypted.decode('utf-8')
        if is_printable(plaintext):
            return plaintext
    except Exception as e:
        logging.error(f"Erro na descriptografia direta: {e}")
    return None

def decrypt_aes(ciphertext_b64, passphrases, salts, ivs, wordlist_files=None, modes=None):
    resultados = []
    if wordlist_files:
        resultados.extend(brute_force_aes(ciphertext_b64, wordlist_files, salts, ivs, modes))
    resultados.extend(try_decrypt(ciphertext_b64, passphrases, salts, ivs, modes))
    return resultados

class AESDecryptor:
    """
    Implementação avançada para decriptação AES com suporte a múltiplos modos e padding.
    """
    def __init__(self, key=None, iv=None):
        self.key = key or os.urandom(16)  # AES-128 por padrão
        self.iv = iv or os.urandom(16)    # IV de 16 bytes
        self.modes = {
            'ECB': AES.MODE_ECB,
            'CBC': AES.MODE_CBC
        }
        self.padding_schemes = ['PKCS7', 'ISO10126', 'ZERO', 'ANSIX923']
        
        logging.info("AESDecryptor inicializado com sucesso")
    
    def _pad_pkcs7(self, data):
        """PKCS#7 padding"""
        pad_len = 16 - (len(data) % 16)
        return data + bytes([pad_len]) * pad_len
    
    def _unpad_pkcs7(self, data):
        """Remove PKCS#7 padding"""
        pad_len = data[-1]
        if pad_len > 16:
            return data  # Padding inválido
        for i in range(1, pad_len + 1):
            if data[-i] != pad_len:
                return data  # Padding inválido
        return data[:-pad_len]
    
    def _pad_zero(self, data):
        """Zero padding"""
        pad_len = 16 - (len(data) % 16)
        return data + bytes(pad_len)
    
    def _unpad_zero(self, data):
        """Remove zero padding"""
        i = len(data) - 1
        while i >= 0 and data[i] == 0:
            i -= 1
        return data[:i+1]
    
    def _pad_ansix923(self, data):
        """ANSI X.923 padding"""
        pad_len = 16 - (len(data) % 16)
        return data + bytes(pad_len - 1) + bytes([pad_len])
    
    def _unpad_ansix923(self, data):
        """Remove ANSI X.923 padding"""
        pad_len = data[-1]
        if pad_len > 16:
            return data  # Padding inválido
        for i in range(2, pad_len + 1):
            if data[-i] != 0:
                return data  # Padding inválido
        return data[:-pad_len]
    
    def _pad_iso10126(self, data):
        """ISO 10126 padding (random bytes com o último byte sendo o tamanho)"""
        pad_len = 16 - (len(data) % 16)
        padding = os.urandom(pad_len - 1) + bytes([pad_len])
        return data + padding
    
    def _unpad_iso10126(self, data):
        """Remove ISO 10126 padding"""
        pad_len = data[-1]
        if pad_len > 16:
            return data  # Padding inválido
        return data[:-pad_len]
    
    def decrypt(self, encrypted_data, mode='CBC', padding='PKCS7', key=None, iv=None):
        try:
            key = key or self.key
            iv = iv or self.iv
            
            # Verificação de tamanho de chave
            if len(key) not in [16, 24, 32]:
                logging.error(f"Tamanho de chave inválido: {len(key)} bytes. Deve ser 16, 24 ou 32 bytes.")
                return None
            
            # Base64 decode se necessário
            if isinstance(encrypted_data, str):
                try:
                    encrypted_data = base64.b64decode(encrypted_data)
                except Exception as e:
                    logging.error(f"Erro ao decodificar base64: {e}")
                    return None
            
            # Criar cipher object
            if mode == 'CBC':
                cipher = AES.new(key, AES.MODE_CBC, iv)
            elif mode == 'ECB':
                cipher = AES.new(key, AES.MODE_ECB)
            else:
                logging.error(f"Modo AES não suportado: {mode}")
                return None
            
            # Descriptografar
            decrypted = cipher.decrypt(encrypted_data)
            
            # Remover padding
            if padding == 'PKCS7':
                decrypted = self._unpad_pkcs7(decrypted)
            elif padding == 'ISO10126':
                decrypted = self._unpad_iso10126(decrypted)
            elif padding == 'ZERO':
                decrypted = self._unpad_zero(decrypted)
            elif padding == 'ANSIX923':
                decrypted = self._unpad_ansix923(decrypted)
            else:
                logging.error(f"Esquema de padding não suportado: {padding}")
                return None
            
            logging.info(f"Decriptação bem-sucedida: {len(encrypted_data)} bytes -> {len(decrypted)} bytes")
            return decrypted
        except Exception as e:
            logging.error(f"Erro na decriptação: {e}")
            return None
    
    def decrypt_json(self, encrypted_data, mode='CBC', padding='PKCS7', key=None, iv=None):
        decrypted = self.decrypt(encrypted_data, mode, padding, key, iv)
        if not decrypted:
            return None
        
        try:
            return json.loads(decrypted)
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON: {e}")
            return None

def decrypt_aes(encrypted_data, key, iv=None, mode="CBC", padding="PKCS7"):
    """
    Função para decriptar dados AES.
    
    Args:
        encrypted_data (str/bytes): Dados criptografados
        key (bytes): Chave de descriptografia
        iv (bytes, opcional): Vetor de inicialização
        mode (str): Modo AES - 'CBC' ou 'ECB'
        padding (str): Esquema de padding - 'PKCS7', 'ISO10126', 'ZERO', 'ANSIX923'
        
    Returns:
        bytes: Dados descriptografados ou None em caso de erro
    """
    decryptor = AESDecryptor(key, iv)
    return decryptor.decrypt(encrypted_data, mode, padding)

def run_tests():
    """Função para testar a decriptação com diferentes modos e padding."""
    key = b'ThisIsA16ByteKey'
    iv = b'ThisIsA16ByteIVV'
    test_data = b'{"user":"admin","role":"user","exp":1642342800}'
    
    # Pad e criptografa para testes
    decryptor = AESDecryptor(key, iv)
    padded = decryptor._pad_pkcs7(test_data)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(padded)
    encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
    
    print(colored("[*] Executando testes de decriptação AES...", "cyan"))
    
    # Teste CBC + PKCS7
    result = decrypt_aes(encrypted, key, iv, "CBC", "PKCS7")
    if result and result == test_data:
        print(colored("[✓] Teste CBC + PKCS7: Sucesso", "green"))
    else:
        print(colored("[x] Teste CBC + PKCS7: Falha", "red"))
    
    # Teste de Base64
    result = decrypt_aes(encrypted_b64, key, iv, "CBC", "PKCS7")
    if result and result == test_data:
        print(colored("[✓] Teste Base64: Sucesso", "green"))
    else:
        print(colored("[x] Teste Base64: Falha", "red"))
    
    print(colored("[+] Testes concluídos", "cyan"))

if __name__ == "__main__":
    run_tests()