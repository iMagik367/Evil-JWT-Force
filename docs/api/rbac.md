# API de RBAC

## Endpoints

### `GET /api/rbac/roles`
Lista todos os papéis disponíveis.

### `GET /api/rbac/permissions`
Lista todas as permissões disponíveis.

### `POST /api/rbac/assign`
Atribui uma permissão a um papel.

**Body:**
```json
{
  "role": "security_analyst",
  "permission": "execute:tests"
}
```

### `POST /api/rbac/check`
Verifica se um papel possui determinada permissão.

**Body:**
```json
{
  "role": "viewer",
  "permission": "read:reports"
}
```

**Resposta:**
```json
{
  "has_permission": true
}
``` 