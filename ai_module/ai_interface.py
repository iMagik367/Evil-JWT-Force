"""
Interface para serviços de IA
"""

import logging
from typing import Dict, Any, Optional, List, Union
from utils.network.connection_manager import ConnectionManager

# Configuração de logging
logger = logging.getLogger(__name__)

class AIInterface:
    """Interface para serviços de IA"""
    
    def __init__(self, provider: str, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """
        Inicializa a interface com o provedor de IA.
        
        Args:
            provider: Nome do provedor (openai, pentest_muse, librechat)
            api_key: Chave de API (opcional)
            api_url: URL base da API (opcional)
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.api_url = api_url
        
        # Configurar headers
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            
        # Configurar gerenciador de conexão
        self.conn = ConnectionManager(
            base_url=self.api_url or self._get_default_url(),
            timeout=30,
            verify_ssl=False
        )
        self.conn.session.headers.update(self.headers)
        
    def _get_default_url(self) -> str:
        """
        Retorna a URL padrão para o provedor.
        
        Returns:
            str: URL base da API
        """
        urls = {
            "openai": "https://api.openai.com/v1",
            "pentest_muse": "https://api.pentestmuse.com/v1",
            "librechat": "https://api.librechat.com/v1"
        }
        return urls.get(self.provider, "")
        
    def _check_connection(self) -> bool:
        """
        Verifica a conexão com o provedor de IA.
        
        Returns:
            bool: True se a conexão for bem-sucedida
        """
        try:
            # Tentar uma requisição básica para verificar se a API está online
            response = self.conn.get("/health")
            
            if isinstance(response, dict) and "error" in response:
                logger.error(f"Erro na conexão com {self.provider}: {response['error']}")
                raise ConnectionError(f"Erro na conexão com {self.provider}: {response['error']}")
                
            if response.status_code < 500:
                logger.info(f"Conexão com {self.provider} estabelecida com sucesso")
                return True
            else:
                logger.error(f"Erro na conexão com {self.provider}: {response.status_code}")
                raise ConnectionError(f"Erro na conexão com {self.provider}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erro ao verificar conexão com {self.provider}: {str(e)}")
            raise ConnectionError(f"Erro ao verificar conexão com {self.provider}: {str(e)}")
            
    def generate_response(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Gera uma resposta usando o provedor de IA.
        
        Args:
            prompt: Texto de entrada
            max_tokens: Número máximo de tokens na resposta
            
        Returns:
            str: Resposta gerada
        """
        try:
            data = {
                "prompt": prompt,
                "max_tokens": max_tokens
            }
            
            response = self.conn.post("/completions", json=data)
            
            if isinstance(response, dict) and "error" in response:
                raise Exception(f"Erro ao gerar resposta: {response['error']}")
                
            if response.status_code != 200:
                raise Exception(f"Erro ao gerar resposta: HTTP {response.status_code}")
                
            result = response.json()
            return result.get("choices", [{}])[0].get("text", "")
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            raise Exception(f"Erro ao gerar resposta: {str(e)}")
            
    def analyze_jwt(self, token: str) -> Dict[str, Any]:
        """
        Analisa um token JWT usando o provedor de IA.
        
        Args:
            token: Token JWT para análise
            
        Returns:
            dict: Resultado da análise
        """
        try:
            data = {
                "token": token,
                "action": "analyze"
            }
            
            response = self.conn.post("/analyze", json=data)
            
            if isinstance(response, dict) and "error" in response:
                raise Exception(f"Erro ao analisar JWT: {response['error']}")
                
            if response.status_code != 200:
                raise Exception(f"Erro ao analisar JWT: HTTP {response.status_code}")
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao analisar JWT: {str(e)}")
            raise Exception(f"Erro ao analisar JWT: {str(e)}")
            
    def suggest_attack(self, token: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sugere um ataque baseado no token e contexto.
        
        Args:
            token: Token JWT para análise
            context: Contexto adicional para a sugestão
            
        Returns:
            dict: Sugestão de ataque
        """
        try:
            data = {
                "token": token,
                "context": context,
                "action": "suggest_attack"
            }
            
            response = self.conn.post("/suggest", json=data)
            
            if isinstance(response, dict) and "error" in response:
                raise Exception(f"Erro ao sugerir ataque: {response['error']}")
                
            if response.status_code != 200:
                raise Exception(f"Erro ao sugerir ataque: HTTP {response.status_code}")
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Erro ao sugerir ataque: {str(e)}")
            raise Exception(f"Erro ao sugerir ataque: {str(e)}")
            
    def chat_completion(self, prompt: str, system_prompt: Optional[str] = None, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Gera uma resposta de chat usando o provedor de IA.
        
        Args:
            prompt: Texto de entrada
            system_prompt: Prompt do sistema (opcional)
            conversation_history: Histórico da conversa (opcional)
            
        Returns:
            str: Resposta gerada
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                
            if conversation_history:
                messages.extend(conversation_history)
                
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "messages": messages,
                "model": "gpt-3.5-turbo" if self.provider == "openai" else "default"
            }
            
            response = self.conn.post("/chat/completions", json=data)
            
            if isinstance(response, dict) and "error" in response:
                raise Exception(f"Erro ao gerar resposta de chat: {response['error']}")
                
            if response.status_code != 200:
                raise Exception(f"Erro ao gerar resposta de chat: HTTP {response.status_code}")
                
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta de chat: {str(e)}")
            raise Exception(f"Erro ao gerar resposta de chat: {str(e)}") 