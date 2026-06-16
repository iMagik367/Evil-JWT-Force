# Visão Geral da API

A API do sistema oferece endpoints para autenticação, análise de segurança, integração com IA, gerenciamento de usuários e RBAC.

## Principais Endpoints
- `/api/auth/*` — Autenticação e gerenciamento de tokens
- `/api/security/*` — Análise de segurança e relatórios
- `/api/ai/*` — Integração com IA
- `/api/users/*` — Gerenciamento de usuários
- `/api/rbac/*` — Gerenciamento de papéis e permissões

Todas as rotas protegidas exigem autenticação JWT. 