import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import yaml

class ConfigEncryptor:
    def __init__(self):
        # Hardcoded salt and password for KDF - these should be changed in production
        self._salt = b'EVIL_JWT_FORCE_SALT_2024'
        self._password = b'EVIL_JWT_FORCE_PASS_2024'
        self._iterations = 100000
        self._key_length = 32  # 256 bits for AES-256
        
    def _derive_key(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self._key_length,
            salt=self._salt,
            iterations=self._iterations,
            backend=default_backend()
        )
        return kdf.derive(self._password)
    
    def encrypt_config(self, config_path, output_path):
        """Encrypt a YAML config file using AES-256"""
        # Read the config file
        with open(config_path, 'r') as f:
            config_data = f.read()
            
        # Convert to bytes
        data = config_data.encode('utf-8')
        
        # Generate a random IV
        iv = os.urandom(16)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self._derive_key()),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Pad the data
        padder = algorithms.padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine IV and encrypted data
        final_data = iv + encrypted_data
        
        # Save to file
        with open(output_path, 'wb') as f:
            f.write(final_data)
            
    def decrypt_config(self, encrypted_path):
        """Decrypt an encrypted config file"""
        # Read the encrypted file
        with open(encrypted_path, 'rb') as f:
            data = f.read()
            
        # Extract IV and encrypted data
        iv = data[:16]
        encrypted_data = data[16:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self._derive_key()),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Unpad
        unpadder = algorithms.padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        # Parse YAML
        return yaml.safe_load(data.decode('utf-8'))

if __name__ == '__main__':
    # Example usage
    encryptor = ConfigEncryptor()
    encryptor.encrypt_config('config/config.yaml', 'config/config.enc') 