#!/bin/bash
set -e

# Atualiza o sistema e instala dependências essenciais
sudo apt update && sudo apt install -y python3 python3-pip git build-essential libssl-dev libffi-dev python3-venv

# (Opcional) Cria um ambiente virtual isolado
python3 -m venv ~/theharvester-venv
source ~/theharvester-venv/bin/activate

# Clona o repositório (caso não esteja na pasta correta)
# git clone https://github.com/laramies/theHarvester.git
# cd theHarvester

# Instala o pacote via pip
pip install .

# Torna scripts executáveis (caso necessário)
chmod +x theHarvester.py restfulHarvest.py

# Adiciona o diretório de scripts ao PATH (caso use venv)
export PATH="$PATH:$(pwd)"

# Mensagem de sucesso
clear
echo "theHarvester instalado com sucesso! Use 'theHarvester' ou 'restfulHarvest' para executar."