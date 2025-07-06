# src/core/history.py

"""
Módulo para gerenciamento do histórico de downloads.

Usa o mesmo banco de dados SQLite do cache para manter um registro
persistente de todos os downloads concluídos com sucesso.
"""

import sqlite3
import json
import datetime
import os
from .config import load_config

class HistoryManager:
    """Gerencia o armazenamento e recuperação do histórico de downloads."""

    def __init__(self):
        """Inicializa o HistoryManager."""
        config = load_config()
        db_folder = config.get('download_path', 'downloads')
        os.makedirs(db_folder, exist_ok=True)
        
        self.db_path = os.path.join(db_folder, 'cache.db') # Usando o mesmo DB do cache
        self._create_table()

    def _get_connection(self):
        """Retorna uma conexão com o banco de dados SQLite."""
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        """Cria a tabela de histórico se ela não existir."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    download_date TIMESTAMP NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Completed'
                )
            """)
            conn.commit()

    def add_entry(self, title: str, url: str, size_bytes: int):
        """
        Adiciona uma nova entrada ao histórico de downloads.

        Args:
            title (str): O título do vídeo.
            url (str): A URL original do vídeo.
            size_bytes (int): O tamanho do arquivo baixado em bytes.
        """
        download_date = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO download_history (title, url, download_date, size_bytes) VALUES (?, ?, ?, ?)",
                (title, url, download_date, size_bytes)
            )
            conn.commit()

    def get_all_entries(self) -> list:
        """
        Recupera todas as entradas do histórico, ordenadas pela mais recente.

        Returns:
            list: Uma lista de tuplas, onde cada tupla representa um registro.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title, url, download_date, size_bytes, status FROM download_history ORDER BY download_date DESC")
            return cursor.fetchall()

    def clear_history(self):
        """Limpa todos os registros da tabela de histórico."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM download_history")
            conn.commit()
