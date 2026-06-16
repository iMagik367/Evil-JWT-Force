# Guia de Instalação

Este documento fornece instruções detalhadas para instalar e configurar o sistema de segurança com IA.

## 1. Pré-requisitos

### 1.1 Requisitos de Sistema
- Python 3.11 ou superior
- Docker e Docker Compose
- Git
- 4GB RAM mínimo
- 20GB espaço em disco
- Sistema operacional Linux/Windows/MacOS

### 1.2 Dependências Externas
- OpenAI API Key
- PostgreSQL/MongoDB
- Redis
- Shodan API Key (opcional)
- VirusTotal API Key (opcional)

## 2. Instalação

### 2.1 Clone do Repositório
```bash
git clone https://github.com/seu-usuario/evil-force-jwt.git
cd evil-force-jwt
```

### 2.2 Configuração do Ambiente Virtual
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Linux/MacOS
source venv/bin/activate
# Windows
.\venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2.3 Configuração do Docker
```bash
# Construir imagens
docker-compose build

# Iniciar serviços
docker-compose up -d
```

## 3. Configuração

### 3.1 Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações Gerais
DEBUG=False
SECRET_KEY=sua-chave-secreta
ENVIRONMENT=production

# Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_NAME=security_db
DB_USER=admin
DB_PASSWORD=sua-senha-segura

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=sua-senha-redis

# OpenAI
OPENAI_API_KEY=sua-chave-api

# JWT
JWT_SECRET_KEY=sua-chave-jwt
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=86400

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=3600

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log
```

### 3.2 Configuração do Banco de Dados
```bash
# Criar banco de dados
python manage.py db init
python manage.py db migrate
python manage.py db upgrade

# Criar usuário admin
python manage.py create_admin
```

### 3.3 Configuração do RBAC
```bash
# Carregar configurações RBAC
python manage.py load_rbac_config
```

## 4. Verificação da Instalação

### 4.1 Testes
```bash
# Executar testes
pytest

# Verificar cobertura
pytest --cov=app tests/
```

### 4.2 Verificação de Serviços
```bash
# Verificar status dos serviços
docker-compose ps

# Verificar logs
docker-compose logs
```

## 5. Configuração de Segurança

### 5.1 Certificados SSL
```bash
# Gerar certificados auto-assinados (desenvolvimento)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout private.key -out certificate.crt
```

### 5.2 Firewall
```bash
# Configurar regras de firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5432/tcp  # PostgreSQL
sudo ufw allow 6379/tcp  # Redis
```

## 6. Configuração de Backup

### 6.1 Backup do Banco de Dados
```bash
# Script de backup
#!/bin/bash
pg_dump -U admin security_db > backup_$(date +%Y%m%d).sql
```

### 6.2 Backup de Configurações
```bash
# Backup de arquivos de configuração
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/
```

## 7. Monitoramento

### 7.1 Prometheus
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'security_app'
    static_configs:
      - targets: ['localhost:8000']
```

### 7.2 Grafana
```bash
# Instalar Grafana
docker run -d -p 3000:3000 grafana/grafana
```

## 8. Troubleshooting

### 8.1 Problemas Comuns

#### Banco de Dados não Conecta
```bash
# Verificar conexão
psql -h localhost -U admin -d security_db
```

#### Redis não Responde
```bash
# Verificar status
redis-cli ping
```

#### Serviços Docker não Iniciam
```bash
# Verificar logs
docker-compose logs

# Reiniciar serviços
docker-compose down
docker-compose up -d
```

### 8.2 Logs
```bash
# Verificar logs da aplicação
tail -f app.log

# Verificar logs do sistema
journalctl -u security-app
```

## 9. Atualização

### 9.1 Atualizar Código
```bash
# Atualizar repositório
git pull origin main

# Atualizar dependências
pip install -r requirements.txt

# Reconstruir containers
docker-compose build
docker-compose up -d
```

### 9.2 Migrações
```bash
# Aplicar migrações
python manage.py db upgrade
```

## 10. Desinstalação

### 10.1 Remover Serviços
```bash
# Parar e remover containers
docker-compose down

# Remover volumes
docker-compose down -v
```

### 10.2 Limpar Dados
```bash
# Remover banco de dados
dropdb security_db

# Remover arquivos
rm -rf venv/
rm -rf __pycache__/
rm -rf .pytest_cache/
```

## 11. Suporte

Para suporte adicional:
- Abra uma issue no GitHub
- Consulte a documentação em `docs/`
- Entre em contato com a equipe de suporte 