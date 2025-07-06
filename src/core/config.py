# src/core/config.py

"""
Módulo para carregar e salvar as configurações da aplicação.

Gerencia um arquivo JSON (downloader_config.json) para persistir
as preferências do usuário, como o caminho de download.
"""

import json
import os

CONFIG_FILE = "downloader_config.json"
DEFAULT_CONFIG = {
    "download_path": "downloads",
    "max_resolution": "1080",
    "download_playlist": False,
}

def load_config() -> dict:
    """
    Carrega a configuração do arquivo JSON.

    Se o arquivo não existir, ele será criado com os valores padrão.
    Se o arquivo estiver corrompido, ele retornará os valores padrão.

    Returns:
        dict: O dicionário de configurações.
    """
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Garante que todas as chaves padrão existam
            for key, value in DEFAULT_CONFIG.items():
                config.setdefault(key, value)
            return config
    except (json.JSONDecodeError, IOError):
        # Em caso de arquivo corrompido ou erro de leitura, retorna o padrão
        return DEFAULT_CONFIG

def save_config(config: dict):
    """
    Salva o dicionário de configuração fornecido no arquivo JSON.

    Args:
        config (dict): O dicionário de configurações a ser salvo.
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except IOError as e:
        print(f"Erro ao salvar o arquivo de configuração: {e}")

