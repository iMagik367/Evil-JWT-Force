from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.build_py import build_py
import shutil
import os
import sys
from scripts.obfuscator import CodeObfuscator

class CustomInstallCommand(install):
    def run(self):
        install.run(self)
        # Copia o arquivo .bat para o Scripts do venv (Windows)
        bat_src = os.path.join(os.path.dirname(__file__), "EVIL_JWT_FORCE.bat")
        if os.path.exists(bat_src):
            if hasattr(sys, 'real_prefix'):  # virtualenv
                scripts_dir = os.path.join(sys.prefix, 'Scripts')
            else:
                scripts_dir = os.path.join(sys.base_prefix, 'Scripts')
            bat_dst = os.path.join(scripts_dir, "EVIL_JWT_FORCE.bat")
            try:
                shutil.copyfile(bat_src, bat_dst)
                print(f"Arquivo .bat copiado para {bat_dst}")
            except Exception as e:
                print(f"Falha ao copiar o .bat: {e}")

class BuildProtectedCommand(build_py):
    """Custom command to build protected version of the package"""
    def run(self):
        # First run normal build
        build_py.run(self)
        
        # Then run obfuscation
        obfuscator = CodeObfuscator()
        obfuscator.obfuscate_all()
        
        # Copy obfuscated files to build directory
        for directory in obfuscator.target_dirs:
            protected_dir = f'{directory}_protected'
            if os.path.exists(protected_dir):
                build_dir = os.path.join(self.build_lib, directory)
                if os.path.exists(build_dir):
                    for root, _, files in os.walk(protected_dir):
                        for file in files:
                            src = os.path.join(root, file)
                            dst = os.path.join(build_dir, os.path.relpath(src, protected_dir))
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            with open(src, 'rb') as f_src, open(dst, 'wb') as f_dst:
                                f_dst.write(f_src.read())

setup(
    name="EVIL_JWT_FORCE",
    version="1.0.0",
    description="Ferramenta de Teste de Segurança JWT",
    author="EVIL_JWT_FORCE Team",
    packages=find_packages(
        include=[
            "core", "core.*",
            "modules", "modules.*",
            "utils", "utils.*",
            "config", "config.*",
            "output", "output.*",
            "logs", "logs.*",
            "reports", "reports.*",
            "scripts", "scripts.*",
            "gui", "gui.*"
        ]
    ),
    include_package_data=True,
    package_data={
        "": [
            "requirements.txt",
            "README.md",
            "LICENSE",
            "config/*",
            "output/*",
            "logs/*",
            "reports/*",
            "gui/assets/*",
            "scripts/*"
        ]
    },
    install_requires=[
        "pyjwt>=2.4.0",
        "termcolor",
        "colorama",
        "cryptography>=3.4.7",
        "beautifulsoup4>=4.9.3",
        "lxml",
        "fake-useragent>=1.5.1",
        "httpx>=0.24.0",
        "pyyaml",
        "tk",  # Tkinter (pode ser necessário instalar via sistema em alguns ambientes)
        "aiohttp",
        "requests",
        "pytest",
        "Pillow",
        "tabulate",
        "rich",
        "pyinstaller",
        "pyperclip",
        "validators",
        "requests[socks]",
        "openpyxl",
        "reportlab",
        "sqlalchemy",
        "psycopg2-binary",
        "python-jose",
        "shodan",
        "censys",
        "dnspython",
        "python-whois",
        "spyse-python",
        "mitmproxy",
        "pyarmor>=7.0.0"
    ],
    python_requires=">=3.7",
    entry_points={
        'console_scripts': [
            'evil-jwt=main:main',
            'evil-jwt-force=core.cli:main',
        ],
    },
    cmdclass={
        'install': CustomInstallCommand,
        'build_protected': BuildProtectedCommand,
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Application Frameworks"
    ],
    long_description=open("README.md", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    zip_safe=False,
)