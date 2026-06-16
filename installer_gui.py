import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QTextEdit, QMessageBox,
    QCheckBox, QGroupBox, QFileDialog, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import install_deps
import logging

class InstallerThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, install_path, options):
        super().__init__()
        self.install_path = install_path
        self.options = options
        
    def run(self):
        try:
            # Configurar logging para capturar mensagens
            class QtLogHandler(logging.Handler):
                def __init__(self, signal):
                    super().__init__()
                    self.signal = signal
                def emit(self, record):
                    msg = self.format(record)
                    self.signal.emit(msg)
            
            # Adicionar handler personalizado
            handler = QtLogHandler(self.progress)
            handler.setFormatter(logging.Formatter('%(message)s'))
            logging.getLogger().addHandler(handler)
            
            # Mudar para o diretório de instalação
            os.chdir(self.install_path)
            
            # Executar instalação
            install_deps.main()
            
            self.finished.emit(True, "Instalação concluída com sucesso!")
        except Exception as e:
            self.finished.emit(False, f"Erro durante a instalação: {str(e)}")

class InstallerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Evil JWT Force - Instalador")
        self.setMinimumSize(600, 400)
        
        # Configurar interface
        self.setup_ui()
        
        # Inicializar thread de instalação
        self.install_thread = None
        
    def setup_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Título
        title = QLabel("Evil JWT Force - Instalador")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Grupo de opções
        options_group = QGroupBox("Opções de Instalação")
        options_layout = QVBoxLayout()
        
        # Checkboxes para opções
        self.install_venv = QCheckBox("Criar ambiente virtual")
        self.install_venv.setChecked(True)
        options_layout.addWidget(self.install_venv)
        
        self.install_deps = QCheckBox("Instalar dependências")
        self.install_deps.setChecked(True)
        options_layout.addWidget(self.install_deps)
        
        self.create_shortcut = QCheckBox("Criar atalho global")
        self.create_shortcut.setChecked(True)
        options_layout.addWidget(self.create_shortcut)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Diretório de instalação
        dir_group = QGroupBox("Diretório de Instalação")
        dir_layout = QHBoxLayout()
        
        self.install_path = QLineEdit()
        self.install_path.setText(str(Path.cwd()))
        dir_layout.addWidget(self.install_path)
        
        browse_btn = QPushButton("Procurar...")
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_btn)
        
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log de instalação
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        self.install_btn = QPushButton("Instalar")
        self.install_btn.clicked.connect(self.start_installation)
        buttons_layout.addWidget(self.install_btn)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
    def browse_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Selecione o Diretório de Instalação",
            str(Path.cwd())
        )
        if dir_path:
            self.install_path.setText(dir_path)
    
    def start_installation(self):
        # Desabilitar botões durante instalação
        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        # Limpar log
        self.log_text.clear()
        
        # Configurar opções
        options = {
            'install_venv': self.install_venv.isChecked(),
            'install_deps': self.install_deps.isChecked(),
            'create_shortcut': self.create_shortcut.isChecked()
        }
        
        # Iniciar thread de instalação
        self.install_thread = InstallerThread(
            self.install_path.text(),
            options
        )
        self.install_thread.progress.connect(self.update_log)
        self.install_thread.finished.connect(self.installation_finished)
        self.install_thread.start()
        
        # Iniciar barra de progresso
        self.progress_bar.setRange(0, 0)
    
    def update_log(self, message):
        self.log_text.append(message)
        # Rolar para o final
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def installation_finished(self, success, message):
        # Parar barra de progresso
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        
        # Reabilitar botões
        self.install_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        
        # Mostrar mensagem
        if success:
            QMessageBox.information(self, "Sucesso", message)
        else:
            QMessageBox.critical(self, "Erro", message)

def main():
    app = QApplication(sys.argv)
    
    # Definir estilo
    app.setStyle('Fusion')
    
    # Criar e mostrar janela
    window = InstallerGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 