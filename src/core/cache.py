# src/core/cache.py

"""
Módulo para gerenciamento de cache de metadados de vídeos.

Usa um banco de dados SQLite para armazenar informações extraídas,
evitando requisições repetidas para a mesma URL e acelerando a resposta da aplicação.
"""

import sqlite3
import json
import datetime
import os
from .config import load_config

class CacheManager:
    """Gerencia o armazenamento e recuperação de metadados de vídeo em um banco de dados SQLite."""

    def __init__(self, ttl_days: int = 7):
        """
        Inicializa o CacheManager.

        Args:
            ttl_days (int): Tempo de vida (em dias) para os dados em cache.
        """
        config = load_config()
        # Armazena o banco de dados na pasta de downloads para portabilidade
        db_folder = config.get('download_path', 'downloads')
        os.makedirs(db_folder, exist_ok=True)
        
        self.db_path = os.path.join(db_folder, 'cache.db')
        self.ttl = datetime.timedelta(days=ttl_days)
        self._create_table()

    def _get_connection(self):
        """Retorna uma conexão com o banco de dados SQLite."""
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        """Cria a tabela de cache se ela não existir."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_cache (
                    url TEXT PRIMARY KEY,
                    info_json TEXT NOT NULL,
                    cached_at TIMESTAMP NOT NULL
                )
            """)
            conn.commit()

    def get_info(self, url: str) -> dict | None:
        """
        Recupera informações de uma URL do cache, se existirem e não estiverem expiradas.

        Args:
            url (str): A URL do vídeo.

        Returns:
            dict | None: O dicionário de informações ou None se não estiver em cache ou expirado.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT info_json, cached_at FROM video_cache WHERE url = ?", (url,))
            result = cursor.fetchone()

            if result:
                info_json, cached_at_str = result
                cached_at = datetime.datetime.fromisoformat(cached_at_str)
                
                if datetime.datetime.now() - cached_at < self.ttl:
                    return json.loads(info_json)
        return None

    def save_info(self, url: str, info: dict):
        """
        Salva as informações de um vídeo no cache.

        Args:
            url (str): A URL do vídeo.
            info (dict): O dicionário de informações retornado pelo yt-dlp.
        """
        info_json = json.dumps(info)
        cached_at = datetime.datetime.now().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO video_cache (url, info_json, cached_at) VALUES (?, ?, ?)",
                (url, info_json, cached_at)
            )
            conn.commit()

    def clear_cache(self):
        """Limpa todos os dados da tabela de cache."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM video_cache")
            conn.commit()

