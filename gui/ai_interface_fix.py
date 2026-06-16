#!/usr/bin/env python3
"""
Patch para corrigir problemas na interface de IA do Evil Force JWT.
Este script aplica correções ao arquivo ai_interface.py para garantir que os comandos de ataque funcionem corretamente.
"""

import os
import sys
import re
import shutil
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('AI_INTERFACE_FIX')

def backup_file(file_path):
    """Cria um backup do arquivo original"""
    backup_path = str(file_path) + '.bak'
    shutil.copy2(file_path, backup_path)
    logger.info(f"Backup criado em {backup_path}")
    return backup_path

def fix_imports(content):
    """Corrige as importações no arquivo"""
    # Adicionar importações necessárias
    imports_to_add = """
# Importações adicionadas pelo patch
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para importações relativas
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Importar módulos necessários para os ataques
try:
    from modules.jwt_utils_simple import decode_token_parts, extract_parts, is_jwt, generate_token
    from modules.jwt_decrypt import JWTDecrypt
    from modules.token_bruteforce import TokenBruteforcer
    from modules.scan_target import TargetScanner
    from modules.fuzz_jwt import JWTFuzzer
    
    HAS_ATTACK_MODULES = True
    print("Módulos de ataque carregados com sucesso")
except ImportError as e:
    print(f"Erro ao importar módulos de ataque: {e}")
    HAS_ATTACK_MODULES = False
"""
    
    # Encontrar a posição após as importações existentes
    import_section_end = re.search(r'import.*?\n\n', content, re.DOTALL)
    if import_section_end:
        pos = import_section_end.end()
        content = content[:pos] + imports_to_add + content[pos:]
    else:
        # Se não encontrar o padrão, adicionar após a última importação
        last_import = re.search(r'import.*?\n', content)
        if last_import:
            pos = last_import.end()
            content = content[:pos] + "\n" + imports_to_add + content[pos:]
    
    return content

def fix_analyze_token_method(content):
    """Corrige o método analyze_token para usar os módulos importados"""
    # Procurar o método _run_token_analysis
    method_pattern = r'def _run_token_analysis\(self, token\):.*?try:.*?if self\.llm_api:(.*?)else:(.*?)except Exception as e:'
    
    replacement = r'''def _run_token_analysis(self, token):
        """Run token analysis in background thread"""
        try:
            # Verificar se os módulos de ataque estão disponíveis
            if HAS_ATTACK_MODULES:
                # Usar os módulos de ataque para análise
                try:
                    # Obter partes do token
                    parsed = extract_parts(token)
                    if not parsed:
                        self.master.after(0, lambda: self.update_token_details(token, {"error": "Token inválido ou mal-formado"}))
                        self.master.after(0, lambda: self.status_msg.set("Erro na análise: Token inválido"))
                        return
                    
                    # Criar instância do JWTDecrypt para análise avançada
                    decryptor = JWTDecrypt()
                    vulnerabilities = decryptor.get_vulnerabilities(token).get('vulnerabilities', [])
                    
                    # Estruturar a análise
                    analysis = {
                        'valid': True,
                        'header': parsed['header'],
                        'payload': parsed['payload'],
                        'vulnerabilities': vulnerabilities,
                        'recommendations': [
                            "Use algoritmos assimétricos como RS256 em vez de HS256",
                            "Adicione uma claim de expiração (exp) ao token",
                            "Não armazene dados sensíveis no payload",
                            "Use chaves fortes e seguras"
                        ]
                    }
                    
                    # Update UI with results
                    self.master.after(0, lambda: self.update_token_details(token, analysis))
                    self.master.after(0, lambda: self.update_token_vulnerabilities(analysis, {"recommendations": analysis['recommendations']}))
                    self.master.after(0, lambda: self.status_msg.set("Análise completa"))
                    return
                except Exception as e:
                    logger = logging.getLogger('AI_INTERFACE')
                    logger.error(f"Erro ao usar módulos de ataque: {str(e)}")
                    # Continuar com o fluxo normal se ocorrer um erro
            
            # Verificar se a API LLM está disponível
            if self.llm_api:
                # Analisar token usando a API LLM
                analysis = self.llm_api.analyze_token(token)
            else:
                # Fallback para análise básica
                logger = logging.getLogger('AI_INTERFACE')
                logger.warning("Nenhuma API LLM disponível, usando análise básica")
                
                # Obter partes do token
                from modules.jwt_utils_simple import decode_token_parts
                token_parts = decode_token_parts(token)'''
    
    # Substituir o método
    content = re.sub(method_pattern, replacement, content, flags=re.DOTALL)
    
    return content

def fix_execute_manual_attack(content):
    """Corrige o método execute_manual_attack para usar os módulos importados"""
    # Procurar o método execute_manual_attack
    method_pattern = r'def execute_manual_attack\(self\):.*?attack_type = self\.attack_type_var\.get\(\)(.*?)def run_attack\(\):'
    
    replacement = r'''def execute_manual_attack(self):
        """Execute the selected manual attack"""
        attack_type = self.attack_type_var.get()
        token = self.manual_token_entry.get().strip()
        wordlist = self.manual_wordlist_entry.get().strip()
        url = self.manual_url_entry.get().strip()
        
        # Validate token
        if not token:
            messagebox.showerror("Error", "JWT Token is required")
            return
        
        # Check if attack modules are available
        if not HAS_ATTACK_MODULES:
            messagebox.showerror("Error", "Attack modules are not available. Please check the logs.")
            return
        
        # Update status
        self.status_msg.set(f"Executing {attack_type}...")
        
        # Update results
        self.update_manual_results("", clear=True)
        self.update_manual_results(f"Executing {attack_type}\\n", "header")
        self.update_manual_results("=" * 50 + "\\n\\n")
        self.update_manual_results(f"JWT Token: {token}\\n\\n")
        
        # Execute attack in background thread
        def run_attack():'''
    
    # Substituir o método
    content = re.sub(method_pattern, replacement, content, flags=re.DOTALL)
    
    return content

def fix_scan_target(content):
    """Corrige o método scan_target para usar os módulos importados"""
    # Procurar o método scan_target
    method_pattern = r'def scan_target\(self\):.*?url = self\.url_entry\.get\(\)\.strip\(\)(.*?)def run_scan\(\):'
    
    replacement = r'''def scan_target(self):
        """Scan the target URL for JWT tokens and vulnerabilities"""
        # Get the URL
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a target URL")
            return
        
        # Check if attack modules are available
        if not HAS_ATTACK_MODULES:
            messagebox.showerror("Error", "Attack modules are not available. Please check the logs.")
            return
        
        # Validate URL format
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        
        # Get output file and verbose flag
        output_file = self.output_entry.get().strip() or None
        verbose = self.verbose_var.get()
        
        # Update status
        self.status_msg.set("Scanning target...")
        
        # Clear previous results
        self.scan_output_text.config(state=tk.NORMAL)
        self.scan_output_text.delete(1.0, tk.END)
        self.scan_output_text.config(state=tk.DISABLED)
        
        self.tokens_list.delete(0, tk.END)
        
        # Run scan in background thread
        def run_scan():'''
    
    # Substituir o método
    content = re.sub(method_pattern, replacement, content, flags=re.DOTALL)
    
    return content

def fix_execute_balance_injection(content):
    """Corrige o método execute_balance_injection para usar os módulos importados"""
    # Procurar o método execute_balance_injection
    method_pattern = r'def execute_balance_injection\(self\):.*?api_url = self\.api_url_entry\.get\(\)\.strip\(\)(.*?)def run_attack\(\):'
    
    replacement = r'''def execute_balance_injection(self):
        """Execute the balance injection attack"""
        # Get input values
        api_url = self.api_url_entry.get().strip()
        method = self.method_var.get()
        token = self.injection_token_entry.get().strip()
        current_balance = self.current_balance_entry.get().strip()
        new_balance = self.new_balance_entry.get().strip()
        balance_field = self.balance_field_entry.get().strip()
        request_body = self.request_body_text.get("1.0", tk.END).strip()
        
        # Check if attack modules are available
        if not HAS_ATTACK_MODULES:
            messagebox.showerror("Error", "Attack modules are not available. Please check the logs.")
            return
        
        # Validate inputs
        if not api_url:
            messagebox.showerror("Erro", "URL da API é obrigatória")
            return
            
        if not token:
            messagebox.showerror("Erro", "Token JWT é obrigatório")
            return
            
        if not new_balance:
            messagebox.showerror("Erro", "Novo valor de saldo é obrigatório")
            return
        
        # Update status
        self.status_msg.set("Executando ataque de injeção de saldo...")
        
        # Clear previous results
        self.update_injection_results("", clear=True)
        self.update_injection_results("Ataque de Injeção de Saldo\\n", "info")
        self.update_injection_results(f"Alvo: {api_url}\\n", "info")
        self.update_injection_results(f"Método: {method}\\n", "info")
        self.update_injection_results(f"Saldo Atual: {current_balance}\\n", "info")
        self.update_injection_results(f"Novo Saldo: {new_balance}\\n\\n", "info")
        
        # Run attack in background thread
        def run_attack():'''
    
    # Substituir o método
    content = re.sub(method_pattern, replacement, content, flags=re.DOTALL)
    
    return content

def apply_fixes():
    """Aplica todas as correções ao arquivo ai_interface.py"""
    file_path = Path("gui/ai_interface.py")
    
    if not file_path.exists():
        logger.error(f"Arquivo {file_path} não encontrado!")
        return False
    
    # Criar backup
    backup_path = backup_file(file_path)
    
    # Ler o conteúdo do arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Aplicar correções
    content = fix_imports(content)
    content = fix_analyze_token_method(content)
    content = fix_execute_manual_attack(content)
    content = fix_scan_target(content)
    content = fix_execute_balance_injection(content)
    
    # Salvar as alterações
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Correções aplicadas com sucesso ao arquivo {file_path}")
    logger.info(f"Backup do arquivo original salvo em {backup_path}")
    
    return True

if __name__ == "__main__":
    print("Aplicando correções à interface de IA do Evil Force JWT...")
    
    if apply_fixes():
        print("\n✅ Correções aplicadas com sucesso!")
        print("Agora você pode executar a interface com 'python gui/interface.py'")
    else:
        print("\n❌ Falha ao aplicar correções!")
        print("Verifique os logs para mais detalhes.") 