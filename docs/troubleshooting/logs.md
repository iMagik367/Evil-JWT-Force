# Logs e Debugging

## Estrutura de Logs
- **Application Logs**: `/var/log/app/`
- **Nginx Logs**: `/var/log/nginx/`
- **Database Logs**: `/var/log/postgresql/`
- **Docker Logs**: `docker logs <container>`

## Níveis de Log
- DEBUG: Informações detalhadas para debugging
- INFO: Confirmação de operações normais
- WARNING: Avisos sobre situações inesperadas
- ERROR: Erros que não impedem a execução
- CRITICAL: Erros críticos que impedem a execução

## Como usar logs
1. Verifique os logs relevantes para o problema
2. Procure por erros e warnings
3. Analise o contexto do erro
4. Use ferramentas como `grep` para filtrar logs

## Exemplos
```bash
# Ver logs da aplicação
tail -f /var/log/app/app.log

# Filtrar erros
grep ERROR /var/log/app/app.log

# Ver logs do Docker
docker logs -f app
``` 