# Autenticação

O sistema utiliza autenticação baseada em JWT (JSON Web Token) para proteger recursos e operações sensíveis.

## Fluxo de Autenticação
1. O usuário envia suas credenciais (usuário/senha) para o endpoint de login.
2. O sistema valida as credenciais e retorna um token JWT.
3. O token deve ser enviado no header Authorization em todas as requisições protegidas.

## Exemplo de uso
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "usuario",
  "password": "senha"
}
```

**Resposta:**
```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer"
}
```

Inclua o token nas requisições:
```http
GET /api/secure-data
Authorization: Bearer <jwt_token>
``` 