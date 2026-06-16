from typing import Any

class AttackModuleBase:
    """
    Base para módulos de ataque com hooks de integração em tempo real.
    """
    def __init__(self, name):
        self.name = name
        self.event_bus = None
        self.suggestion_callback = None

    def set_event_bus(self, event_bus):
        self.event_bus = event_bus

    def set_suggestion_callback(self, callback):
        self.suggestion_callback = callback

    def report_result(self, result: dict):
        if self.event_bus:
            event = result.copy()
            event['module'] = self.name
            self.event_bus.publish('attack_result', event)

    def receive_suggestion(self, suggestion: Any):
        # Cada módulo pode implementar lógica para aplicar sugestões automaticamente
        pass

    def run(self, event_bus=None):
        self.set_event_bus(event_bus)
        # Implementação específica do ataque deve ser feita nas subclasses
        raise NotImplementedError()
