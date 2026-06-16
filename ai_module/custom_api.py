#!/usr/bin/env python3
"""
Custom API Module for Evil JWT Force
Provides integration with custom LLM APIs
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from utils.network.connection_manager import ConnectionManager

# Configuração de logging
logger = logging.getLogger(__name__)

class CustomAPI:
    """Interface para APIs personalizadas de LLM"""
    
    def __init__(self, api_url: str, api_key: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        """
        Inicializa a interface com a API personalizada.
        
        Args:
            api_url: URL base da API
            api_key: Chave de API (opcional)
            headers: Headers adicionais (opcional)
        """
        self.api_url = api_url.rstrip('/')
        self.headers = headers or {}
        
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
            
        self.conn = ConnectionManager(
            base_url=self.api_url,
            timeout=30,
            verify_ssl=False
        )
        self.conn.session.headers.update(self.headers)
        
    def _check_connection(self) -> bool:
        """
        Verifica a conexão com a API personalizada
        
        Returns:
            bool: True se a conexão for bem-sucedida
        """
        try:
            # Tentar uma requisição básica para verificar se a API está online
            # Primeiro, tenta um endpoint de health check comum
            endpoints = ["/health", "/v1/health", "/api/health", "/"]
            
            for endpoint in endpoints:
                try:
                    response = self.conn.get(endpoint)
                    
                    if isinstance(response, dict) and "error" in response:
                        continue
                        
                    if response.status_code < 500:  # Aceitamos qualquer resposta que não seja erro do servidor
                        logger.info(f"Conexão com API personalizada estabelecida com sucesso: {self.api_url}")
                        return True
                except:
                    continue
            
            # Se nenhum endpoint de health funcionou, tenta uma requisição mínima de chat
            minimal_data = {
                "prompt": "test",
                "max_tokens": 5
            }
            
            response = self.conn.post('', json=minimal_data)
            
            if isinstance(response, dict) and "error" in response:
                logger.error(f"Erro na conexão com API personalizada: {response['error']}")
                raise ConnectionError(f"Erro na conexão com API personalizada: {response['error']}")
                
            if response.status_code < 500:
                logger.info(f"Conexão com API personalizada estabelecida com sucesso: {self.api_url}")
                return True
            else:
                logger.error(f"Erro na conexão com API personalizada: {response.status_code}")
                raise ConnectionError(f"Erro na conexão com API personalizada: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erro ao verificar conexão com API personalizada: {str(e)}")
            raise ConnectionError(f"Erro ao verificar conexão com API personalizada: {str(e)}")
            
    def generate_response(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Gera uma resposta usando a API personalizada.
        
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
            
            response = self.conn.post('', json=data)
            
            if isinstance(response, dict) and "error" in response:
                raise Exception(f"Erro ao gerar resposta: {response['error']}")
                
            if response.status_code != 200:
                raise Exception(f"Erro ao gerar resposta: HTTP {response.status_code}")
                
            result = response.json()
            return result.get('response', '')
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            raise Exception(f"Erro ao gerar resposta: {str(e)}")
            
    def analyze_jwt(self, token: str) -> Dict[str, Any]:
        """
        Analisa um token JWT usando a API personalizada.
        
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
            
            response = self.conn.post('/analyze', json=data)
            
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
            
            response = self.conn.post('/suggest', json=data)
            
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
        Envia um prompt para o modelo e retorna a resposta
        
        Args:
            prompt: Prompt do usuário
            system_prompt: Prompt do sistema (opcional)
            conversation_history: Histórico da conversa (opcional)
            
        Returns:
            str: Resposta do modelo
        """
        try:
            # Preparar dados para diferentes formatos de API
            # Primeiro formato: estilo OpenAI
            openai_format = {
                "messages": [],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            # Segundo formato: estilo simples
            simple_format = {
                "prompt": prompt,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            # Adicionar system prompt se fornecido
            if system_prompt:
                openai_format["messages"].append({
                    "role": "system", 
                    "content": system_prompt
                })
                simple_format["system_prompt"] = system_prompt
            
            # Adicionar histórico de conversa se fornecido
            if conversation_history:
                openai_format["messages"].extend(conversation_history)
                
                # Para formato simples, concatenar histórico
                history_text = ""
                for msg in conversation_history:
                    role = msg["role"]
                    content = msg["content"]
                    history_text += f"{role.capitalize()}: {content}\n"
                
                simple_format["prompt"] = f"{history_text}\nUser: {prompt}"
            
            # Adicionar prompt do usuário
            if not conversation_history or conversation_history[-1]["role"] != "user" or conversation_history[-1]["content"] != prompt:
                openai_format["messages"].append({
                    "role": "user",
                    "content": prompt
                })
            
            # Tentar primeiro formato (estilo OpenAI)
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=openai_format,
                    timeout=30
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Tentar extrair resposta no formato OpenAI
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        if "message" in response_data["choices"][0]:
                            return response_data["choices"][0]["message"]["content"].strip()
                        elif "text" in response_data["choices"][0]:
                            return response_data["choices"][0]["text"].strip()
                    
                    # Outros formatos possíveis
                    if "response" in response_data:
                        return response_data["response"].strip()
                    if "output" in response_data:
                        return response_data["output"].strip()
                    if "result" in response_data:
                        return response_data["result"].strip()
                    if "generated_text" in response_data:
                        return response_data["generated_text"].strip()
                    
                    # Se não conseguir extrair, retornar JSON completo
                    return str(response_data)
            except:
                # Se falhar, tentar segundo formato
                pass
            
            # Tentar segundo formato (estilo simples)
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=simple_format,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Tentar extrair resposta em vários formatos possíveis
                if "response" in response_data:
                    return response_data["response"].strip()
                if "output" in response_data:
                    return response_data["output"].strip()
                if "result" in response_data:
                    return response_data["result"].strip()
                if "text" in response_data:
                    return response_data["text"].strip()
                if "generated_text" in response_data:
                    return response_data["generated_text"].strip()
                
                # Se não conseguir extrair, retornar JSON completo
                return str(response_data)
            else:
                logger.error(f"Erro na API personalizada: {response.status_code} - {response.text}")
                return f"Erro na API: {response.status_code}"
        
        except Exception as e:
            logger.error(f"Erro ao obter resposta da API personalizada: {str(e)}")
            return f"Erro ao processar resposta: {str(e)}"
    
    def analyze_token(self, token: str) -> Dict[str, Any]:
        """
        Analisa um token JWT usando a API personalizada
        
        Args:
            token: Token JWT a ser analisado
            
        Returns:
            Dict: Resultado da análise
        """
        try:
            system_prompt = """
            Você é um especialista em segurança de JWT (JSON Web Tokens).
            Analise o token fornecido e identifique possíveis vulnerabilidades.
            Forneça uma resposta estruturada com os seguintes campos:
            - header: conteúdo do cabeçalho decodificado
            - payload: conteúdo do payload decodificado
            - vulnerabilities: lista de vulnerabilidades encontradas
            - recommendations: recomendações para mitigar as vulnerabilidades
            """
            
            prompt = f"Analise este token JWT: {token}"
            
            # Obter resposta da API
            response_text = self.chat_completion(prompt, system_prompt=system_prompt)
            
            # Tentar extrair JSON da resposta
            try:
                # Verificar se a resposta contém JSON
                import re
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    json_str = json_match.group(0)
                    analysis = json.loads(json_str)
                else:
                    # Processar resposta em texto para extrair informações
                    analysis = self._parse_text_response(response_text, token)
                
                # Garantir que a análise tenha os campos necessários
                analysis.setdefault("valid", True)
                analysis.setdefault("header", {})
                analysis.setdefault("payload", {})
                analysis.setdefault("vulnerabilities", [])
                analysis.setdefault("recommendations", [])
                
                return analysis
            
            except json.JSONDecodeError:
                # Se não for possível extrair JSON, processar como texto
                return self._parse_text_response(response_text, token)
        
        except Exception as e:
            logger.error(f"Erro ao analisar token com API personalizada: {str(e)}")
            return {
                "valid": False,
                "error": f"Erro ao analisar token: {str(e)}"
            }
    
    def _parse_text_response(self, text: str, token: str) -> Dict[str, Any]:
        """
        Processa uma resposta em texto para extrair informações estruturadas
        
        Args:
            text: Texto da resposta
            token: Token JWT original
            
        Returns:
            Dict: Análise estruturada
        """
        # Implementação básica para extrair informações do texto
        analysis = {
            "valid": True,
            "header": {},
            "payload": {},
            "vulnerabilities": [],
            "recommendations": []
        }
        
        # Tentar extrair partes do token manualmente
        try:
            import base64
            import json
            
            # Dividir o token em partes
            parts = token.split('.')
            if len(parts) >= 2:
                # Decodificar o cabeçalho
                header_b64 = parts[0]
                # Adicionar padding se necessário
                header_b64 += "=" * ((4 - len(header_b64) % 4) % 4)
                header_json = base64.urlsafe_b64decode(header_b64).decode('utf-8')
                analysis["header"] = json.loads(header_json)
                
                # Decodificar o payload
                payload_b64 = parts[1]
                # Adicionar padding se necessário
                payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
                analysis["payload"] = json.loads(payload_json)
        except Exception as e:
            logger.error(f"Erro ao decodificar token: {str(e)}")
        
        # Extrair vulnerabilidades do texto da resposta
        if "vulnerabilidade" in text.lower() or "vulnerability" in text.lower():
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    if "vulnerabilidade" in line.lower() or "vulnerability" in line.lower():
                        analysis["vulnerabilities"].append({
                            "type": line.strip('- *').strip(),
                            "severity": "medium"
                        })
                elif "recomendação" in line.lower() or "recommendation" in line.lower() or "sugestão" in line.lower():
                    analysis["recommendations"].append(line.strip('- *').strip())
        
        return analysis
    
    def shutdown(self):
        """Método para desligar a API (não faz nada para API personalizada)"""
        pass 