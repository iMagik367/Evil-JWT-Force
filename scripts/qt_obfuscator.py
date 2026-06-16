import os
import sys
import subprocess
import shutil
from typing import List, Set
import base64
import zlib

class QtObfuscator:
    def __init__(self):
        self.gui_dir = 'gui'
        self.output_dir = 'gui/qt_compiled'
        self.temp_dir = 'temp_qt'
        
    def _compile_ui(self, ui_file: str, output_file: str):
        """Compile .ui file to Python using pyuic5"""
        try:
            subprocess.run([
                'pyuic5',
                ui_file,
                '-o',
                output_file
            ], check=True)
        except subprocess.CalledProcessError:
            print(f"Failed to compile {ui_file}")
            sys.exit(1)
    
    def _obfuscate_qt_class(self, content: str) -> str:
        """Obfuscate PyQt class names and methods"""
        # Replace MainWindow with WindowX
        content = content.replace('MainWindow', 'WindowX')
        
        # Obfuscate method names
        method_names = [
            'setupUi', 'retranslateUi', 'initUI', 'createWidgets',
            'setupConnections', 'handleEvent', 'processData'
        ]
        
        for method in method_names:
            new_name = f'x{base64.b85encode(method.encode()).decode()[:8]}'
            content = content.replace(method, new_name)
        
        return content
    
    def _compile_pyc(self, py_file: str, output_file: str):
        """Compile Python file to .pyc"""
        try:
            subprocess.run([
                sys.executable,
                '-m',
                'py_compile',
                py_file
            ], check=True)
            
            # Move the .pyc file
            pyc_file = py_file + 'c'
            if os.path.exists(pyc_file):
                shutil.move(pyc_file, output_file)
        except subprocess.CalledProcessError:
            print(f"Failed to compile {py_file}")
            sys.exit(1)
    
    def obfuscate_qt_interface(self):
        """Obfuscate the PyQt interface"""
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Process all .ui files
        for root, _, files in os.walk(self.gui_dir):
            for file in files:
                if file.endswith('.ui'):
                    ui_path = os.path.join(root, file)
                    rel_path = os.path.relpath(ui_path, self.gui_dir)
                    py_path = os.path.join(self.temp_dir, rel_path.replace('.ui', '.py'))
                    pyc_path = os.path.join(self.output_dir, rel_path.replace('.ui', '.pyc'))
                    
                    # Create output directory
                    os.makedirs(os.path.dirname(py_path), exist_ok=True)
                    os.makedirs(os.path.dirname(pyc_path), exist_ok=True)
                    
                    # Compile UI to Python
                    self._compile_ui(ui_path, py_path)
                    
                    # Obfuscate the generated Python
                    with open(py_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    obfuscated_content = self._obfuscate_qt_class(content)
                    
                    with open(py_path, 'w', encoding='utf-8') as f:
                        f.write(obfuscated_content)
                    
                    # Compile to .pyc
                    self._compile_pyc(py_path, pyc_path)
        
        # Cleanup
        shutil.rmtree(self.temp_dir)

def main():
    obfuscator = QtObfuscator()
    obfuscator.obfuscate_qt_interface()

if __name__ == '__main__':
    main() 