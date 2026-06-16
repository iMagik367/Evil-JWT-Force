#!/bin/bash

set -e

echo "[*] Iniciando desinstalacao do Evil JWT Force..."

echo "[*] Executando script de desinstalacao Python..."
python3 install_deps.py --uninstall

echo "[*] Removendo diretorios..."
rm -rf logs output reports

echo "[*] Desinstalacao concluida!" 