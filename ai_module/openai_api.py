#!/usr/bin/env python3
"""
OpenAI API Module for Evil JWT Force
Provides integration with OpenAI's API for LLM capabilities
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List

class OpenAIAPI:
    """Interface para a API OpenAI"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Inicializa a API OpenAI
        
        Args:
            api_key: Chave de API da OpenAI (se None, tenta obter de OPENAI_API_KEY)
            model: Modelo a ser usado (padrão: gpt-3.5-turbo)
        """
        self.logger = logging.getLogger('OPENAI_API')
        
        # Obter API key
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            self.logger.error("API Key da OpenAI não encontrada")
            raise ValueError("API Key da OpenAI não encontrada")
        
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Verificar conexão
        self._check_connection()
    
    def _check_connection(self) -> bool:
        """
        Verifica a conexão com a API OpenAI
        
        Returns:
            bool: True se a conexão for bem-sucedida
        """
        try:
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Conexão com OpenAI ({self.model}) estabelecida com sucesso")
                return True
            else:
                self.logger.error(f"Erro na conexão com OpenAI: {response.status_code} - {response.text}")
                raise ConnectionError(f"Erro na conexão com OpenAI: {response.status_code}")
        
        except Exception as e:
            self.logger.error(f"Erro ao verificar conexão com OpenAI: {str(e)}")
            raise
    
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
            messages = []
            
            # Adicionar prompt do sistema se fornecido
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Adicionar histórico de conversa se fornecido
            if conversation_history:
                messages.extend(conversation_history)
            
            # Adicionar prompt do usuário se não estiver no histórico
            if not conversation_history or conversation_history[-1]["role"] != "user" or conversation_history[-1]["content"] != prompt:
                messages.append({
                    "role": "user",
                    "content": prompt
                })
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1000,  # Aumentado para permitir respostas mais elaboradas
                "temperature": 0.7
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return response_data["choices"][0]["message"]["content"].strip()
            else:
                self.logger.error(f"Erro na API OpenAI: {response.status_code} - {response.text}")
                return f"Erro na API: {response.status_code}"
        
        except Exception as e:
            self.logger.error(f"Erro ao obter resposta da OpenAI: {str(e)}")
            return f"Erro ao processar resposta: {str(e)}"
    
    def analyze_token(self, token: str) -> Dict[str, Any]:
        """
        Analisa um token JWT usando o modelo OpenAI
        
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
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                response_text = response_data["choices"][0]["message"]["content"].strip()
                
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
            else:
                self.logger.error(f"Erro na API OpenAI: {response.status_code} - {response.text}")
                return {
                    "valid": False,
                    "error": f"Erro na API: {response.status_code}"
                }
        
        except Exception as e:
            self.logger.error(f"Erro ao analisar token com OpenAI: {str(e)}")
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
            self.logger.error(f"Erro ao decodificar token: {str(e)}")
        
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
        """Método para desligar a API (não faz nada para OpenAI)"""
        pass 