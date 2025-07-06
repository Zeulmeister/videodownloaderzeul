# src/core/stats.py

"""
Módulo para gerenciamento de estatísticas da aplicação.

Rastreia métricas como o número total de downloads e o total de
bytes baixados, salvando os dados em um arquivo JSON.
"""

import json
import os
import threading

STATS_FILE = "downloader_stats.json"
DEFAULT_STATS = {
    "total_downloads": 0,
    "total_bytes_downloaded": 0,
}

class StatsManager:
    """Gerencia as estatísticas de uso da aplicação de forma thread-safe."""

    def __init__(self):
        self._stats = self.load_stats()
        # Usar um lock é crucial para evitar que múltiplas threads de download
        # tentem escrever no arquivo ao mesmo tempo, o que corromperia os dados.
        self._lock = threading.Lock()

    def load_stats(self) -> dict:
        """Carrega as estatísticas do arquivo JSON."""
        if not os.path.exists(STATS_FILE):
            return DEFAULT_STATS.copy()
        
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                # Garante que todas as chaves padrão existam no arquivo carregado
                for key, value in DEFAULT_STATS.items():
                    stats.setdefault(key, value)
                return stats
        except (json.JSONDecodeError, IOError):
            return DEFAULT_STATS.copy()

    def _save_stats(self):
        """Salva as estatísticas atuais no arquivo JSON de forma segura."""
        with self._lock:
            try:
                with open(STATS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self._stats, f, indent=4)
            except IOError as e:
                print(f"Erro ao salvar o arquivo de estatísticas: {e}")

    def increment_download_count(self, count: int = 1):
        """Incrementa o contador total de downloads."""
        self._stats["total_downloads"] += count
        self._save_stats()

    def add_bytes_downloaded(self, byte_count: int):
        """Adiciona o número de bytes ao total baixado."""
        if byte_count and isinstance(byte_count, (int, float)):
            self._stats["total_bytes_downloaded"] += byte_count
            self._save_stats()

    def get_stats(self) -> dict:
        """Retorna uma cópia do dicionário de estatísticas."""
        return self._stats.copy()
