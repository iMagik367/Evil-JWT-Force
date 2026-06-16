#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - API Ollama
Implementa interface com o Ollama para processamento de linguagem natural
e análise de tokens JWT com capacidade avançada similar a ChatGPT/Gemini.
"""

import os
import json
import logging
import subprocess
import threading
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
        logging.FileHandler('logs/ollama_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('OLLAMA_API')

class OllamaAPI:
    """
    Interface com Ollama para análise de JWT e chat
    Oferece capacidades de IA avançadas similares a ChatGPT/Gemini/DeepSeek
    """
    
    def __init__(self, model_name="llama3", api_base_url="http://localhost:11434/api"):
        """
        Inicializa a API Ollama
        
        Args:
            model_name: Nome do modelo a ser usado
            api_base_url: URL base da API Ollama
        """
        self.model_name = model_name
        self.api_base_url = api_base_url
        self.ollama_installed = False
        self.ollama_running = False
        
        # Verificar se o Ollama está instalado
        self.ollama_installed = self._check_ollama_installed()
        
        # Se não estiver instalado, tentar instalar
        if not self.ollama_installed:
            self._install_ollama()
        
        # Verificar se o servidor Ollama está rodando
        self.ollama_running = self._check_ollama_running()
        
        # Se o servidor estiver rodando, verificar/baixar o modelo
        # Não fazemos isso automaticamente para permitir que o script de instalação funcione
        # O método ensure_model deve ser chamado explicitamente quando necessário
        # self._ensure_model()
    
    def _ensure_ollama(self):
        """
        Garante que o Ollama está instalado e rodando
        """
        # Verificar se o Ollama já está instalado
        if self._check_ollama_installed():
            self.ollama_installed = True
            logger.info("Ollama já está instalado")
        else:
            # Instalar Ollama
            self._install_ollama()
        
        # Verificar se o Ollama já está rodando
        if self._check_ollama_running():
            self.ollama_running = True
            logger.info("Ollama já está rodando")
        else:
            # Iniciar Ollama
            self._start_ollama()
        
        # Verificar se o modelo está disponível, caso contrário, baixá-lo
        self._ensure_model()
    
    def _check_ollama_installed(self) -> bool:
        """
        Verifica se o Ollama está instalado
        
        Returns:
            True se o Ollama estiver instalado, False caso contrário
        """
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(['where', 'ollama'], capture_output=True, text=True)
            else:  # Linux/macOS
                result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Erro ao verificar se o Ollama está instalado: {str(e)}")
            return False
    
    def _install_ollama(self):
        """
        Instala o Ollama no sistema
        """
        try:
            print("⚠️ Ollama não encontrado. Iniciando o download e instalação...")
            
            if os.name == 'nt':  # Windows
                download_url = "https://ollama.com/download/windows"
                installer_path = os.path.join(os.environ.get('TEMP', '.'), "ollama-installer.exe")
                
                # Baixar o instalador
                print("Baixando o instalador do Ollama para Windows...")
                try:
                    response = requests.get(download_url, stream=True)
                    response.raise_for_status()
                    
                    with open(installer_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    if os.path.exists(installer_path) and os.path.getsize(installer_path) > 1000000:  # Verificar se o arquivo tem pelo menos 1MB
                        print("✅ Instalador baixado com sucesso.")
                        print(f"Caminho do instalador: {installer_path}")
                        
                        # Perguntar se o usuário quer executar o instalador agora
                        print("\n" + "="*80)
                        print("INSTRUÇÕES DE INSTALAÇÃO:")
                        print("="*80)
                        print("1. Execute o instalador baixado.")
                        print("2. Siga as instruções na tela para instalar o Ollama.")
                        print("3. Após a instalação, reinicie este aplicativo.")
                        print("="*80 + "\n")
                        
                        # Abrir o explorador de arquivos no local do instalador
                        os.system(f'explorer /select,"{installer_path}"')
                        
                        # Tentar executar o instalador automaticamente
                        try:
                            print("Tentando executar o instalador automaticamente...")
                            os.startfile(installer_path)
                        except Exception as e:
                            print(f"Não foi possível executar o instalador automaticamente: {str(e)}")
                            print("Por favor, execute o instalador manualmente.")
                    else:
                        print("❌ Falha ao baixar o instalador ou arquivo corrompido.")
                        print("Por favor, visite https://ollama.com/download/windows para baixar manualmente.")
                        
                        # Abrir a página de download no navegador
                        import webbrowser
                        webbrowser.open("https://ollama.com/download/windows")
                except Exception as e:
                    print(f"❌ Erro ao baixar o instalador: {str(e)}")
                    print("Por favor, visite https://ollama.com/download/windows para baixar manualmente.")
                    
                    # Abrir a página de download no navegador
                    import webbrowser
                    webbrowser.open("https://ollama.com/download/windows")
                
                return False
            else:  # Linux/macOS
                install_cmd = 'curl -fsSL https://ollama.com/install.sh | sh'
                print(f"Executando: {install_cmd}")
                result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Ollama instalado com sucesso!")
                    self.ollama_installed = True
                    return True
                else:
                    print(f"❌ Erro ao instalar Ollama: {result.stderr}")
                    return False
        except Exception as e:
            logger.error(f"Erro ao instalar Ollama: {str(e)}")
            print(f"❌ Erro ao instalar Ollama: {str(e)}")
            return False
    
    def _check_ollama_running(self) -> bool:
        """
        Verifica se o servidor Ollama está rodando
        
        Returns:
            True se o servidor Ollama estiver rodando, False caso contrário
        """
        try:
            response = requests.get(f"{self.api_base_url}/tags", timeout=2)
            if response.status_code == 200:
                # Verificar se a resposta é válida
                data = response.json()
                if "models" in data:
                    logger.info("Servidor Ollama está rodando e respondendo corretamente")
                    return True
                else:
                    logger.warning("Servidor Ollama respondeu com código 200 mas sem dados de modelos")
                    return False
            else:
                logger.warning(f"Servidor Ollama retornou código de erro: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.info("Servidor Ollama não está rodando (ConnectionError)")
            return False
        except requests.exceptions.Timeout:
            logger.info("Timeout ao conectar ao servidor Ollama")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar se o servidor Ollama está rodando: {str(e)}")
            return False
    
    def _start_ollama(self):
        """
        Inicia o servidor Ollama
        """
        if not self.ollama_installed:
            logger.error("Ollama não está instalado")
            return
        
        try:
            # Iniciar o Ollama em um processo separado
            if os.name == 'nt':  # Windows
                self.ollama_process = subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:  # Linux/macOS
                self.ollama_process = subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                )
            
            # Esperar o servidor iniciar
            print("⏳ Iniciando o servidor Ollama...")
            start_time = time.time()
            while time.time() - start_time < 30:  # Timeout de 30 segundos
                if self._check_ollama_running():
                    self.ollama_running = True
                    print("✅ Servidor Ollama iniciado com sucesso!")
                    logger.info("Servidor Ollama iniciado com sucesso")
                    break
                time.sleep(1)
            
            if not self.ollama_running:
                print("❌ Timeout ao iniciar o servidor Ollama")
                logger.error("Timeout ao iniciar o servidor Ollama")
        except Exception as e:
            logger.error(f"Erro ao iniciar o servidor Ollama: {str(e)}")
            print(f"❌ Erro ao iniciar o servidor Ollama: {str(e)}")
    
    def _ensure_model(self):
        """
        Garante que o modelo está disponível, baixando-o se necessário
        """
        if not self.ollama_running:
            logger.error("Servidor Ollama não está rodando")
            print("❌ Servidor Ollama não está rodando. Não é possível verificar ou baixar modelos.")
            return
        
        try:
            # Verificar se o modelo já está disponível
            print(f"Verificando se o modelo {self.model_name} já está disponível...")
            response = requests.get(f"{self.api_base_url}/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "models" not in data:
                    logger.warning("Resposta da API não contém informações sobre modelos")
                    print("⚠️ Não foi possível obter a lista de modelos disponíveis.")
                    return
                    
                available_models = [model["name"] for model in data.get("models", [])]
                
                if f"{self.model_name}:latest" in available_models:
                    logger.info(f"Modelo {self.model_name} já está disponível")
                    print(f"✅ Modelo {self.model_name} já está disponível e pronto para uso.")
                    return
                else:
                    print(f"Modelo {self.model_name} não encontrado. Modelos disponíveis: {', '.join(available_models) if available_models else 'nenhum'}")
            else:
                logger.warning(f"Erro ao verificar modelos: {response.status_code}")
                print(f"⚠️ Erro ao verificar modelos disponíveis: código {response.status_code}")
            
            # Baixar o modelo
            print(f"\n⏳ Baixando o modelo {self.model_name}... (isso pode levar alguns minutos)")
            print("Este download tem aproximadamente 4GB e será feito em segundo plano.")
            print("Você pode usar a aplicação normalmente enquanto o download é concluído.")
            print("Respostas de IA avançadas estarão disponíveis assim que o download terminar.\n")
            
            try:
                # Iniciar o download em uma thread separada para não bloquear a interface
                def download_model():
                    try:
                        response = requests.post(
                            f"{self.api_base_url}/pull",
                            json={"name": self.model_name},
                            stream=True
                        )
                        
                        if response.status_code == 200:
                            for line in response.iter_lines():
                                if line:
                                    line_data = json.loads(line.decode('utf-8'))
                                    if 'status' in line_data:
                                        logger.info(f"Download status: {line_data['status']}")
                            
                            logger.info(f"Modelo {self.model_name} baixado com sucesso")
                            print(f"\n✅ Modelo {self.model_name} baixado com sucesso!")
                        else:
                            logger.error(f"Erro ao baixar modelo: {response.text}")
                            print(f"\n❌ Erro ao baixar modelo: {response.text}")
                    except Exception as e:
                        logger.error(f"Erro durante o download do modelo: {str(e)}")
                        print(f"\n❌ Erro durante o download do modelo: {str(e)}")
                
                # Iniciar o download em segundo plano
                import threading
                download_thread = threading.Thread(target=download_model, daemon=True)
                download_thread.start()
                
            except Exception as e:
                logger.error(f"Erro ao iniciar download do modelo: {str(e)}")
                print(f"❌ Erro ao iniciar download do modelo: {str(e)}")
        
        except Exception as e:
            logger.error(f"Erro ao verificar/baixar o modelo: {str(e)}")
            print(f"❌ Erro ao verificar/baixar o modelo: {str(e)}")
    
    def chat_completion(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Obtém uma resposta do modelo de chat
        
        Args:
            message: A mensagem do usuário
            history: Histórico opcional da conversa
            
        Returns:
            Resposta do modelo como string
        """
        if not self.ollama_running:
            return self._fallback_response(message)
        
        try:
            # Formatar histórico de conversa e mensagem atual
            formatted_messages = self._format_chat_messages(message, history)
            
            # Fazer requisição para o Ollama
            response = requests.post(
                f"{self.api_base_url}/chat",
                json={
                    "model": self.model_name,
                    "messages": formatted_messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500
                    }
                }
            )
            
            # Verificar se a requisição foi bem-sucedida
            if response.status_code == 200:
                result = response.json()
                if "message" in result and "content" in result["message"]:
                    return result["message"]["content"]
                return "Desculpe, não consegui processar sua solicitação."
            else:
                logger.warning(f"Erro na API Ollama: {response.status_code} - {response.text}")
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
            
            if not self.ollama_running:
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
            
            # Configurar a mensagem para o Ollama
            messages = [
                {
                    "role": "system", 
                    "content": "Você é um especialista em segurança de JWT. Analise o token fornecido e forneça informações detalhadas sobre vulnerabilidades, recomendações e vetores de ataque. Responda em formato JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Fazer requisição para o Ollama
            response = requests.post(
                f"{self.api_base_url}/chat",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.2
                    }
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"Erro na API Ollama: {response.status_code} - {response.text}")
                return self._basic_token_analysis(token, token_parts)
            
            result = response.json()
            
            if "message" in result and "content" in result["message"]:
                ai_analysis = result["message"]["content"]
                
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
    
    def _format_chat_messages(self, message: str, history: Optional[List[Dict[str, str]]]) -> List[Dict[str, str]]:
        """Formata o histórico de chat e a mensagem atual para o formato esperado pela API"""
        formatted_messages = [
            {
                "role": "system", 
                "content": "Você é um especialista em segurança de JWT. Responda às perguntas em português, com um tom amigável e conversacional. Forneça informações precisas, detalhadas e úteis sobre testes de segurança, análise de tokens e técnicas de ataque. Pense passo a passo e seja extremamente preciso e útil para o usuário."
            }
        ]
        
        # Adicionar histórico
        if history:
            for item in history[-10:]:  # Incluir até 10 mensagens do histórico para contexto
                role = item.get("role", "")
                content = item.get("content", "")
                if role and content:
                    formatted_messages.append({"role": role, "content": content})
        
        # Adicionar mensagem atual
        formatted_messages.append({"role": "user", "content": message})
        
        return formatted_messages
    
    def _fallback_response(self, message: str) -> str:
        """Fornece uma resposta de fallback quando a API falha"""
        # Palavras-chave para diferentes categorias
        jwt_keywords = ["jwt", "token", "autenticação", "authentication", "header", "payload", "signature", "assinatura"]
        function_keywords = ["função", "funcionalidade", "pode fazer", "o que faz", "como usar", "recursos", "capacidades"]
        help_keywords = ["ajuda", "help", "como", "guia", "tutorial", "instrução", "manual"]
        greeting_keywords = ["olá", "oi", "ola", "bom dia", "boa tarde", "boa noite", "e aí", "eai", "tudo bem"]
        attack_keywords = ["ataque", "attack", "exploit", "vulnerabilidade", "hacking", "invadir", "força bruta", "fuzzing"]
        
        # Verificar se o download do modelo está em andamento
        model_downloading = "Estou baixando um modelo de IA avançado para melhorar minhas respostas. " \
                           "Enquanto isso, estou usando um modo simplificado, mas já posso te ajudar com o básico. "
        
        # Funções do programa
        if any(keyword in message.lower() for keyword in function_keywords):
            return (
                "O Evil Force JWT é uma poderosa ferramenta de segurança para testar, analisar e explorar vulnerabilidades em tokens JWT. "
                "Ele oferece diversas funcionalidades:\n\n"
                "1. Análise de Tokens JWT - Examina tokens e identifica vulnerabilidades\n"
                "2. Escaneamento de Alvos - Detecta tokens JWT em aplicações web\n"
                "3. Injeção de Saldo - Permite modificar valores em tokens para testar a segurança\n"
                "4. Ataques Manuais - Executa técnicas como força bruta, fuzzing e confusão de algoritmos\n"
                "5. Extração de Dados - Recupera informações de tokens criptografados\n\n"
                "Para usar, basta selecionar a função desejada e seguir as instruções na interface. "
                "Posso te ajudar com qualquer uma dessas funcionalidades se precisar de mais detalhes!"
            )
        
        # Informações sobre JWT
        elif any(keyword in message.lower() for keyword in jwt_keywords):
            if "vulnerabilidade" in message.lower() or "vulnerável" in message.lower() or "ataque" in message.lower():
                return (
                    "Os tokens JWT podem ser vulneráveis a vários tipos de ataques, incluindo:\n\n"
                    "1. Algoritmo 'none' - Alguns sistemas aceitam tokens sem assinatura\n"
                    "2. Força bruta em chaves fracas - Especialmente com algoritmos HS256\n"
                    "3. Confusão de chaves - Troca entre algoritmos simétricos e assimétricos\n"
                    "4. Injeção de cabeçalho - Manipulação do parâmetro 'kid' para ataques de injeção\n"
                    "5. Manipulação de payload - Alteração de claims como 'exp' ou 'role'\n\n"
                    "O Evil Force JWT pode testar todas essas vulnerabilidades. Para iniciar uma análise, "
                    "vá até a aba 'Análise de Token' e insira o token que deseja verificar."
                )
            else:
                return (
                    "Os tokens JWT (JSON Web Tokens) são um padrão aberto para transmitir informações de forma segura entre partes. "
                    "Eles consistem em três partes separadas por pontos: header.payload.signature\n\n"
                    "Para analisar um token JWT com nossa ferramenta, vá até a aba 'Análise de Token' e cole o token no campo indicado. "
                    "Vou verificar vulnerabilidades como algoritmos fracos, expiração ausente, e muito mais. "
                    "Se precisar de ajuda específica com algum token, estou à disposição! 😊"
                )
        
        # Pedidos de ajuda
        elif any(keyword in message.lower() for keyword in help_keywords):
            if any(attack in message.lower() for attack in attack_keywords):
                return (
                    "Para executar ataques contra tokens JWT, você tem várias opções no Evil Force JWT:\n\n"
                    "1. Na aba 'Ataque Manual', selecione o tipo de ataque (força bruta, fuzzing, etc.)\n"
                    "2. Insira o token alvo e os parâmetros necessários\n"
                    "3. Clique em 'Executar Ataque'\n\n"
                    "A ferramenta tentará explorar vulnerabilidades e mostrará os resultados detalhados. "
                    "Se precisar de ajuda com um ataque específico, me diga qual e posso te dar instruções mais detalhadas."
                )
            else:
                return (
                    "Claro! Posso te ajudar com várias coisas no Evil Force JWT:\n\n"
                    "- Analisar tokens JWT em detalhes\n"
                    "- Escanear sites e aplicações para encontrar vulnerabilidades\n"
                    "- Injetar saldos falsos em aplicações com JWT vulneráveis\n"
                    "- Executar ataques personalizados como força bruta e fuzzing\n"
                    "- Descobrir senhas e chaves secretas de tokens\n"
                    "- Descriptografar JWTs e expor seu conteúdo\n\n"
                    "Qual dessas funcionalidades você gostaria de explorar? Posso te guiar passo a passo! 👍"
                )
        
        # Saudações
        elif any(keyword in message.lower() for keyword in greeting_keywords):
            return (
                "Olá! Que bom te ver por aqui! Sou o assistente avançado do Evil Force JWT, especializado em segurança de tokens. "
                "Posso te ajudar com análise de vulnerabilidades, ataques personalizados e recomendações de segurança. "
                "Como posso te ajudar hoje? 😊"
            )
        
        # Resposta genérica
        else:
            return (
                "Estou aqui para te ajudar com o Evil Force JWT, uma ferramenta especializada em segurança de tokens JWT. "
                "Posso te explicar como usar as diferentes funcionalidades, ajudar na análise de vulnerabilidades, ou guiar você "
                "em ataques específicos para testes de penetração. Apenas me diga o que você precisa saber, e farei o meu melhor "
                "para ajudar! 👍"
            )
    
    def shutdown(self):
        """Encerra o servidor Ollama"""
        if self.ollama_process and self.ollama_process.poll() is None:
            try:
                # Tenta encerrar graciosamente primeiro
                self.ollama_process.terminate()
                
                # Aguarda o término (máximo 5 segundos)
                time.sleep(5)
                
                # Força o encerramento se ainda estiver em execução
                if self.ollama_process.poll() is None:
                    self.ollama_process.kill()
                
                logger.info("Servidor Ollama encerrado")
                
            except Exception as e:
                logger.error(f"Erro ao encerrar servidor Ollama: {str(e)}")
        
        self.ollama_running = False

    def ensure_model(self):
        """
        Método público para garantir que o modelo está disponível
        Deve ser chamado explicitamente antes de usar a API
        """
        self._ensure_model()

    def generate_response(self, message: str) -> str:
        """
        Gera uma resposta para uma mensagem usando o modelo Ollama
        
        Args:
            message: Mensagem do usuário
            
        Returns:
            Resposta gerada pelo modelo
        """
        # Se o Ollama não estiver rodando, usar resposta de fallback
        if not self.ollama_running:
            logger.warning("Ollama não está rodando, usando resposta de fallback")
            return self._fallback_response(message)
        
        # Garantir que o modelo está disponível
        self.ensure_model()
        
        try:
            # Criar o prompt para o modelo
            prompt = f"""Você é um assistente especializado em segurança de tokens JWT e está integrado ao Evil Force JWT, uma ferramenta para testes de segurança.
Responda sempre em português do Brasil de forma natural e conversacional.
Use emojis ocasionalmente para tornar a conversa mais amigável.
Forneça explicações detalhadas e técnicas quando necessário, mas mantenha um tom acessível.

Mensagem do usuário: {message}

Sua resposta:"""
            
            # Fazer a chamada para a API
            response = requests.post(
                f"{self.api_base_url}/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_predict": 1024
                    }
                }
            )
            
            # Verificar se a chamada foi bem-sucedida
            if response.status_code == 200:
                # Extrair a resposta
                response_text = response.json().get("response", "")
                
                # Limpar a resposta (remover prefixos comuns)
                response_text = self._clean_response(response_text)
                
                logger.info(f"Resposta gerada com sucesso usando Ollama ({len(response_text)} caracteres)")
                return response_text
            else:
                # Se houver erro, usar resposta de fallback
                logger.error(f"Erro ao gerar resposta: {response.status_code} - {response.text}")
                return self._fallback_response(message)
                
        except Exception as e:
            # Em caso de exceção, usar resposta de fallback
            logger.error(f"Exceção ao gerar resposta: {str(e)}")
            return self._fallback_response(message)

    def _clean_response(self, text: str) -> str:
        """
        Limpa a resposta do modelo, removendo prefixos comuns
        
        Args:
            text: Texto a ser limpo
            
        Returns:
            Texto limpo
        """
        # Remover prefixos comuns que os modelos podem gerar
        prefixes = [
            "Sua resposta:",
            "Resposta:",
            "Assistente:",
            "AI:",
            "IA:"
        ]
        
        cleaned_text = text.strip()
        
        for prefix in prefixes:
            if cleaned_text.startswith(prefix):
                cleaned_text = cleaned_text[len(prefix):].strip()
        
        return cleaned_text 