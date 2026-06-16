#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - Chat Manager Module
Handles multi-turn conversations with chain-of-thought prompting and fallback between LlamaAPI and HuggingFaceAPI.
"""
import logging
import time
import os
from typing import List, Dict, Any, Optional

try:
    from openai import OpenAI
except ImportError:
    print("Biblioteca 'openai' não está instalada. Instale-a com 'pip install openai'")
    exit(1)

class ChatManager:
    """Manage advanced chat sessions with history and reasoning directives."""

    def __init__(self, hf_api_key: Optional[str] = None, system_prompt: Optional[str] = None):
        self.logger = logging.getLogger('ChatManager')
        # Obter a chave da API da OpenAI
        self.api_key = os.environ.get('OPENAI_API_KEY', '')
        # Obter modelo de chat (permite customizado via variável de ambiente)
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.logger.info(f"Modelo de chat selecionado: {self.model}")
        self.client = OpenAI(api_key=self.api_key)
        self.logger.info("Cliente OpenAI inicializado.")
        # Conversation history
        self.history: List[Dict[str, str]] = []
        # System directive for chain-of-thought with clearer natural language and deep reasoning
        if system_prompt:
            self.system_prompt = system_prompt
        else:
            self.system_prompt = (
                "Você é um especialista em segurança de JWT. "
                "Forneça respostas detalhadas em linguagem natural, sem fazer perguntas ao usuário. "
                "Pense passo a passo e explique seu raciocínio de forma clara e profunda."
            )
        self.history.append({'role': 'system', 'content': self.system_prompt})

    def set_openai_api_key(self, key: str):
        # Update the OpenAI API key and reinitialize the client.
        self.api_key = key
        self.client = OpenAI(api_key=self.api_key)

    def set_chat_model(self, model_name: str):
        # Permite atualizar o modelo de chat em tempo real
        self.model = model_name
        os.environ['OPENAI_MODEL'] = model_name
        self.logger.info(f"Modelo de chat atualizado para: {model_name}")

    def set_chat_model(self, model_name: str):
        # Permite atualizar o modelo de chat em tempo real
        self.model = model_name
        os.environ['OPENAI_MODEL'] = model_name
        self.logger.info(f"Modelo de chat atualizado para: {model_name}")

    def send(self, message: str) -> str:
        """Send a user message and return the assistant's response."""
        # Append user message
        self.history.append({'role': 'user', 'content': message})
        # Try OpenAI API
        try:
            self.logger.info("Enviando mensagem à API da OpenAI...")
            start = time.time()
            # Seleciona max_tokens conforme o modelo
            def get_max_tokens(model_name):
                if '32k' in model_name:
                    return 32768
                elif '16k' in model_name:
                    return 16384
                elif 'gpt-4' in model_name:
                    return 8192
                elif 'gpt-3.5-turbo' in model_name or '3.5-turbo' in model_name:
                    return 4096
                else:
                    return 4096  # Valor seguro
            max_tokens = get_max_tokens(self.model)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=1.0
            )
            latency = time.time() - start
            response_content = response.choices[0].message.content
            self.logger.info(f"OpenAI respondeu em {latency:.2f}s")
            # Append assistant response
            self.history.append({'role': 'assistant', 'content': response_content})
            return response_content
        except Exception as e:
            self.logger.error(f"Erro ao conectar à API da OpenAI: {str(e)}")
            return f"Erro ao conectar à API da OpenAI: {str(e)}" 