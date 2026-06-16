import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging
import json
import os
from dataclasses import dataclass

@dataclass
class User:
    id: str
    username: str
    roles: List[str]
    permissions: List[str]
    is_active: bool = True

class AuthManager:
    def __init__(self, config_path: str = "config/auth_config.json"):
        self.config_path = config_path
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        self.users: Dict[str, User] = {}
        self.setup_logging()
        self.load_config()

    def setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            filename='logs/auth.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('AuthManager')

    def load_config(self):
        """Carrega configurações de autenticação"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Carrega usuários do arquivo de configuração
                    for user_data in config.get('users', []):
                        self.users[user_data['id']] = User(**user_data)
        except Exception as e:
            self.logger.error(f"Erro ao carregar configurações: {str(e)}")

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Autentica um usuário e retorna um token JWT
        """
        # Aqui você implementaria a verificação real de senha
        # Este é apenas um exemplo simplificado
        for user in self.users.values():
            if user.username == username and user.is_active:
                return self.generate_token(user)
        return None

    def generate_token(self, user: User) -> str:
        """
        Gera um token JWT para o usuário
        """
        payload = {
            'user_id': user.id,
            'username': user.username,
            'roles': user.roles,
            'permissions': user.permissions,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verifica um token JWT e retorna o payload se válido
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token expirado")
            return None
        except jwt.InvalidTokenError:
            self.logger.warning("Token inválido")
            return None

    def has_permission(self, user_id: str, required_permission: str) -> bool:
        """
        Verifica se um usuário tem uma permissão específica
        """
        user = self.users.get(user_id)
        if not user or not user.is_active:
            return False
        return required_permission in user.permissions

    def has_role(self, user_id: str, required_role: str) -> bool:
        """
        Verifica se um usuário tem um papel específico
        """
        user = self.users.get(user_id)
        if not user or not user.is_active:
            return False
        return required_role in user.roles

    def add_user(self, user: User):
        """
        Adiciona um novo usuário
        """
        self.users[user.id] = user
        self._save_config()

    def remove_user(self, user_id: str):
        """
        Remove um usuário
        """
        if user_id in self.users:
            del self.users[user_id]
            self._save_config()

    def _save_config(self):
        """
        Salva as configurações de usuários no arquivo
        """
        try:
            config = {
                'users': [
                    {
                        'id': user.id,
                        'username': user.username,
                        'roles': user.roles,
                        'permissions': user.permissions,
                        'is_active': user.is_active
                    }
                    for user in self.users.values()
                ]
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Erro ao salvar configurações: {str(e)}") 