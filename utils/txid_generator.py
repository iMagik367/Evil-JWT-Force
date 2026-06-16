import random
import string


def generate_realistic_txid():
    """Gera um TXID realístico de 35 caracteres"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=35)) 