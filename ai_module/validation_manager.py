import re
import json
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import os

class ValidationManager:
    def __init__(self, config_path: str = "config/validation_config.json"):
        self.config_path = config_path
        self.setup_logging()
        self.load_config()
        self.setup_validation_rules()

    def setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            filename='logs/validation.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('ValidationManager')

    def load_config(self):
        """Carrega configurações de validação"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = self._get_default_config()
        except Exception as e:
            self.logger.error(f"Erro ao carregar configurações: {str(e)}")
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Retorna configuração padrão de validação"""
        return {
            "max_string_length": 1000,
            "max_payload_size": 1048576,  # 1MB
            "allowed_file_types": [".txt", ".json", ".log"],
            "ip_pattern": r"^(\d{1,3}\.){3}\d{1,3}$",
            "url_pattern": r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$",
            "email_pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        }

    def setup_validation_rules(self):
        """Configura regras de validação"""
        self.rules = {
            "ip": re.compile(self.config["ip_pattern"]),
            "url": re.compile(self.config["url_pattern"]),
            "email": re.compile(self.config["email_pattern"])
        }

    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """
        Valida dados de entrada
        Retorna um dicionário com os resultados da validação
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }

        try:
            # Verifica campos obrigatórios
            for field in required_fields:
                if field not in data:
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"Campo obrigatório ausente: {field}")

            # Valida tamanho do payload
            if len(json.dumps(data)) > self.config["max_payload_size"]:
                validation_result["is_valid"] = False
                validation_result["errors"].append("Payload excede o tamanho máximo permitido")

            # Valida campos específicos
            for field, value in data.items():
                if isinstance(value, str):
                    # Valida comprimento da string
                    if len(value) > self.config["max_string_length"]:
                        validation_result["warnings"].append(f"Campo {field} excede o comprimento recomendado")

                    # Valida formato de IP
                    if field.endswith("_ip") and not self.rules["ip"].match(value):
                        validation_result["is_valid"] = False
                        validation_result["errors"].append(f"Formato de IP inválido em {field}")

                    # Valida formato de URL
                    if field.endswith("_url") and not self.rules["url"].match(value):
                        validation_result["is_valid"] = False
                        validation_result["errors"].append(f"Formato de URL inválido em {field}")

                    # Valida formato de email
                    if field.endswith("_email") and not self.rules["email"].match(value):
                        validation_result["is_valid"] = False
                        validation_result["errors"].append(f"Formato de email inválido em {field}")

            # Registra resultado da validação
            self._log_validation(validation_result, data)

            return validation_result

        except Exception as e:
            self.logger.error(f"Erro durante validação: {str(e)}")
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Erro durante validação: {str(e)}")
            return validation_result

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Valida um arquivo
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }

        try:
            # Verifica extensão do arquivo
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.config["allowed_file_types"]:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Tipo de arquivo não permitido: {file_ext}")

            # Verifica tamanho do arquivo
            file_size = os.path.getsize(file_path)
            if file_size > self.config["max_payload_size"]:
                validation_result["is_valid"] = False
                validation_result["errors"].append("Arquivo excede o tamanho máximo permitido")

            # Registra resultado da validação
            self._log_validation(validation_result, {"file_path": file_path})

            return validation_result

        except Exception as e:
            self.logger.error(f"Erro durante validação de arquivo: {str(e)}")
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Erro durante validação: {str(e)}")
            return validation_result

    def _log_validation(self, validation_result: Dict[str, Any], data: Dict[str, Any]):
        """
        Registra o resultado da validação
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "validation_result": validation_result,
            "data": data
        }
        
        if not validation_result["is_valid"]:
            self.logger.error(json.dumps(log_entry))
        elif validation_result["warnings"]:
            self.logger.warning(json.dumps(log_entry))
        else:
            self.logger.info(json.dumps(log_entry)) 