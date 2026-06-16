from PyQt5 import QtWidgets, QtCore
import sys

class FeedbackWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Evil JWT Force - Feedback em Tempo Real')
        self.setGeometry(100, 100, 800, 400)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.text_area = QtWidgets.QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.layout.addWidget(self.text_area)
        self.suggestion_area = QtWidgets.QTextEdit(self)
        self.suggestion_area.setReadOnly(True)
        self.layout.addWidget(self.suggestion_area)
        self.alert_area = QtWidgets.QTextEdit(self)
        self.alert_area.setReadOnly(True)
        self.layout.addWidget(self.alert_area)
        self.setLayout(self.layout)

    def update_feedback(self, feedback):
        event = feedback.get('event', {})
        suggestions = feedback.get('suggestions', [])
        alerts = feedback.get('alerts', [])
        if event:
            self.text_area.append(f"<b>Evento:</b> {event}")
        if suggestions:
            self.suggestion_area.append(f"<span style='color:blue'><b>Sugestão:</b> {suggestions}</span>")
        if alerts:
            self.alert_area.append(f"<span style='color:red'><b>Alerta:</b> {alerts}</span>")
        QtWidgets.QApplication.processEvents()

# Exemplo de uso isolado
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = FeedbackWindow()
    win.show()
    import threading
    import time
    def fake_feedback():
        for i in range(10):
            win.update_feedback({'suggestions': [f"Teste {i}"], 'alerts': [f"Alerta {i}"], 'event': {'jwt': f"token{i}"}})
            time.sleep(1)
    t = threading.Thread(target=fake_feedback)
    t.start()
    sys.exit(app.exec_())
