import logging
import time
from core.jwt_bruteforcer import JWTBruteforcer
from core.orchestrator import Orchestrator
from core.gui_feedback import FeedbackWindow
from PyQt5 import QtWidgets
import sys

class GUIOrchestrator(Orchestrator):
    def __init__(self, modules, gui_window, auto_mode=False):
        super().__init__(modules, cli_callback=gui_window.update_feedback, auto_mode=auto_mode)
        self.gui_window = gui_window

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = QtWidgets.QApplication(sys.argv)
    win = FeedbackWindow()
    win.show()
    # Instancia módulo de ataque
    bruteforcer = JWTBruteforcer(wordlist=['admin', 'jwt', 'evil', 'force'], alg='HS256')
    # Orquestrador com feedback GUI dinâmico
    orchestrator = GUIOrchestrator(
        modules={'brute': bruteforcer},
        gui_window=win,
        auto_mode=False  # True para aplicar sugestões automaticamente
    )
    orchestrator.start()
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        orchestrator.stop()
        print("Execução finalizada.")
