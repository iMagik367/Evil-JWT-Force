#!/usr/bin/env python3
"""
Módulo utilitário para saída colorida no terminal
"""

import os
import sys
import platform

class ColorOutput:
    """
    Classe para exibir texto colorido no terminal.
    Detecta automaticamente suporte a cores no terminal.
    """
    
    # Códigos ANSI para cores
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # Cores de texto
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Cores de fundo
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    def __init__(self, use_colors=None):
        """
        Inicializa a classe de saída colorida.
        
        Args:
            use_colors: Força o uso de cores (True) ou desativa cores (False).
                       Se None, detecta automaticamente o suporte a cores.
        """
        # Determinar se devemos usar cores
        if use_colors is None:
            self.use_colors = self._detect_color_support()
        else:
            self.use_colors = use_colors
    
    def _detect_color_support(self):
        """
        Detecta se o terminal suporta cores ANSI.
        
        Returns:
            bool: True se o terminal suporta cores, False caso contrário.
        """
        # Windows 10 com suporte a ANSI
        if platform.system() == 'Windows':
            if int(platform.release()) >= 10:
                return True
            
            # Verificar se é o terminal CMD ou PowerShell no Windows
            if 'TERM' in os.environ and os.environ['TERM'] == 'xterm':
                return True
            
            return False
        
        # No Linux e macOS, verificar se a saída é um terminal
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            return True
        
        # Verificar variável de ambiente TERM
        if 'TERM' in os.environ and os.environ['TERM'] != 'dumb':
            return True
        
        return False
    
    def colorize(self, text, color=None, bg_color=None, bold=False, underline=False):
        """
        Aplica cores e estilos ao texto.
        
        Args:
            text: Texto a ser colorido
            color: Código de cor para o texto
            bg_color: Código de cor para o fundo
            bold: Aplica estilo negrito
            underline: Aplica estilo sublinhado
            
        Returns:
            str: Texto colorido com códigos ANSI
        """
        if not self.use_colors:
            return text
        
        style = ""
        if bold:
            style += self.BOLD
        if underline:
            style += self.UNDERLINE
        if color:
            style += color
        if bg_color:
            style += bg_color
        
        if style:
            return f"{style}{text}{self.RESET}"
        return text
    
    def success(self, message):
        """
        Exibe mensagem de sucesso em verde.
        
        Args:
            message: Mensagem a ser exibida
        """
        print(self.colorize(f"[+] {message}", self.GREEN, bold=True))
    
    def error(self, message):
        """
        Exibe mensagem de erro em vermelho.
        
        Args:
            message: Mensagem a ser exibida
        """
        print(self.colorize(f"[-] {message}", self.RED, bold=True))
    
    def warning(self, message):
        """
        Exibe mensagem de aviso em amarelo.
        
        Args:
            message: Mensagem a ser exibida
        """
        print(self.colorize(f"[!] {message}", self.YELLOW, bold=True))
    
    def info(self, message):
        """
        Exibe mensagem informativa em azul.
        
        Args:
            message: Mensagem a ser exibida
        """
        print(self.colorize(f"[*] {message}", self.BLUE, bold=True))
    
    def debug(self, message):
        """
        Exibe mensagem de depuração em ciano.
        
        Args:
            message: Mensagem a ser exibida
        """
        print(self.colorize(f"[D] {message}", self.CYAN))
    
    def title(self, message):
        """
        Exibe título em magenta com sublinhado.
        
        Args:
            message: Mensagem a ser exibida
        """
        print(self.colorize(f"\n{message}", self.MAGENTA, bold=True, underline=True))
    
    def section(self, message):
        """
        Exibe título de seção em ciano.
        
        Args:
            message: Mensagem a ser exibida
        """
        print(self.colorize(f"\n=== {message} ===", self.CYAN, bold=True))
    
    def result(self, message):
        """
        Exibe resultado em verde com fundo.
        
        Args:
            message: Mensagem a ser exibida
        """
        print(self.colorize(f"[RESULT] {message}", self.GREEN, bold=True))
    
    def table_header(self, *headers):
        """
        Exibe cabeçalho de tabela.
        
        Args:
            *headers: Cabeçalhos da tabela
        """
        header_text = " | ".join(headers)
        divider = "-" * len(header_text)
        print(self.colorize(header_text, self.WHITE, bold=True))
        print(self.colorize(divider, self.WHITE))
    
    def table_row(self, *columns):
        """
        Exibe linha de tabela.
        
        Args:
            *columns: Colunas da linha
        """
        row_text = " | ".join(str(col) for col in columns)
        print(row_text)

if __name__ == "__main__":
    # Exemplo de uso
    color = ColorOutput()
    
    color.title("EVIL JWT FORCE - DEMONSTRAÇÃO DE CORES")
    
    color.section("Mensagens de Status")
    color.success("Operação concluída com sucesso")
    color.error("Erro ao executar operação")
    color.warning("Atenção: recurso experimental")
    color.info("Processando dados...")
    color.debug("Variável x = 42")
    
    color.section("Tabela de Exemplo")
    color.table_header("ID", "Nome", "Status")
    color.table_row(1, "Token HS256", "Vulnerável")
    color.table_row(2, "Token RS256", "Seguro")
    color.table_row(3, "Token none", "Crítico")
    
    color.section("Cores Personalizadas")
    print(color.colorize("Texto em vermelho", color.RED))
    print(color.colorize("Texto em verde com fundo amarelo", color.GREEN, color.BG_YELLOW))
    print(color.colorize("Texto negrito e sublinhado", bold=True, underline=True)) 