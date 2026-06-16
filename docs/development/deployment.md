# Deployment

O sistema pode ser implantado via Docker Compose ou Kubernetes.

## Docker Compose
```bash
docker-compose build
docker-compose up -d
```

## Kubernetes (exemplo simplificado)
- Crie os manifests para os serviços (app, db, redis, nginx)
- Use ConfigMaps e Secrets para variáveis sensíveis
- Utilize um Ingress Controller para expor o serviço

## Variáveis de ambiente
Consulte o arquivo `.env.example` para todas as variáveis necessárias. 