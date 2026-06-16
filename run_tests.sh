#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Iniciando testes..."

# Testa a API
echo -e "\n${GREEN}Testando API...${NC}"
python test_api.py

# Testa o modelo
echo -e "\n${GREEN}Testando modelo...${NC}"
python test_model.py

# Testa o pipeline
echo -e "\n${GREEN}Testando pipeline...${NC}"
python run_pipeline.py

# Testa o ambiente de produção
echo -e "\n${GREEN}Testando ambiente de produção...${NC}"
python run_production.py

# Testa o monitoramento
echo -e "\n${GREEN}Testando monitoramento...${NC}"
python run_production_alerts.py

# Testa a API com carga
echo -e "\n${GREEN}Testando API com carga...${NC}"
python load_test.py

echo -e "\n${GREEN}Todos os testes concluídos!${NC}" 