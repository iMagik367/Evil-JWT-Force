"""
Módulo de gerenciamento de wordlists para ataques de bruteforce.
"""

import os
import re
import logging
import json
import random
import time
from pathlib import Path
from typing import List, Set, Dict, Any, Optional

# Configuração de logging
logging.basicConfig(filename='logs/wordlist_manager.log', level=logging.INFO, format='[%(asctime)s] %(message)s')

class WordlistManager:
    """
    Gerenciador de wordlists para ataques de bruteforce e fuzzing.
    """
    def __init__(self, wordlist_path: Optional[str] = None):
        self.wordlist_path = wordlist_path
        self.wordlists: Dict[str, List[str]] = {}
        self.default_wordlist: List[str] = []
        self.loaded_files: Set[str] = set()
        
        # Carregar wordlist padrão se fornecida
        if wordlist_path and os.path.exists(wordlist_path):
            self.load_wordlist(wordlist_path, "default")
    
    def load_wordlist(self, filepath: str, name: str = "default") -> bool:
        """
        Carrega uma wordlist de um arquivo.
        
        Args:
            filepath: Caminho para o arquivo de wordlist
            name: Nome para identificar a wordlist
            
        Returns:
            True se a wordlist foi carregada com sucesso, False caso contrário
        """
        try:
            if not os.path.exists(filepath):
                logging.error(f"Arquivo de wordlist não encontrado: {filepath}")
                return False
            
            # Verificar se já foi carregado
            if filepath in self.loaded_files:
                logging.info(f"Wordlist já carregada: {filepath}")
                return True
            
            # Carregar wordlist
            words = []
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    word = line.strip()
                    if word:  # Ignorar linhas vazias
                        words.append(word)
            
            # Armazenar wordlist
            self.wordlists[name] = words
            self.loaded_files.add(filepath)
            
            # Se for a wordlist default, atualizar a referência
            if name == "default":
                self.default_wordlist = words
                self.wordlist_path = filepath
            
            logging.info(f"Wordlist '{name}' carregada com sucesso: {len(words)} palavras")
            return True
        
        except Exception as e:
            logging.error(f"Erro ao carregar wordlist '{name}' de {filepath}: {str(e)}")
            return False
    
    def get_wordlist(self, name: str = "default") -> List[str]:
        """
        Obtém uma wordlist pelo nome.
        
        Args:
            name: Nome da wordlist
            
        Returns:
            Lista de palavras
        """
        return self.wordlists.get(name, [])
    
    def filter_wordlist(self, pattern: str, name: str = "default") -> List[str]:
        """
        Filtra uma wordlist por um padrão regex.
        
        Args:
            pattern: Padrão regex para filtrar
            name: Nome da wordlist
            
        Returns:
            Lista de palavras filtradas
        """
        try:
            wordlist = self.get_wordlist(name)
            compiled_pattern = re.compile(pattern)
            filtered = [word for word in wordlist if compiled_pattern.search(word)]
            logging.info(f"Wordlist '{name}' filtrada com o padrão '{pattern}': {len(filtered)} resultados")
            return filtered
        except Exception as e:
            logging.error(f"Erro ao filtrar wordlist '{name}' com padrão '{pattern}': {str(e)}")
            return []
    
    def optimize_for_jwt(self, name: str = "default") -> List[str]:
        """
        Otimiza uma wordlist para ataques a JWT, reordenando e priorizando
        palavras mais prováveis de serem segredos.
        
        Args:
            name: Nome da wordlist
            
        Returns:
            Lista de palavras otimizada
        """
        wordlist = self.get_wordlist(name)
        
        # Critérios de prioridade para possíveis segredos JWT
        priority_words = []
        medium_priority = []
        other_words = []
        
        jwt_keywords = ["secret", "key", "jwt", "token", "auth", "signature", "sign", "secure", 
                       "password", "pass", "api", "hash", "security", "authentication"]
        
        for word in wordlist:
            # Palavras de alta prioridade (contêm keywords JWT ou têm tamanho adequado)
            if any(keyword in word.lower() for keyword in jwt_keywords) or (16 <= len(word) <= 64):
                priority_words.append(word)
            # Prioridade média (tem tamanho razoável ou contém caracteres especiais)
            elif (8 <= len(word) <= 32) or any(c in word for c in "!@#$%^&*()_+=-"):
                medium_priority.append(word)
            # Todas as outras palavras
            else:
                other_words.append(word)
        
        # Juntar as listas em ordem de prioridade
        optimized = priority_words + medium_priority + other_words
        logging.info(f"Wordlist '{name}' otimizada para JWT: {len(optimized)} palavras")
        return optimized
    
    def create_combined_wordlist(self, output_path: str, wordlist_names: List[str] = None) -> bool:
        """
        Cria uma wordlist combinada a partir de múltiplas wordlists.
        
        Args:
            output_path: Caminho para o arquivo de saída
            wordlist_names: Lista de nomes de wordlists a combinar
            
        Returns:
            True se a wordlist foi criada com sucesso, False caso contrário
        """
        try:
            # Se nenhuma wordlist específica for fornecida, usar todas as carregadas
            if not wordlist_names:
                wordlist_names = list(self.wordlists.keys())
            
            # Combinar wordlists
            combined_words = set()
            for name in wordlist_names:
                if name in self.wordlists:
                    combined_words.update(self.wordlists[name])
            
            # Remover duplicatas e converter para lista
            combined_list = list(combined_words)
            
            # Salvar wordlist combinada
            with open(output_path, 'w', encoding='utf-8') as f:
                for word in combined_list:
                    f.write(f"{word}\n")
            
            logging.info(f"Wordlist combinada criada com sucesso em {output_path}: {len(combined_list)} palavras")
            return True
        
        except Exception as e:
            logging.error(f"Erro ao criar wordlist combinada em {output_path}: {str(e)}")
            return False
    
    def add_mutations(self, name: str = "default") -> List[str]:
        """
        Adiciona mutações às palavras da wordlist.
        
        Args:
            name: Nome da wordlist
            
        Returns:
            Lista de palavras com mutações
        """
        try:
            wordlist = self.get_wordlist(name)
            mutated = set(wordlist)
            
            # Adicionar mutações comuns
            for word in wordlist:
                # Variações de caixa
                mutated.add(word.lower())
                mutated.add(word.upper())
                mutated.add(word.capitalize())
                
                # Substituições comuns
                mutated.add(word.replace('a', '@'))
                mutated.add(word.replace('o', '0'))
                mutated.add(word.replace('i', '1'))
                mutated.add(word.replace('e', '3'))
                mutated.add(word.replace('s', '$'))
                
                # Adições de números e caracteres especiais
                mutated.add(word + "123")
                mutated.add(word + "2024")
                mutated.add(word + "!")
                mutated.add(word + "_secret")
                mutated.add(word + "_key")
                
                # Inversões
                mutated.add(word[::-1])
            
            result = list(mutated)
            logging.info(f"Wordlist '{name}' com mutações: {len(result)} palavras (original: {len(wordlist)})")
            return result
        
        except Exception as e:
            logging.error(f"Erro ao adicionar mutações à wordlist '{name}': {str(e)}")
            return self.get_wordlist(name)
    
    def sample_wordlist(self, size: int, name: str = "default") -> List[str]:
        """
        Obtém uma amostra aleatória da wordlist.
        
        Args:
            size: Tamanho da amostra
            name: Nome da wordlist
            
        Returns:
            Lista com amostra da wordlist
        """
        wordlist = self.get_wordlist(name)
        if size >= len(wordlist):
            return wordlist
        return random.sample(wordlist, size)
    
    def get_statistics(self, name: str = "default") -> Dict[str, Any]:
        """
        Obtém estatísticas sobre a wordlist.
        
        Args:
            name: Nome da wordlist
            
        Returns:
            Dicionário com estatísticas
        """
        try:
            wordlist = self.get_wordlist(name)
            
            # Calcular estatísticas
            word_lengths = [len(word) for word in wordlist]
            char_classes = {
                'lowercase': sum(1 for word in wordlist if word.islower()),
                'uppercase': sum(1 for word in wordlist if word.isupper()),
                'mixed_case': sum(1 for word in wordlist if not word.islower() and not word.isupper() and word.isalpha()),
                'alphanumeric': sum(1 for word in wordlist if any(c.isdigit() for c in word) and any(c.isalpha() for c in word)),
                'special_chars': sum(1 for word in wordlist if any(not c.isalnum() for c in word)),
            }
            
            return {
                'total_words': len(wordlist),
                'unique_words': len(set(wordlist)),
                'min_length': min(word_lengths) if word_lengths else 0,
                'max_length': max(word_lengths) if word_lengths else 0,
                'avg_length': sum(word_lengths) / len(word_lengths) if word_lengths else 0,
                'char_classes': char_classes
            }
        
        except Exception as e:
            logging.error(f"Erro ao obter estatísticas da wordlist '{name}': {str(e)}")
            return {'error': str(e)}
    
    def save_to_file(self, wordlist: List[str], output_path: str) -> bool:
        """
        Salva uma wordlist em um arquivo.
        
        Args:
            wordlist: Lista de palavras
            output_path: Caminho para o arquivo de saída
            
        Returns:
            True se a wordlist foi salva com sucesso, False caso contrário
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for word in wordlist:
                    f.write(f"{word}\n")
            logging.info(f"Wordlist salva com sucesso em {output_path}: {len(wordlist)} palavras")
            return True
        except Exception as e:
            logging.error(f"Erro ao salvar wordlist em {output_path}: {str(e)}")
            return False
    
    def generate_wordlist_from_data(self, data: Dict[str, Any], output_path: str) -> bool:
        """
        Gera uma wordlist a partir de dados específicos do alvo.
        
        Args:
            data: Dicionário com dados do alvo
            output_path: Caminho para o arquivo de saída
            
        Returns:
            True se a wordlist foi gerada com sucesso, False caso contrário
        """
        try:
            generated = set()
            
            # Extrair palavras de dados do alvo
            for key, value in data.items():
                if isinstance(value, str):
                    words = re.findall(r'\w+', value)
                    generated.update(words)
                    # Adicionar variações
                    generated.add(value)
                    generated.add(value.lower())
                    generated.add(value.replace(' ', ''))
                elif isinstance(value, (list, tuple)):
                    for item in value:
                        if isinstance(item, str):
                            words = re.findall(r'\w+', item)
                            generated.update(words)
                            # Adicionar variações
                            generated.add(item)
                            generated.add(item.lower())
                            generated.add(item.replace(' ', ''))
            
            # Adicionar combinações de palavras-chave comuns
            if 'company' in data:
                company = data['company']
                if isinstance(company, str):
                    generated.add(company + "_secret")
                    generated.add(company.lower() + "_key")
                    generated.add(company.lower() + "jwt")
                    generated.add(company.lower() + "2024")
            
            if 'domain' in data:
                domain = data['domain']
                if isinstance(domain, str):
                    generated.add(domain + "_secret")
                    generated.add(domain.lower() + "_key")
                    generated.add(domain.split('.')[0] + "_secret")
            
            # Salvar wordlist gerada
            wordlist = list(generated)
            return self.save_to_file(wordlist, output_path)
        
        except Exception as e:
            logging.error(f"Erro ao gerar wordlist a partir de dados: {str(e)}")
            return False 