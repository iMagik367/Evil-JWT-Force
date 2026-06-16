class WordlistEngine:
    def __init__(self, base_wordlist=None):
        self.base_wordlist = base_wordlist or []
        self.generated_list = []

    def generate(self, size=1000):
        """Gera uma wordlist com base em uma lista base ou padrões."""
        if not self.base_wordlist:
            self.generated_list = [f"password{i}" for i in range(size)]
        else:
            self.generated_list = self.base_wordlist[:size]
        return self.generated_list

    def save_to_file(self, filepath):
        """Salva a wordlist gerada em um arquivo."""
        with open(filepath, 'w') as f:
            for word in self.generated_list:
                f.write(f"{word}\n")
        return filepath 