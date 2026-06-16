# RBAC (Controle de Acesso Baseado em Funções)

O sistema implementa RBAC para garantir que apenas usuários autorizados possam acessar recursos sensíveis.

## Papéis e Permissões
- **admin**: acesso total ao sistema
- **security_analyst**: análise de segurança e relatórios
- **viewer**: acesso somente leitura a relatórios

## Como funciona
1. Cada usuário recebe um ou mais papéis.
2. Cada papel possui permissões específicas.
3. O sistema verifica as permissões antes de executar qualquer ação sensível.

## Exemplo de verificação
```python
rbac_manager.check_permission('security_analyst', 'execute:tests')
# Retorna True se o papel tiver permissão
``` 