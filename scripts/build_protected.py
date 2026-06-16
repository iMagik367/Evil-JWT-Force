import os
import sys
import subprocess
import shutil
from typing import List, Set
import platform
import uuid
import hashlib

class ProtectedBuilder:
    def __init__(self):
        self.project_name = "EVIL_JWT_FORCE"
        self.version = "1.0.0"
        self.build_dir = "build_protected"
        self.dist_dir = "dist_protected"
        
    def _get_machine_id(self) -> str:
        """Generate a unique machine ID for license binding"""
        if platform.system() == "Windows":
            # Get Windows machine ID
            try:
                output = subprocess.check_output('wmic csproduct get uuid').decode()
                uuid_str = output.split('\n')[1].strip()
                return hashlib.sha256(uuid_str.encode()).hexdigest()
            except:
                return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()
        else:
            # Get Linux/Unix machine ID
            try:
                with open('/etc/machine-id', 'r') as f:
                    return hashlib.sha256(f.read().strip().encode()).hexdigest()
            except:
                return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()
    
    def _generate_license(self):
        """Generate a license file with machine binding"""
        machine_id = self._get_machine_id()
        license_data = {
            'machine_id': machine_id,
            'version': self.version,
            'project': self.project_name
        }
        
        # Save license file
        os.makedirs(self.build_dir, exist_ok=True)
        with open(os.path.join(self.build_dir, 'license.dat'), 'w') as f:
            f.write(str(license_data))
    
    def _encrypt_logs(self):
        """Setup encrypted logging"""
        log_dir = os.path.join(self.build_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create encrypted log handler
        with open(os.path.join(log_dir, 'encrypted_handler.py'), 'w') as f:
            f.write('''
import os
import base64
from cryptography.fernet import Fernet
from datetime import datetime

class EncryptedLogHandler:
    def __init__(self, log_file):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.log_file = log_file
        
    def write(self, message):
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp}: {message}"
        encrypted = self.cipher.encrypt(log_entry.encode())
        with open(self.log_file, 'ab') as f:
            f.write(encrypted + b'\\n')
            
    def read(self):
        with open(self.log_file, 'rb') as f:
            for line in f:
                try:
                    decrypted = self.cipher.decrypt(line.strip())
                    yield decrypted.decode()
                except:
                    continue
''')
    
    def _rename_directories(self):
        """Rename directories to generic names"""
        dir_mapping = {
            'core': 'modx',
            'modules': 'mody',
            'utils': 'modz',
            'gui': 'modw',
            'config': 'conf',
            'logs': 'logx'
        }
        
        for old_name, new_name in dir_mapping.items():
            if os.path.exists(old_name):
                os.rename(old_name, new_name)
    
    def build(self):
        """Build the protected version of the project"""
        print("Starting protected build...")
        
        # Clean previous builds
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)
        if os.path.exists(self.dist_dir):
            shutil.rmtree(self.dist_dir)
        
        # Create build directory
        os.makedirs(self.build_dir)
        
        # Generate license
        self._generate_license()
        
        # Setup encrypted logging
        self._encrypt_logs()
        
        # Run PyArmor obfuscation
        try:
            subprocess.run([
                sys.executable,
                'scripts/obfuscator.py'
            ], check=True)
        except subprocess.CalledProcessError:
            print("PyArmor obfuscation failed")
            sys.exit(1)
        
        # Run Qt obfuscation
        try:
            subprocess.run([
                sys.executable,
                'scripts/qt_obfuscator.py'
            ], check=True)
        except subprocess.CalledProcessError:
            print("Qt obfuscation failed")
            sys.exit(1)
        
        # Build with setuptools
        try:
            subprocess.run([
                sys.executable,
                'setup.py',
                'build_protected'
            ], check=True)
        except subprocess.CalledProcessError:
            print("Setuptools build failed")
            sys.exit(1)
        
        # Rename directories
        self._rename_directories()
        
        print("Protected build completed successfully!")

def main():
    builder = ProtectedBuilder()
    builder.build()

if __name__ == '__main__':
    main() 