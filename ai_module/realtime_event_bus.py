import queue
import threading
from typing import Callable, Any, Dict, List

class EventBus:
    """
    Simple thread-safe event bus for real-time communication between attack modules and the AI pipeline.
    """
    def __init__(self):
        self.subscribers: Dict[str, List[Callable[[Any], None]]] = {}
        self.q = queue.Queue()
        self.running = False
        self.thread = None

    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, data: Any):
        self.q.put((event_type, data))

    def _event_loop(self):
        while self.running:
            try:
                event_type, data = self.q.get(timeout=0.2)
                for cb in self.subscribers.get(event_type, []):
                    try:
                        cb(data)
                    except Exception as e:
                        print(f"[EventBus] Error in callback: {e}")
            except queue.Empty:
                continue

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._event_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
