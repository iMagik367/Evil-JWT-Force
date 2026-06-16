import os
import sys
import subprocess
import shutil
from typing import List, Set
import base64
import zlib
import random
import string

class CodeObfuscator:
    def __init__(self):
        self.target_dirs = ['core', 'modules', 'utils', 'gui']
        self.exclude_files = {'main.py', 'cli.py', 'setup.py', 'install.py'}
        self.temp_dir = 'temp_obfuscated'
        
    def _generate_random_name(self, length: int = 8) -> str:
        """Generate a random name for obfuscation"""
        return ''.join(random.choices(string.ascii_letters, k=length))
    
    def _obfuscate_strings(self, content: str) -> str:
        """Obfuscate string literals in code"""
        # This is a simple example - in production you'd want more sophisticated obfuscation
        lines = content.split('\n')
        obfuscated_lines = []
        
        for line in lines:
            if '=' in line and ('"' in line or "'" in line):
                # Simple string obfuscation
                parts = line.split('=')
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    value = parts[1].strip()
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        # Encode string
                        str_value = value[1:-1]
                        encoded = base64.b85encode(zlib.compress(str_value.encode())).decode()
                        new_line = f"{var_name} = zlib.decompress(base64.b85decode('{encoded}')).decode()"
                        obfuscated_lines.append(new_line)
                        continue
            obfuscated_lines.append(line)
        
        return '\n'.join(obfuscated_lines)
    
    def _obfuscate_file(self, file_path: str, output_path: str):
        """Obfuscate a single Python file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add necessary imports
        imports = "import base64\nimport zlib\n"
        
        # Obfuscate strings
        obfuscated_content = self._obfuscate_strings(content)
        
        # Write obfuscated content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(imports + obfuscated_content)
    
    def _setup_pyarmor(self):
        """Setup PyArmor for obfuscation"""
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyarmor'], check=True)
        except subprocess.CalledProcessError:
            print("Failed to install PyArmor")
            sys.exit(1)
    
    def obfuscate_directory(self, directory: str):
        """Obfuscate all Python files in a directory"""
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist")
            return
        
        # Create temp directory
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Obfuscate each Python file
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py') and file not in self.exclude_files:
                    input_path = os.path.join(root, file)
                    rel_path = os.path.relpath(input_path, directory)
                    output_path = os.path.join(self.temp_dir, rel_path)
                    
                    # Create output directory if it doesn't exist
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    # Obfuscate file
                    self._obfuscate_file(input_path, output_path)
        
        # Use PyArmor to further protect the code
        self._setup_pyarmor()
        
        # Run PyArmor on the temp directory
        try:
            subprocess.run([
                'pyarmor', 'obfuscate',
                '--recursive',
                '--output', f'{directory}_protected',
                self.temp_dir
            ], check=True)
        except subprocess.CalledProcessError:
            print("PyArmor obfuscation failed")
            sys.exit(1)
        
        # Cleanup
        shutil.rmtree(self.temp_dir)
    
    def obfuscate_all(self):
        """Obfuscate all target directories"""
        for directory in self.target_dirs:
            print(f"Obfuscating {directory}...")
            self.obfuscate_directory(directory)
            print(f"Finished obfuscating {directory}")

def main():
    obfuscator = CodeObfuscator()
    obfuscator.obfuscate_all()

if __name__ == '__main__':
    main() 