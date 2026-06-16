#!/usr/bin/env python3
"""
AI Module Package for Evil JWT Force
"""

import logging
import os
import sys
import importlib
from pathlib import Path

# Configurar logging
logger = logging.getLogger('AI_MODULE')

# Lista de módulos disponíveis
available_modules = []

# Tentar importar módulos de API
try:
    from .ollama_api import OllamaAPI
    available_modules.append("OllamaAPI")
except ImportError as e:
    logger.warning(f"Módulo OllamaAPI não disponível: {str(e)}")

try:
    from .openai_api import OpenAIAPI
    available_modules.append("OpenAIAPI")
except ImportError as e:
    logger.warning(f"Módulo OpenAIAPI não disponível: {str(e)}")

try:
    from .huggingface_api import HuggingFaceAPI
    available_modules.append("HuggingFaceAPI")
except ImportError as e:
    logger.warning(f"Módulo HuggingFaceAPI não disponível: {str(e)}")

try:
    from .custom_api import CustomAPI
    available_modules.append("CustomAPI")
except ImportError as e:
    logger.warning(f"Módulo CustomAPI não disponível: {str(e)}")

try:
    from .llama_api import LlamaAPI
    available_modules.append("LlamaAPI")
except ImportError as e:
    logger.warning(f"Módulo LlamaAPI não disponível: {str(e)}")

# Tentar importar módulos de análise
try:
    from .jwt_predictor import JWTPredictor
    available_modules.append("JWTPredictor")
except ImportError as e:
    logger.warning(f"Módulo JWTPredictor não disponível: {str(e)}")

try:
    from .adaptive_fuzzer import AdaptiveFuzzer
    available_modules.append("AdaptiveFuzzer")
except ImportError as e:
    logger.warning(f"Módulo AdaptiveFuzzer não disponível: {str(e)}")

# Registrar módulos disponíveis
if available_modules:
    logger.info(f"Módulos AI disponíveis: {', '.join(available_modules)}")
else:
    logger.warning("Nenhum módulo AI disponível")

# Exportar módulos disponíveis
__all__ = available_modules 