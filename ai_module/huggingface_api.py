#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - Hugging Face API Integration Module
Integrates with Hugging Face Inference API to provide AI capabilities for JWT analysis
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/huggingface_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HUGGINGFACE_API')

class HuggingFaceAPI:
    """
    Interface to the Hugging Face Inference API
    Provides AI capabilities for JWT analysis and conversation
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the Hugging Face API client
        
        Args:
            api_key: Optional API key for Hugging Face (can use HF_TOKEN env var)
        """
        self.api_key = api_key or os.environ.get("HF_TOKEN")
        if not self.api_key:
            logger.warning("No Hugging Face API key provided. Some features may be limited.")
            self.api_key = ""
        
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.base_url = "https://api-inference.huggingface.co/models"
        
        # Default models - atualizados para versões disponíveis no Hugging Face
        self.default_jwt_analysis_model = "facebook/blenderbot-400M-distill"
        self.default_chat_model = "microsoft/DialoGPT-medium"
        self.default_embedding_model = "sentence-transformers/all-mpnet-base-v2"

    def analyze_token(self, token: str) -> Dict[str, Any]:
        """
        Analyze a JWT token using natural language processing
        
        Args:
            token: The JWT token to analyze
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # First, get token parts using local functions
            from modules.jwt_utils_simple import decode_token_parts
            token_parts = decode_token_parts(token)
            
            # Convert token parts to text for analysis
            token_text = f"Header: {json.dumps(token_parts.get('header', {}))}\n"
            token_text += f"Payload: {json.dumps(token_parts.get('payload', {}))}\n"
            
            # Get embeddings for the token text
            embeddings = self._get_embeddings(token_text)
            
            # Basic vulnerability checks
            vulnerabilities = []
            header = token_parts.get('header', {})
            payload = token_parts.get('payload', {})
            
            # Check algorithm vulnerabilities
            if header.get('alg') == 'none':
                vulnerabilities.append({
                    'type': 'none_algorithm', 
                    'severity': 'high',
                    'description': 'Token uses "none" algorithm which is vulnerable to signature bypass attacks'
                })
            elif header.get('alg') == 'HS256':
                vulnerabilities.append({
                    'type': 'brute_force_possible', 
                    'severity': 'medium',
                    'description': 'Token uses HS256 algorithm which may be vulnerable to brute force attacks if a weak secret is used'
                })
            
            # Check expiration
            if 'exp' not in payload:
                vulnerabilities.append({
                    'type': 'no_expiration', 
                    'severity': 'medium',
                    'description': 'Token has no expiration claim, which can lead to indefinite validity'
                })
            
            # Check for sensitive data in payload
            sensitive_fields = ['password', 'secret', 'api_key', 'apikey', 'key', 'auth', 'credential']
            found_sensitive = [field for field in sensitive_fields if any(field in key.lower() for key in payload.keys())]
            
            if found_sensitive:
                vulnerabilities.append({
                    'type': 'sensitive_data_exposure', 
                    'severity': 'high',
                    'description': f'Token contains potentially sensitive data: {", ".join(found_sensitive)}'
                })
            
            # Generate recommendations based on vulnerabilities
            recommendations = self._generate_recommendations(vulnerabilities)
            
            return {
                'valid': True,
                'header': header,
                'payload': payload,
                'vulnerabilities': vulnerabilities,
                'recommendations': recommendations,
                'embeddings': embeddings[:5] if embeddings else []  # Store first 5 dimensions of embeddings
            }
            
        except Exception as e:
            logger.error(f"Error analyzing token: {str(e)}")
            return {'valid': False, 'error': str(e), 'vulnerabilities': []}

    def chat_completion(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Get a response from the chat model
        
        Args:
            message: The user message
            history: Optional conversation history
            
        Returns:
            Model response as string
        """
        try:
            if not history:
                history = []
            
            # For free tier, we'll use a simple text completion approach
            # Format the prompt with history and current message
            prompt = self._format_chat_prompt(message, history)
            
            # Make API request to the model
            response = requests.post(
                f"{self.base_url}/{self.default_chat_model}",
                headers=self.headers,
                json={"inputs": prompt, "parameters": {"max_length": 200}}
            )
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "")
                return str(result)
            else:
                # Use fallback for errors
                logger.warning(f"Error from Hugging Face API: {response.status_code} - {response.text}")
                return self._fallback_response(message)
                
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            return self._fallback_response(message)
    
    def _get_embeddings(self, text: str) -> List[float]:
        """
        Get embeddings for the text using the embedding model
        
        Args:
            text: The text to get embeddings for
            
        Returns:
            List of embedding values
        """
        try:
            response = requests.post(
                f"{self.base_url}/{self.default_embedding_model}",
                headers=self.headers,
                json={"inputs": text}
            )
            
            if response.status_code == 200:
                embeddings = response.json()
                if isinstance(embeddings, list) and len(embeddings) > 0:
                    return embeddings[0]
                return embeddings
            else:
                logger.warning(f"Error getting embeddings: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            return []

    def _format_chat_prompt(self, message: str, history: List[Dict[str, str]]) -> str:
        """Format conversation history and message into a prompt"""
        prompt = "Você é um especialista em segurança de JWT. Responda à seguinte pergunta em português, com um tom amigável e conversacional:\n\n"
        
        # Add history
        for item in history[-5:]:  # Include only last 5 messages for context
            role = item.get("role", "")
            content = item.get("content", "")
            if role == "user":
                prompt += f"Usuário: {content}\n"
            else:
                prompt += f"Assistente: {content}\n"
        
        # Add current message
        prompt += f"Usuário: {message}\n"
        prompt += "Assistente: "
        
        return prompt

    def _fallback_response(self, message: str) -> str:
        """Provide a fallback response when API fails"""
        jwt_keywords = ["jwt", "token", "autenticação", "authentication", "header", "payload", "signature", "assinatura"]
        
        if any(keyword in message.lower() for keyword in jwt_keywords):
            return (
                "Posso te ajudar com a análise de tokens JWT! Para analisar um token, vá até a aba 'Token Analysis' "
                "e insira seu JWT. Vou verificar vulnerabilidades como algoritmos fracos, expiração ausente, e muito mais. "
                "Se precisar de alguma ajuda, estou aqui! 😊"
            )
        
        return (
            "Estou aqui para te ajudar com análise de segurança de JWT. Pode me perguntar sobre vulnerabilidades específicas, "
            "técnicas de ataque ou como proteger seus tokens. Estou com conectividade limitada no momento, mas vou fazer o "
            "meu melhor para te ajudar. O que você precisa saber? 👍"
        )
    
    def _generate_recommendations(self, vulnerabilities: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on vulnerabilities"""
        recommendations = []
        
        for vuln in vulnerabilities:
            vuln_type = vuln.get('type')
            
            if vuln_type == 'none_algorithm':
                recommendations.append(
                    "Substitua o algoritmo 'none' por um algoritmo seguro como RS256 ou ES256."
                )
                recommendations.append(
                    "Certifique-se de que seu sistema de autenticação valide corretamente as assinaturas JWT."
                )
            
            elif vuln_type == 'brute_force_possible':
                recommendations.append(
                    "Use uma chave secreta forte (pelo menos 32 caracteres) para o algoritmo HS256."
                )
                recommendations.append(
                    "Considere mudar para algoritmos assimétricos como RS256 para maior segurança."
                )
            
            elif vuln_type == 'no_expiration':
                recommendations.append(
                    "Adicione uma reivindicação de expiração ('exp') para limitar o tempo de vida do token."
                )
                recommendations.append(
                    "Implemente mecanismos de renovação de token em vez de tokens com vida longa."
                )
            
            elif vuln_type == 'sensitive_data_exposure':
                recommendations.append(
                    "Remova informações sensíveis do payload do token."
                )
                recommendations.append(
                    "Armazene apenas identificadores e permissões nos tokens, mantendo dados sensíveis no servidor."
                )
        
        # Add general recommendations
        if recommendations:
            recommendations.append(
                "Implemente uma validação adequada de tokens no seu servidor, verificando todas as reivindicações e assinaturas."
            )
        
        return recommendations 