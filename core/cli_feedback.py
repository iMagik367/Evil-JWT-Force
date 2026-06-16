import sys
import time
import threading

def cli_feedback_callback(feedback):
    """
    Exibe sugestões e alertas em tempo real na CLI.
    """
    suggestions = feedback.get('suggestions', [])
    alerts = feedback.get('alerts', [])
    event = feedback.get('event', {})
    if alerts:
        print(f"\033[91m[ALERTA]\033[0m {alerts}")
    if suggestions:
        print(f"\033[94m[SUGESTÃO]\033[0m {suggestions}")
    if event:
        print(f"[EVENTO] {event}")
    sys.stdout.flush()

# Exemplo de uso isolado
if __name__ == "__main__":
    def fake_feedback():
        for i in range(5):
            cli_feedback_callback({'suggestions': [f"Teste {i}"], 'alerts': [f"Alerta {i}"], 'event': {'jwt': f"token{i}"}})
            time.sleep(1)
    t = threading.Thread(target=fake_feedback)
    t.start()
    t.join()
