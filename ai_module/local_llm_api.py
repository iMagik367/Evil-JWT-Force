#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - API Local LLM
Implementa interface com modelos locais LLaMA.cpp para processamento de linguagem natural
e análise de tokens JWT sem dependência de serviços externos.
"""

import os
import json
import logging
import subprocess
import threading
import queue
import time
import re
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/local_llm.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LOCAL_LLM_API')

class LocalLLMAPI:
    """
    Interface com modelos locais LLaMA.cpp para análise de JWT e chat
    Oferece capacidades de IA robustas sem dependência de serviços externos
    """
    
    def __init__(self, model_path=None):
        """
        Inicializa a API LLM local

        Args:
            model_path: Caminho opcional para o modelo (se None, baixará automaticamente)
        """
        # Diretório base para modelos
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        # URL base para o servidor local LLaMA.cpp
        self.api_base_url = "http://localhost:8080/v1"
        
        # Verifica se o modelo está presente ou precisa ser baixado
        self.model_path = model_path
        if not self.model_path:
            self.model_path = os.path.join(self.models_dir, "llama-2-7b-chat.gguf")
            
        # Flag para indicar se o servidor está rodando
        self.server_running = False
        self.server_process = None
        
        # Fila para armazenar a saída do servidor
        self.server_output = queue.Queue()
        
        # Inicializa o servidor se o modelo estiver disponível
        if self._ensure_model():
            self._start_server()
    
    def _ensure_model(self) -> bool:
        """
        Garante que o modelo está disponível, baixando-o se necessário
        
        Returns:
            True se o modelo estiver disponível, False caso contrário
        """
        # Verificar se o modelo já existe
        if os.path.exists(self.model_path):
            logger.info(f"Modelo encontrado em: {self.model_path}")
            return True
            
        # Se não existir, baixe um modelo pequeno por padrão
        logger.info("Modelo não encontrado. Baixando modelo LLaMA-2-7B-Chat...")
        try:
            # URL para o modelo Llama-2-7B-Chat (aproximadamente 4GB)
            model_url = "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
            
            # Informar o usuário
            print("⚠️ Baixando modelo de IA para uso local (~4GB). Isso pode levar alguns minutos...")
            
            # Baixar o modelo
            response = requests.get(model_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 * 1024  # 1MB
            
            with open(self.model_path, 'wb') as f:
                downloaded = 0
                for data in response.iter_content(block_size):
                    f.write(data)
                    downloaded += len(data)
                    
                    # Mostrar progresso
                    if total_size > 0:
                        progress = downloaded / total_size * 100
                        print(f"Download em andamento: {progress:.1f}% ({downloaded/(1024*1024):.1f}MB/{total_size/(1024*1024):.1f}MB)", end='\r')
            
            print("\nDownload concluído com sucesso!")
            logger.info(f"Modelo baixado para: {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao baixar modelo: {str(e)}")
            print(f"❌ Erro ao baixar modelo: {str(e)}")
            print("A IA funcionará em modo fallback com capacidades limitadas.")
            return False
    
    def _start_server(self):
        """Inicia o servidor LLaMA.cpp local"""
        if self.server_running:
            return
            
        # Caminho para o executável do llama.cpp
        llama_cpp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin")
        server_exe = os.path.join(llama_cpp_path, "server.exe" if os.name == 'nt' else "server")
        
        # Se o executável não existir, tente baixá-lo
        if not os.path.exists(server_exe):
            os.makedirs(llama_cpp_path, exist_ok=True)
            self._download_llama_cpp(llama_cpp_path)
        
        if not os.path.exists(server_exe):
            logger.error(f"Executável llama.cpp não encontrado em: {server_exe}")
            return
            
        try:
            # Inicie o servidor com o modelo selecionado
            logger.info(f"Iniciando servidor LLaMA.cpp com o modelo: {self.model_path}")
            
            # Comando para iniciar o servidor
            cmd = [
                server_exe,
                "--model", self.model_path,
                "--ctx-size", "2048",
                "--port", "8080",
                "--host", "127.0.0.1"
            ]
            
            # Iniciar o processo do servidor
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Inicie uma thread para monitorar a saída do servidor
            def monitor_output():
                for line in iter(self.server_process.stdout.readline, ''):
                    self.server_output.put(line.strip())
                    
                    # Verificar se o servidor está pronto
                    if "HTTP server listening" in line:
                        self.server_running = True
                        logger.info("Servidor LLaMA.cpp iniciado com sucesso!")
            
            # Inicie a thread de monitoramento
            threading.Thread(target=monitor_output, daemon=True).start()
            
            # Aguarde o servidor iniciar (máximo 30 segundos)
            timeout = 30
            start_time = time.time()
            while not self.server_running and time.time() - start_time < timeout:
                time.sleep(0.5)
                
                # Verificar se o processo terminou prematuramente
                if self.server_process.poll() is not None:
                    error_msg = ""
                    while not self.server_output.empty():
                        error_msg += self.server_output.get() + "\n"
                    
                    logger.error(f"Servidor falhou ao iniciar: {error_msg}")
                    return
            
            if not self.server_running:
                logger.error("Timeout ao iniciar o servidor")
        
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor: {str(e)}")
    
    def _download_llama_cpp(self, destination_dir):
        """Baixa o executável LLaMA.cpp compilado"""
        try:
            # Determinar URL baseado no sistema operacional
            if os.name == 'nt':  # Windows
                # URL para versão Windows (simplificado - na prática seria necessário um link real)
                url = "https://github.com/ggerganov/llama.cpp/releases/download/b1337/llama-b1337-bin-win-x64.zip"
                out_file = os.path.join(destination_dir, "llama_cpp.zip")
            else:  # Linux/macOS
                # URL para versão Linux
                url = "https://github.com/ggerganov/llama.cpp/releases/download/b1337/llama-b1337-bin-linux-x64.tar.gz"
                out_file = os.path.join(destination_dir, "llama_cpp.tar.gz")
            
            # Baixar o arquivo
            logger.info(f"Baixando LLaMA.cpp de {url}")
            response = requests.get(url)
            response.raise_for_status()
            
            with open(out_file, 'wb') as f:
                f.write(response.content)
            
            # Extrair o arquivo
            if os.name == 'nt':
                import zipfile
                with zipfile.ZipFile(out_file, 'r') as zip_ref:
                    zip_ref.extractall(destination_dir)
            else:
                import tarfile
                with tarfile.open(out_file) as tar:
                    tar.extractall(destination_dir)
            
            # Tornar os arquivos executáveis no Linux/macOS
            if os.name != 'nt':
                for file in os.listdir(destination_dir):
                    if not file.endswith('.tar.gz'):
                        file_path = os.path.join(destination_dir, file)
                        os.chmod(file_path, 0o755)
            
            logger.info(f"LLaMA.cpp baixado e extraído para {destination_dir}")
        
        except Exception as e:
            logger.error(f"Erro ao baixar LLaMA.cpp: {str(e)}")
    
    def _fallback_mode(self) -> bool:
        """Verifica se o modo fallback deve ser usado"""
        return not self.server_running
    
    def chat_completion(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Obtém uma resposta do modelo de chat
        
        Args:
            message: A mensagem do usuário
            history: Histórico opcional da conversa
            
        Returns:
            Resposta do modelo como string
        """
        if self._fallback_mode():
            return self._fallback_response(message)
            
        try:
            if not history:
                history = []
                
            # Preparar o prompt para o modelo
            formatted_messages = self._format_chat_messages(message, history)
            
            # Fazer requisição para o servidor local
            response = requests.post(
                f"{self.api_base_url}/chat/completions",
                json={
                    "model": "local-model",
                    "messages": formatted_messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            
            # Verificar se a requisição foi bem-sucedida
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                return "Desculpe, não consegui processar sua solicitação."
            else:
                logger.warning(f"Erro na API local: {response.status_code} - {response.text}")
                return self._fallback_response(message)
                
        except Exception as e:
            logger.error(f"Erro no chat completion: {str(e)}")
            return self._fallback_response(message)
    
    def analyze_token(self, token: str) -> Dict[str, Any]:
        """
        Analisa um token JWT usando processamento de linguagem natural
        
        Args:
            token: O token JWT para analisar
            
        Returns:
            Dicionário com os resultados da análise
        """
        try:
            # Primeiro, obter partes do token usando funções locais
            from modules.jwt_utils_simple import decode_token_parts
            token_parts = decode_token_parts(token)
            
            if self._fallback_mode():
                # Análise básica sem LLM
                return self._basic_token_analysis(token, token_parts)
            
            # Preparar prompt para análise de token
            header = token_parts.get('header', {})
            payload = token_parts.get('payload', {})
            
            prompt = f"""
            Analise o seguinte token JWT:
            
            Token: {token}
            
            Header: {json.dumps(header, indent=2)}
            
            Payload: {json.dumps(payload, indent=2)}
            
            Identifique as seguintes informações:
            1. Algoritmo utilizado e suas vulnerabilidades conhecidas
            2. Presença de data de expiração e verificação de validade
            3. Conteúdo sensível no payload
            4. Vulnerabilidades potenciais e vetores de ataque
            5. Recomendações de segurança
            
            Forneça uma análise detalhada em formato JSON.
            """
            
            # Fazer requisição para o servidor local
            response = requests.post(
                f"{self.api_base_url}/completions",
                json={
                    "model": "local-model",
                    "prompt": prompt,
                    "temperature": 0.2,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"Erro na API local: {response.status_code} - {response.text}")
                return self._basic_token_analysis(token, token_parts)
                
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                ai_analysis = result["choices"][0]["text"]
                
                # Extrair JSON da resposta
                json_match = re.search(r'\{.*\}', ai_analysis, re.DOTALL)
                if json_match:
                    try:
                        analysis_json = json.loads(json_match.group(0))
                        
                        # Formatar os resultados no formato esperado
                        vulnerabilities = []
                        for vuln in analysis_json.get('vulnerabilities', []):
                            vulnerabilities.append({
                                'type': vuln.get('type', 'unknown'),
                                'severity': vuln.get('severity', 'medium'),
                                'description': vuln.get('description', '')
                            })
                        
                        recommendations = analysis_json.get('recommendations', [])
                        
                        return {
                            'valid': True,
                            'header': header,
                            'payload': payload,
                            'vulnerabilities': vulnerabilities,
                            'recommendations': recommendations,
                            'ai_analysis': analysis_json
                        }
                    except json.JSONDecodeError:
                        logger.warning("Falha ao parsear JSON da análise de IA")
                
            # Fallback para análise básica se a análise da IA falhar
            return self._basic_token_analysis(token, token_parts)
            
        except Exception as e:
            logger.error(f"Erro ao analisar token: {str(e)}")
            return {'valid': False, 'error': str(e), 'vulnerabilities': []}
    
    def _basic_token_analysis(self, token: str, token_parts: Dict[str, Any]) -> Dict[str, Any]:
        """Análise básica de token sem LLM"""
        # Verificações básicas de vulnerabilidade
        vulnerabilities = []
        header = token_parts.get('header', {})
        payload = token_parts.get('payload', {})
        
        # Verificar vulnerabilidades de algoritmo
        if header.get('alg') == 'none':
            vulnerabilities.append({
                'type': 'none_algorithm', 
                'severity': 'high',
                'description': 'Token usa algoritmo "none" que é vulnerável a ataques de bypass de assinatura'
            })
        elif header.get('alg') == 'HS256':
            vulnerabilities.append({
                'type': 'brute_force_possible', 
                'severity': 'medium',
                'description': 'Token usa algoritmo HS256 que pode ser vulnerável a ataques de força bruta se uma chave fraca for usada'
            })
        
        # Verificar expiração
        if 'exp' not in payload:
            vulnerabilities.append({
                'type': 'no_expiration', 
                'severity': 'medium',
                'description': 'Token não tem claim de expiração, o que pode levar a validade indefinida'
            })
        
        # Verificar dados sensíveis no payload
        sensitive_fields = ['password', 'senha', 'secret', 'segredo', 'api_key', 'apikey', 'key', 'chave', 'auth', 'credential']
        found_sensitive = [field for field in sensitive_fields if any(field in key.lower() for key in payload.keys())]
        
        if found_sensitive:
            vulnerabilities.append({
                'type': 'sensitive_data_exposure', 
                'severity': 'high',
                'description': f'Token contém dados potencialmente sensíveis: {", ".join(found_sensitive)}'
            })
        
        # Gerar recomendações com base nas vulnerabilidades
        recommendations = []
        for vuln in vulnerabilities:
            if vuln['type'] == 'none_algorithm':
                recommendations.append("Substitua o algoritmo 'none' por um algoritmo seguro como RS256 ou ES256")
            elif vuln['type'] == 'brute_force_possible':
                recommendations.append("Use uma chave secreta forte (pelo menos 32 caracteres) para o algoritmo HS256")
            elif vuln['type'] == 'no_expiration':
                recommendations.append("Adicione uma reivindicação de expiração ('exp') para limitar o tempo de vida do token")
            elif vuln['type'] == 'sensitive_data_exposure':
                recommendations.append("Remova informações sensíveis do payload do token")
        
        # Adicionar recomendação geral
        if recommendations:
            recommendations.append("Implemente validação adequada de tokens no seu servidor, verificando todas as reivindicações e assinaturas")
        
        return {
            'valid': True,
            'header': header,
            'payload': payload,
            'vulnerabilities': vulnerabilities,
            'recommendations': recommendations
        }
    
    def _format_chat_messages(self, message: str, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Formata o histórico de chat e a mensagem atual para o formato esperado pela API"""
        formatted_messages = [
            {"role": "system", "content": "Você é um especialista em segurança de JWT. Responda às perguntas em português, com um tom amigável e conversacional. Forneça informações precisas sobre testes de segurança, análise de tokens e técnicas de ataque."}
        ]
        
        # Adicionar histórico
        for item in history[-5:]:  # Incluir apenas as últimas 5 mensagens para contexto
            role = item.get("role", "")
            content = item.get("content", "")
            formatted_messages.append({"role": role, "content": content})
        
        # Adicionar mensagem atual
        formatted_messages.append({"role": "user", "content": message})
        
        return formatted_messages
    
    def _fallback_response(self, message: str) -> str:
        """Fornece uma resposta de fallback quando a API falha"""
        jwt_keywords = ["jwt", "token", "autenticação", "authentication", "header", "payload", "signature", "assinatura"]
        
        if any(keyword in message.lower() for keyword in jwt_keywords):
            return (
                "Posso te ajudar com a análise de tokens JWT! Para analisar um token, vá até a aba 'Análise de Token' "
                "e insira seu JWT. Vou verificar vulnerabilidades como algoritmos fracos, expiração ausente, e muito mais. "
                "Se precisar de alguma ajuda, estou aqui! 😊"
            )
        
        if "ajuda" in message.lower() or "help" in message.lower():
            return (
                "Claro! Posso te ajudar com várias coisas:\n"
                "- Analisar tokens JWT\n"
                "- Escanear sites e aplicações\n"
                "- Injetar saldos falsos\n"
                "- Executar ataques personalizados\n"
                "- Descobrir senhas de tokens\n"
                "- Descriptografar JWTs\n\n"
                "É só me dizer o que você precisa! 👍"
            )
        
        if "olá" in message.lower() or "oi" in message.lower() or "ola" in message.lower():
            return (
                "Olá! Tudo bem? Como posso te ajudar com a análise de tokens JWT hoje? 😊"
            )
        
        return (
            "Estou aqui para te ajudar com análise de segurança de JWT. Pode me perguntar sobre vulnerabilidades específicas, "
            "técnicas de ataque ou como proteger seus tokens. Estou com conectividade limitada no momento, mas vou fazer o "
            "meu melhor para te ajudar. O que você precisa saber? 👍"
        )
    
    def shutdown(self):
        """Encerra o servidor local"""
        if self.server_process and self.server_process.poll() is None:
            try:
                # Tenta encerrar graciosamente primeiro
                self.server_process.terminate()
                
                # Aguarda o término (máximo 5 segundos)
                time.sleep(5)
                
                # Força o encerramento se ainda estiver em execução
                if self.server_process.poll() is None:
                    self.server_process.kill()
                
                logger.info("Servidor LLaMA.cpp encerrado")
                
            except Exception as e:
                logger.error(f"Erro ao encerrar servidor: {str(e)}")
        
        self.server_running = False 