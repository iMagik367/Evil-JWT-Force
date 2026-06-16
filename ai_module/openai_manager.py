import openai
import json
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime
import time

class OpenAIManager:
    def __init__(self, config_path: str = "config/openai_config.json"):
        self.config_path = config_path
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"  # ou outro modelo apropriado
        self.setup_logging()
        self.load_config()
        self.setup_openai()

    def setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            filename='logs/openai.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('OpenAIManager')

    def load_config(self):
        """Carrega configurações da OpenAI"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.model = config.get('model', self.model)
        except Exception as e:
            self.logger.error(f"Erro ao carregar configurações: {str(e)}")

    def setup_openai(self):
        """Configura o cliente OpenAI"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não configurada")
        openai.api_key = self.api_key

    async def analyze_security(self, target_data: Dict) -> Dict:
        """
        Analisa dados de segurança usando a API da OpenAI
        """
        try:
            # Prepara o prompt para análise de segurança
            prompt = self._prepare_security_prompt(target_data)
            
            # Faz a chamada à API
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em segurança cibernética."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Processa a resposta
            analysis = self._process_security_response(response)
            
            # Registra a análise
            self._log_analysis(target_data, analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise de segurança: {str(e)}")
            raise

    def _prepare_security_prompt(self, target_data: Dict) -> str:
        """
        Prepara o prompt para análise de segurança
        """
        return f"""
        Analise os seguintes dados de segurança:
        
        Target: {target_data.get('target')}
        Type: {target_data.get('type')}
        Data: {target_data.get('data')}
        
        Forneça uma análise detalhada incluindo:
        1. Vulnerabilidades potenciais
        2. Recomendações de mitigação
        3. Nível de risco
        4. Próximos passos sugeridos
        """

    def _process_security_response(self, response) -> Dict:
        """
        Processa a resposta da API
        """
        try:
            content = response.choices[0].message.content
            return {
                "analysis": content,
                "timestamp": datetime.now().isoformat(),
                "model": self.model
            }
        except Exception as e:
            self.logger.error(f"Erro ao processar resposta: {str(e)}")
            raise

    def _log_analysis(self, target_data: Dict, analysis: Dict):
        """
        Registra a análise no log
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "target": target_data.get('target'),
            "type": target_data.get('type'),
            "analysis": analysis
        }
        self.logger.info(json.dumps(log_entry))

    async def generate_security_report(self, analysis_data: Dict) -> str:
        """
        Gera um relatório de segurança formatado
        """
        try:
            prompt = f"""
            Gere um relatório de segurança profissional baseado na seguinte análise:
            
            {json.dumps(analysis_data, indent=2)}
            
            O relatório deve incluir:
            1. Resumo executivo
            2. Vulnerabilidades encontradas
            3. Recomendações
            4. Nível de risco
            5. Próximos passos
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em relatórios de segurança."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {str(e)}")
            raise

    async def suggest_security_improvements(self, current_config: Dict) -> List[str]:
        """
        Sugere melhorias de segurança baseadas na configuração atual
        """
        try:
            prompt = f"""
            Analise a seguinte configuração de segurança e sugira melhorias:
            
            {json.dumps(current_config, indent=2)}
            
            Forneça sugestões específicas e práticas para melhorar a segurança.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em segurança cibernética."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.split('\n')
            
        except Exception as e:
            self.logger.error(f"Erro ao sugerir melhorias: {str(e)}")
            raise 