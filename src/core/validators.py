# src/core/validators.py

"""
Módulo para funções de validação.

Centraliza todas as verificações de pré-requisitos antes de iniciar um download,
como validação de URL, permissões de diretório e espaço em disco.
"""

import os
import re
import shutil
from .exceptions import InvalidURLError, FileSystemError

# Regex simples para uma verificação básica de URL.
# Não precisa ser perfeito, mas ajuda a evitar entradas claramente inválidas.
URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://'  # http:// ou https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domínio...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...ou IP
    r'(?::\d+)?'  # porta opcional
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def validate_url(url: str):
    """
    Valida o formato da URL.

    Lança:
        InvalidURLError: Se a URL estiver vazia ou tiver um formato inválido.
    """
    if not url:
        raise InvalidURLError("A URL não pode estar vazia.")
    if not re.match(URL_REGEX, url):
        raise InvalidURLError(f"O formato da URL fornecida é inválido: '{url[:50]}...'")

def validate_download_path(path: str):
    """
    Verifica se o caminho de download existe e se temos permissão para escrever nele.
    Tenta criar o diretório se ele não existir.

    Lança:
        FileSystemError: Se o caminho não puder ser criado ou não tiver permissão de escrita.
    """
    try:
        # Tenta criar o diretório, incluindo os pais. 'exist_ok=True' não lança erro se já existir.
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        raise FileSystemError(f"Não foi possível criar o diretório de download '{path}'. Erro: {e}")

    if not os.access(path, os.W_OK):
        raise FileSystemError(f"Sem permissão de escrita no diretório '{path}'.")

def validate_disk_space(path: str, min_space_mb: int = 50):
    """
    Verifica se há um espaço mínimo em disco disponível no caminho fornecido.

    Lança:
        FileSystemError: Se o espaço livre for menor que o mínimo necessário.
    """
    try:
        _, _, free_bytes = shutil.disk_usage(path)
        free_mb = free_bytes / (1024 * 1024)

        if free_mb < min_space_mb:
            raise FileSystemError(
                f"Espaço em disco insuficiente. Necessário pelo menos {min_space_mb} MB, "
                f"mas apenas {free_mb:.2f} MB estão disponíveis em '{path}'."
            )
    except FileNotFoundError:
        raise FileSystemError(f"O caminho '{path}' não foi encontrado para verificar o espaço em disco.")

