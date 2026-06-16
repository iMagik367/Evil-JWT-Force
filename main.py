#!/usr/bin/env python3
"""
EVIL_JWT_FORCE - Entry Point Avançado
Orquestrador central para CLI, GUI e integração dinâmica de módulos/scripts.
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path
from ai_module.vulnerability_annotator import JWTAnnotator
from core.cli import run_automatic_mode

# Garante que todos os diretórios essenciais estão no sys.path somente em desenvolvimento
PROJECT_ROOT = Path(__file__).resolve().parent
if not getattr(sys, 'frozen', False):
    for subdir in ["core", "utils", "modules", "config", "scripts"]:
        sys.path.insert(0, str(PROJECT_ROOT / subdir))
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure essential directories exist
for d in ['logs', 'output', 'output/api_cache', 'output/osint_results', 'output/pix_logs']:
    dir_path = PROJECT_ROOT / d
    dir_path.mkdir(parents=True, exist_ok=True)

# Logging avançado
try:
    from utils.logger import setup_logger
except ImportError:
    import logging
    def setup_logger(*args, **kwargs):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger("EVIL_JWT_FORCE_Fallback")
logger = setup_logger("EVIL_JWT_FORCE.main")

# Importação dinâmica dos módulos principais
def import_module_safe(module_path, symbol=None):
    try:
        mod = importlib.import_module(module_path)
        if symbol:
            return getattr(mod, symbol)
        return mod
    except Exception as e:
        logger.error(f"Erro ao importar {module_path}: {e}")
        return None

# Função para iniciar a interface gráfica
def start_gui():
    """Initialize and run the PyQt graphical interface"""
    try:
        from PyQt5.QtWidgets import QApplication, QSplashScreen
        from PyQt5.QtGui import QPalette, QColor, QFont, QPixmap
        from gui.qt_interface import MainWindow
    except Exception as e:
        logger.error(f"Erro ao iniciar GUI Qt: {e}")
        sys.exit(3)
    logger.info("Iniciando interface gráfica PyQt (in-process)...")
    app = QApplication(sys.argv)
    # Show splash screen while initializing
    try:
        # Load splash image from assets (700x400px recommended)
        splash_pix = QPixmap(os.path.join(os.path.dirname(__file__), 'gui', 'assets', 'splash.png'))
        splash = QSplashScreen(splash_pix)
        splash.show()
        # Ensure splash is displayed
        app.processEvents()
    except Exception as e:
        logger.warning(f"Não foi possível exibir splash screen: {e}")

    # Apply global dark theme before creating the window
    app.setStyle('Fusion')
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(43,43,43))
    dark_palette.setColor(QPalette.WindowText, QColor(255,255,255))
    dark_palette.setColor(QPalette.Base, QColor(35,35,35))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53,53,53))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(255,255,255))
    dark_palette.setColor(QPalette.ToolTipText, QColor(255,255,255))
    dark_palette.setColor(QPalette.Text, QColor(255,255,255))
    dark_palette.setColor(QPalette.Button, QColor(53,53,53))
    dark_palette.setColor(QPalette.ButtonText, QColor(255,255,255))
    dark_palette.setColor(QPalette.BrightText, QColor(255,0,0))
    dark_palette.setColor(QPalette.Highlight, QColor(142,45,197))
    dark_palette.setColor(QPalette.HighlightedText, QColor(255,255,255))
    app.setPalette(dark_palette)
    # Global font
    app.setFont(QFont('Segoe UI', 12))
    window = MainWindow()
    print('[DEBUG] MainWindow criado')
    # Close splash screen when main window is ready
    try:
        splash.finish(window)
    except NameError:
        pass
    # Always start maximized
    window.showMaximized()
    # Debug: verifica se botões estão criados
    try:
        print('[DEBUG] chat_toggle_btn:', hasattr(window, 'chat_toggle_btn'), window.chat_toggle_btn)
        print('[DEBUG] vpn_log_btn:', hasattr(window, 'vpn_log_btn'), window.vpn_log_btn)
    except Exception as e:
        print('[DEBUG] Erro ao acessar botões:', e)
    app.exec_()
    sys.exit(0)

# Função para executar scripts utilitários
def run_script(script_name, *args):
    script_path = PROJECT_ROOT / "scripts" / script_name
    if not script_path.exists():
        logger.error(f"Script não encontrado: {script_name}")
        return
    logger.info(f"Executando script: {script_name}")
    subprocess.run([sys.executable, str(script_path)] + list(args), check=True)

# Função para executar módulos core dinamicamente
def run_core_module(module_key, **kwargs):
    modules = {
        "auth":      ("core.auth", "Authenticator"),
        "wordlist":  ("core.wordlist_generator", "run"),
        "bruteforce":("core.bruteforce", "JWTBruteforcer"),
        "aes":       ("core.aes_decrypt", "run"),
        "sql":       ("core.sql_injector", "SQLInjector"),
        "sentry":    ("core.sentry_simulator", "run"),
        "report":    ("core.report", "generate_html_report")
    }
    if module_key not in modules:
        logger.error(f"Módulo '{module_key}' não encontrado.")
        return
    module_path, symbol = modules[module_key]
    obj = import_module_safe(module_path, symbol)
    if obj is None:
        logger.error(f"Falha ao carregar {module_path}.{symbol}")
        return
    try:
        if callable(obj):
            obj(**kwargs)
        else:
            if hasattr(obj, "run"):
                obj.run(**kwargs)
            else:
                logger.warning(f"Módulo {module_key} não possui método executável padrão.")
    except Exception as e:
        logger.error(f"Erro ao executar módulo {module_key}: {e}", exc_info=True)

# Função principal de orquestração
def main():
    import argparse
    parser = argparse.ArgumentParser(description="EVIL_JWT_FORCE - Orquestrador CLI/GUI")
    parser.add_argument('--cli', action='store_true', help='Iniciar interface de linha de comando')
    parser.add_argument('--auto', action='store_true', help='Executar modo automático completo')
    parser.add_argument('--manual', action='store_true', help='Executar modo manual')
    parser.add_argument('--module', type=str, help='Executar módulo específico (ex: auth, wordlist, bruteforce, aes, sql, sentry, report)')
    parser.add_argument('--script', type=str, help='Executar script utilitário da pasta scripts/')
    parser.add_argument('--config', type=str, help='Arquivo de configuração customizado')
    parser.add_argument('--args', nargs=argparse.REMAINDER, help='Argumentos adicionais para módulos/scripts')
    # --- PIX Manipulação Avançada ---
    parser.add_argument('--pix-manipular', action='store_true', help='Executar fluxo de manipulação Pix (valor_entrada ≠ valor_saida)')
    parser.add_argument('--valor-entrada', type=float, help='Valor do Pix do QR code (entrada)')
    parser.add_argument('--valor-saida', type=float, help='Valor recebido pelo recebedor (saida)')
    parser.add_argument('--chave', type=str, help='Chave Pix do recebedor')
    parser.add_argument('--endpoint-criacao', type=str, help='Endpoint de criação de cobrança')
    parser.add_argument('--endpoint-webhook', type=str, help='Endpoint de webhook/callback de recebimento')
    parser.add_argument('--txid', type=str, help='TXID opcional para rastreio')
    args = parser.parse_args()

    logger.info("Inicializando EVIL_JWT_FORCE...")

    # --- PIX Manipulação Avançada ---
    if args.pix_manipular:
        from modules.fake_pix_module import manipular_valor_entrada_saida_pix
        if not all([args.valor_entrada, args.valor_saida, args.chave, args.endpoint_criacao, args.endpoint_webhook]):
            print("[ERRO] Para --pix-manipular, forneça --valor-entrada, --valor-saida, --chave, --endpoint-criacao e --endpoint-webhook.")
            return
        resultado = manipular_valor_entrada_saida_pix(
            valor_entrada=args.valor_entrada,
            valor_saida=args.valor_saida,
            chave_pix=args.chave,
            endpoint_criacao=args.endpoint_criacao,
            endpoint_webhook=args.endpoint_webhook,
            txid=args.txid
        )
        print(f"\n[+] PIX Manipulado com sucesso!")
        print(f"  TXID: {resultado['txid']}")
        print(f"  Valor de entrada (pagador): R$ {resultado['valor_entrada']:.2f}")
        print(f"  Valor de saída (recebedor): R$ {resultado['valor_saida']:.2f}")
        print(f"  Payload QR: {resultado['payload_qr']}")
        print(f"  Payload Webhook: {resultado['payload_recebido']}")
        print(f"  Log em: output/fake_pix_logs.txt\n")
        return

    # GUI padrão (se --cli não for passado)
    if not args.cli and not args.auto:
        start_gui()

    # Execução de script utilitário
    if args.script:
        run_script(args.script, *(args.args or []))
        return

    # Execução de módulo core específico
    if args.module:
        run_core_module(args.module, config=args.config, extra_args=args.args)
        return

    # CLI Automático
    if args.auto:
        print("Executando modo automatico completo...\n")
        run_automatic_mode()
        print("Modo automatico concluido.")
        return

    # CLI Manual
    if args.manual:
        logger.info("Executando modo manual (CLI)...")
        cli_manual = import_module_safe("core.cli", "run_manual_mode")
        if cli_manual:
            cli_manual()
        else:
            logger.error("Falha ao iniciar modo manual.")
        return

    # CLI Interativo padrão
    print('[DEBUG] Executando start_gui()')
    start_gui()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Execução interrompida pelo usuário.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)