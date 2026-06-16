import threading
import time
import queue
import logging
from ai_module.chat_manager import ChatManager
from PyQt5.QtCore import QObject, pyqtSignal

class AIWorker(QObject):
    """
    Background AI worker to process user events and provide suggestions.
    """
    suggestion_ready = pyqtSignal(str)

    def __init__(self, hf_api_key=None, openai_key=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('AIWorker')
        self.queue = queue.Queue()
        # Custom system prompt for suggestions
        suggestion_prompt = (
            "Você é um assistente que fornece sugestões de próximos passos "
            "com base nas ações recentes do usuário. Analise as seguintes ações "
            "e proponha sugestões práticas e concisas."
        )
        # Initialize ChatManager with custom prompt
        self.chat_manager = ChatManager(hf_api_key=hf_api_key, system_prompt=suggestion_prompt)
        if openai_key:
            self.chat_manager.set_openai_api_key(openai_key)
        # Start background thread
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def push_event(self, event: str):
        """
        Push a user event into the processing queue.
        """
        self.queue.put(event)

    def run(self):
        """
        Main loop: collect events and send to AI for suggestions.
        """
        events_buffer = []
        while True:
            try:
                # Wait up to 10 seconds for first event
                event = self.queue.get(timeout=10)
                events_buffer.append(event)
                # Collect more events for a short period
                t_start = time.time()
                while time.time() - t_start < 2:
                    try:
                        evt = self.queue.get(timeout=0.5)
                        events_buffer.append(evt)
                    except queue.Empty:
                        break
                # Build summary message
                summary = "Seguem as últimas ações realizadas:\n"
                for ev in events_buffer:
                    summary += f"- {ev}\n"
                summary += "Quais são suas sugestões para próximos passos?"
                self.logger.info("Enviando eventos para AIWorker...")
                # Get suggestion from AI
                suggestion = self.chat_manager.send(summary)
                # Emit signal with suggestion
                self.suggestion_ready.emit(suggestion)
                # Clear buffer
                events_buffer.clear()
            except queue.Empty:
                # No events, continue waiting
                continue
            except Exception as e:
                self.logger.error(f"Erro em AIWorker: {e}")
                time.sleep(5) 