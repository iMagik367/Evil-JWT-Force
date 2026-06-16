#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Iniciando ambiente de desenvolvimento..."

# Cria diretórios necessários
mkdir -p models logs data/raw data/processed

# Instala dependências
echo -e "\n${GREEN}Instalando dependências...${NC}"
pip install -r requirements.txt

# Executa pre-commit
echo -e "\n${GREEN}Executando pre-commit...${NC}"
pre-commit install
pre-commit run --all-files

# Gera dados de treinamento
echo -e "\n${GREEN}Gerando dados de treinamento...${NC}"
python generate_training_data.py

# Treina o modelo
echo -e "\n${GREEN}Treinando modelo...${NC}"
python run_training.py

# Testa o modelo
echo -e "\n${GREEN}Testando modelo...${NC}"
python test_model.py

# Inicia a API em modo de desenvolvimento
echo -e "\n${GREEN}Iniciando API em modo de desenvolvimento...${NC}"
uvicorn ai_module.api:app --reload --host 0.0.0.0 --port 8000

echo -e "\n${GREEN}Ambiente de desenvolvimento iniciado!${NC}" 