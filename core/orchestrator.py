import threading
import logging
from ai_module.realtime_event_bus import EventBus
from ai_module.ai_feedback_engine import AIFeedbackEngine

class Orchestrator:
    """
    Centraliza execução, coleta eventos, envia para IA, aplica sugestões e atualiza interface.
    """
    def __init__(self, modules: dict, cli_callback=None, auto_mode=False):
        self.event_bus = EventBus()
        self.feedback_engine = AIFeedbackEngine()
        self.modules = modules  # Dict de módulos de ataque
        self.cli_callback = cli_callback  # Função para atualizar CLI/GUI
        self.auto_mode = auto_mode
        self.logger = logging.getLogger(__name__)
        self.running = False

    def start(self):
        self.event_bus.subscribe('attack_result', self._on_attack_result)
        self.event_bus.start()
        self.running = True
        # Inicia cada módulo de ataque em thread separada
        for name, mod in self.modules.items():
            t = threading.Thread(target=mod.run, args=(self.event_bus,), daemon=True)
            t.start()
        self.logger.info("Orquestrador iniciado.")

    def _on_attack_result(self, event):
        feedback = self.feedback_engine.process_event(event)
        # Atualiza interface
        if self.cli_callback:
            self.cli_callback(feedback)
        # Aplica sugestões automaticamente se auto_mode
        if self.auto_mode and feedback['suggestions']:
            for s in feedback['suggestions']:
                # Exemplo: aplicar ajuste automático (customize conforme módulo)
                self.logger.info(f"[AUTO] Aplicando sugestão: {s}")
                # Aqui pode-se chamar métodos dos módulos para ajuste dinâmico

    def stop(self):
        self.running = False
        self.event_bus.stop()
