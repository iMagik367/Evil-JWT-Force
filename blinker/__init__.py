# Stub blinker package to override installed blinker
class Namespace:
    """Stub Namespace"""
    def __init__(self):
        pass
    def signal(self, name):
        # Return dummy placeholder
        return lambda *args, **kwargs: None

class Signal:
    """Stub Signal"""
    def __init__(self):
        pass
    def connect(self, receiver):
        pass
    def send(self, *args, **kwargs):
        pass

ANY = None
NamedSignal = None
__all__ = ['Namespace','Signal','ANY','NamedSignal'] 