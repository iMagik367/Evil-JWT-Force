"""
Utilitários para manipulação de wordlists
"""

import os
import logging
from termcolor import colored

logger = logging.getLogger("EVIL_JWT_FORCE.wordlist_utils")

def save_wordlist(words, filename):
    """
    Salva uma lista de palavras em um arquivo de texto.
    
    Args:
        words (list): Lista de palavras para salvar
        filename (str): Caminho do arquivo de saída
        
    Returns:
        str: Caminho do arquivo salvo
    """
    try:
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Escrever palavras no arquivo
        with open(filename, 'w', encoding='utf-8') as f:
            for word in words:
                f.write(f"{word}\n")
        
        logger.info(f"Wordlist salva com {len(words)} palavras em {filename}")
        print(colored(f"[✓] Wordlist salva com {len(words)} palavras em {filename}", "green"))
        return filename
    except Exception as e:
        logger.error(f"Erro ao salvar wordlist: {e}")
        print(colored(f"[x] Erro ao salvar wordlist: {e}", "red"))
        return None

def load_wordlist(filename):
    """
    Carrega uma wordlist de um arquivo.
    
    Args:
        filename (str): Caminho do arquivo de entrada
        
    Returns:
        list: Lista de palavras carregadas
    """
    try:
        if not os.path.exists(filename):
            logger.warning(f"Arquivo não encontrado: {filename}")
            print(colored(f"[!] Arquivo não encontrado: {filename}", "yellow"))
            return []
            
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            words = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Wordlist carregada com {len(words)} palavras de {filename}")
        print(colored(f"[✓] Wordlist carregada com {len(words)} palavras", "green"))
        return words
    except Exception as e:
        logger.error(f"Erro ao carregar wordlist: {e}")
        print(colored(f"[x] Erro ao carregar wordlist: {e}", "red"))
        return []

def filter_wordlist(words, min_length=4, max_length=32, custom_filter=None):
    """
    Filtra uma wordlist com base em critérios específicos.
    
    Args:
        words (list): Lista de palavras para filtrar
        min_length (int): Comprimento mínimo das palavras
        max_length (int): Comprimento máximo das palavras
        custom_filter (callable): Função de filtro personalizada
        
    Returns:
        list: Lista de palavras filtradas
    """
    filtered = [w for w in words if min_length <= len(w) <= max_length]
    
    if custom_filter and callable(custom_filter):
        filtered = [w for w in filtered if custom_filter(w)]
    
    logger.info(f"Wordlist filtrada: {len(words)} -> {len(filtered)} palavras")
    return filtered

def merge_wordlists(wordlists):
    """
    Combina múltiplas wordlists removendo duplicatas.
    
    Args:
        wordlists (list): Lista de listas de palavras
        
    Returns:
        list: Lista combinada sem duplicatas
    """
    combined = set()
    for wordlist in wordlists:
        combined.update(wordlist)
    
    return sorted(list(combined))

def generate_variations(word):
    """
    Gera variações de uma palavra (maiúsculas, minúsculas, capitalizada, etc).
    
    Args:
        word (str): Palavra base
        
    Returns:
        list: Lista de variações
    """
    variations = [
        word,
        word.lower(),
        word.upper(),
        word.capitalize(),
        word + "123",
        word + "!",
        word + "@",
        word + "2023",
        word + "2024",
        word.replace('a', '@'),
        word.replace('e', '3'),
        word.replace('i', '1'),
        word.replace('o', '0'),
        word.replace('s', '$')
    ]
    
    return list(set(variations))  # Remove duplicatas

if __name__ == "__main__":
    # Teste das funções
    test_words = ["password", "admin", "secret", "key"]
    save_wordlist(test_words, "output/test_wordlist.txt")
    loaded = load_wordlist("output/test_wordlist.txt")
    print(f"Palavras carregadas: {loaded}")
    
    variations = []
    for word in test_words:
        variations.extend(generate_variations(word))
    
    print(f"Variações geradas: {len(variations)}")
    save_wordlist(variations, "output/variations.txt") 