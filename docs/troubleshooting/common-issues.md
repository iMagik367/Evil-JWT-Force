# Problemas Comuns e Soluções

## Autenticação
- **Problema**: Token JWT inválido
  - **Solução**: Verifique se o token não expirou e se está sendo enviado corretamente no header Authorization

- **Problema**: Erro de permissão
  - **Solução**: Verifique se o usuário possui o papel e as permissões necessárias

## Análise de Segurança
- **Problema**: Falha na análise de tokens
  - **Solução**: Verifique se o token está em formato válido e se a chave secreta está correta

- **Problema**: Timeout em análises longas
  - **Solução**: Aumente o timeout nas configurações ou divida a análise em partes menores

## IA
- **Problema**: Erro na integração com IA
  - **Solução**: Verifique se as credenciais da API estão corretas e se o serviço está online

## Performance
- **Problema**: Sistema lento
  - **Solução**: Verifique o uso de recursos, logs e considere escalar horizontalmente

## Deployment
- **Problema**: Erro ao iniciar containers
  - **Solução**: Verifique logs do Docker e variáveis de ambiente

- **Problema**: Falha na conexão com banco de dados
  - **Solução**: Verifique credenciais e se o banco está acessível 