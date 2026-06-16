import json
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime
import os
from dataclasses import dataclass

@dataclass
class Role:
    name: str
    permissions: Set[str]
    description: str
    is_active: bool = True

@dataclass
class Permission:
    name: str
    description: str
    resource: str
    action: str
    is_active: bool = True

class RBACManager:
    def __init__(self, config_path: str = "config/rbac_config.json"):
        self.config_path = config_path
        self.roles: Dict[str, Role] = {}
        self.permissions: Dict[str, Permission] = {}
        self.setup_logging()
        self.load_config()

    def setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            filename='logs/rbac.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('RBACManager')

    def load_config(self):
        """Carrega configurações de RBAC"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self._load_permissions(config.get('permissions', []))
                    self._load_roles(config.get('roles', []))
        except Exception as e:
            self.logger.error(f"Erro ao carregar configurações: {str(e)}")

    def _load_permissions(self, permissions_data: List[Dict]):
        """Carrega permissões do arquivo de configuração"""
        for perm_data in permissions_data:
            permission = Permission(**perm_data)
            self.permissions[permission.name] = permission

    def _load_roles(self, roles_data: List[Dict]):
        """Carrega roles do arquivo de configuração"""
        for role_data in roles_data:
            permissions = set(role_data.pop('permissions', []))
            role = Role(**role_data)
            role.permissions = permissions
            self.roles[role.name] = role

    def check_permission(self, role_name: str, permission_name: str) -> bool:
        """
        Verifica se uma role tem uma permissão específica
        """
        role = self.roles.get(role_name)
        if not role or not role.is_active:
            return False

        permission = self.permissions.get(permission_name)
        if not permission or not permission.is_active:
            return False

        return permission_name in role.permissions

    def check_resource_permission(self, role_name: str, resource: str, action: str) -> bool:
        """
        Verifica se uma role tem permissão para uma ação específica em um recurso
        """
        role = self.roles.get(role_name)
        if not role or not role.is_active:
            return False

        for perm_name in role.permissions:
            permission = self.permissions.get(perm_name)
            if (permission and permission.is_active and
                permission.resource == resource and
                permission.action == action):
                return True

        return False

    def add_role(self, role: Role):
        """
        Adiciona uma nova role
        """
        self.roles[role.name] = role
        self._save_config()
        self.logger.info(f"Role adicionada: {role.name}")

    def remove_role(self, role_name: str):
        """
        Remove uma role
        """
        if role_name in self.roles:
            del self.roles[role_name]
            self._save_config()
            self.logger.info(f"Role removida: {role_name}")

    def add_permission(self, permission: Permission):
        """
        Adiciona uma nova permissão
        """
        self.permissions[permission.name] = permission
        self._save_config()
        self.logger.info(f"Permissão adicionada: {permission.name}")

    def remove_permission(self, permission_name: str):
        """
        Remove uma permissão
        """
        if permission_name in self.permissions:
            del self.permissions[permission_name]
            # Remove a permissão de todas as roles
            for role in self.roles.values():
                role.permissions.discard(permission_name)
            self._save_config()
            self.logger.info(f"Permissão removida: {permission_name}")

    def assign_permission_to_role(self, role_name: str, permission_name: str):
        """
        Atribui uma permissão a uma role
        """
        role = self.roles.get(role_name)
        permission = self.permissions.get(permission_name)
        
        if role and permission:
            role.permissions.add(permission_name)
            self._save_config()
            self.logger.info(f"Permissão {permission_name} atribuída à role {role_name}")

    def remove_permission_from_role(self, role_name: str, permission_name: str):
        """
        Remove uma permissão de uma role
        """
        role = self.roles.get(role_name)
        if role:
            role.permissions.discard(permission_name)
            self._save_config()
            self.logger.info(f"Permissão {permission_name} removida da role {role_name}")

    def get_role_permissions(self, role_name: str) -> Set[str]:
        """
        Retorna todas as permissões de uma role
        """
        role = self.roles.get(role_name)
        return role.permissions if role else set()

    def get_permission_roles(self, permission_name: str) -> List[str]:
        """
        Retorna todas as roles que têm uma permissão específica
        """
        return [
            role_name for role_name, role in self.roles.items()
            if permission_name in role.permissions
        ]

    def _save_config(self):
        """
        Salva as configurações de RBAC no arquivo
        """
        try:
            config = {
                'permissions': [
                    {
                        'name': perm.name,
                        'description': perm.description,
                        'resource': perm.resource,
                        'action': perm.action,
                        'is_active': perm.is_active
                    }
                    for perm in self.permissions.values()
                ],
                'roles': [
                    {
                        'name': role.name,
                        'description': role.description,
                        'permissions': list(role.permissions),
                        'is_active': role.is_active
                    }
                    for role in self.roles.values()
                ]
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Erro ao salvar configurações: {str(e)}") 