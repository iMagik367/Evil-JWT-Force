#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - Meta Llama Stack API Integration Module
Integrates with Meta Llama Stack CLI (via llama-stack) to provide AI capabilities.

Usage:
  pip install llama-stack
  pip install llama-stack -U
  llama model list
  llama model list --show-all

Modelos padrão:
  - Llama-4-Scout       (análise de tokens)
  - Llama-4-Maverick    (conversação geral)
  - Llama-3.3-70B       (embeddings)
"""

import subprocess
import json
from typing import Dict, List, Any, Optional

class LlamaAPI:
    """
    Interface to Meta Llama Stack via CLI.
    """

    # Lista de modelos padrão para instalação
    DEFAULT_MODELS: List[str] = [
        "Llama-4-Scout",
        "Llama-4-Maverick",
        "Llama-3.3-70B",
        "Llama-3.2-1B",
        "Llama-3.2-3B",
        "Llama-3.1-405B",
        "Llama-3.1-8B",
        "Llama-3.2-11B",
        "Llama-3.2-90B"
    ]

    def __init__(self):
        # Certifique-se de que o CLI 'llama' está instalado e disponível no PATH
        pass

    def list_models(self, show_all: bool = False) -> str:
        """
        Lista modelos disponíveis no Llama Stack.
        """
        cmd = ["llama", "model", "list"]
        if show_all:
            cmd.append("--show-all")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        return proc.stdout

    def analyze_token(self, token: str) -> Dict[str, Any]:
        """
        Analisa um token JWT usando o modelo Llama-4-Scout via chat CLI e retorna JSON ou texto cru.
        """
        prompt = (
            f"Analise o seguinte token JWT e reporte vulnerabilidades e recomendações em JSON:\n{token}\n"
            "Retorne um objeto JSON com campos: vulnerabilities, recommendations."
        )
        cmd = ["llama", "chat", "--model", "Llama-4-Scout", "--prompt", prompt]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        output = proc.stdout
        try:
            return json.loads(output)
        except Exception:
            return {"analysis_text": output}

    def chat_completion(self, message: str, history: Optional[List[Dict[str, str]]] = None, system_prompt: Optional[str] = None) -> str:
        """
        Retorna resposta de chat usando o modelo Llama-4-Maverick.
        """
        # Incluir prompt de sistema (chain-of-thought) se fornecido
        prompt = ""
        if system_prompt:
            prompt += system_prompt.strip() + "\n\n"
        if history:
            for item in history[-5:]:
                role = item.get("role", "user")
                content = item.get("content", "")
                prefix = "Usuário:" if role == "user" else "Assistente:"
                prompt += f"{prefix} {content}\n"
        prompt += f"Usuário: {message}\nAssistente:"
        cmd = ["llama", "chat", "--model", "Llama-4-Maverick", "--prompt", prompt]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            return "Erro: tempo limite de 10s excedido na chamada ao modelo Llama-4-Maverick."
        stderr = proc.stderr.strip()
        if proc.returncode != 0:
            # Detect invalid subcommand error and fallback to HuggingFaceAPI
            if "invalid choice: 'chat'" in stderr:
                try:
                    from .huggingface_api import HuggingFaceAPI
                    hf = HuggingFaceAPI()
                    return hf.chat_completion(message, history=history)
                except Exception:
                    pass
            return f"Erro na API Llama Stack: {stderr}"
        return proc.stdout

    def get_embeddings(self, text: str) -> List[float]:
        """
        Gera embeddings do texto usando o modelo Llama-3.3-70B via CLI.
        """
        cmd = ["llama", "embed", "--model", "Llama-3.3-70B", "--text", text, "--json"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr)
        try:
            return json.loads(proc.stdout)
        except Exception:
            return []

    def install_model(self, model_name: str) -> bool:
        """
        Instala um modelo específico via CLI llama-stack.

        Retorna True se a instalação for bem-sucedida, False caso contrário.
        """
        cmd = ["llama", "model", "install", model_name]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode == 0

    def install_models(self, models: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Instala uma lista de modelos (ou DEFAULT_MODELS se não fornecida).  
        Retorna um dict mapeando model_name -> sucesso (True/False).
        """
        results: Dict[str, bool] = {}
        to_install = models or self.DEFAULT_MODELS
        for m in to_install:
            try:
                ok = self.install_model(m)
                results[m] = ok
            except Exception:
                results[m] = False
        return results 