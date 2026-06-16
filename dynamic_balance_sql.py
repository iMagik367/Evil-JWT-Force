import sqlite3
import random
import logging
import threading
from typing import Optional, Tuple

DB_PATH = "output/balance.db"
TABLE_NAME = "accounts"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class SQLBalanceManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._ensure_table()

    def _connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _ensure_table(self):
        with self._connect() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    balance INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def update_balance(self, user_id: str) -> Tuple[int, int]:
        """Atualiza amount e balance para valores aleatórios e retorna os novos valores."""
        amount = random.randint(10000, 50000)
        balance = random.randint(10000, 50000)
        with self._lock, self._connect() as conn:
            conn.execute(
                f"""INSERT INTO {TABLE_NAME} (user_id, amount, balance)
                    VALUES (?, ?, ?)""",
                (user_id, amount, balance)
            )
            conn.commit()
        logging.info(f"Saldo atualizado para user_id={user_id}: amount={amount}, balance={balance}")
        return amount, balance

    def get_last_balance(self, user_id: str) -> Optional[Tuple[int, int]]:
        """Obtém o último amount e balance para o user_id informado."""
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                f"""SELECT amount, balance FROM {TABLE_NAME}
                    WHERE user_id = ?
                    ORDER BY updated_at DESC LIMIT 1""",
                (user_id,)
            )
            row = cur.fetchone()
            return (row[0], row[1]) if row else None

    def smart_update(self, user_id: str, min_value: int = 10000, max_value: int = 50000) -> Tuple[int, int]:
        """Atualiza amount/balance de forma inteligente, evitando repetições consecutivas."""
        last = self.get_last_balance(user_id)
        for _ in range(10):
            amount = random.randint(min_value, max_value)
            balance = random.randint(min_value, max_value)
            if not last or (amount, balance) != last:
                break
        return self.update_balance(user_id)

    def execute_custom_sql(self, sql: str, params: tuple = ()):
        """Executa comandos SQL customizados de forma segura."""
        with self._lock, self._connect() as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.fetchall()

# Exemplo de uso programático:
if __name__ == "__main__":
    manager = SQLBalanceManager()
    user = "usuario_teste"
    for _ in range(5):
        amount, balance = manager.smart_update(user)
        print(f"Novo saldo para {user}: amount={amount}, balance={balance}")