# src/core/exceptions.py

"""
Módulo para exceções customizadas da aplicação.

Definir exceções específicas nos ajuda a tratar erros de forma mais granular
e a fornecer feedback mais preciso para o usuário.
"""

class SuperDownloaderException(Exception):
    """Classe base para todas as exceções customizadas do projeto."""
    pass

class DownloaderError(SuperDownloaderException):
    """Exceção genérica para erros que ocorrem durante o processo de download."""
    pass

class NetworkError(DownloaderError):
    """Lançada quando há um problema de rede (ex: sem conexão, DNS falhou)."""
    pass

class InvalidURLError(DownloaderError):
    """Lançada quando a URL fornecida é inválida ou não suportada."""
    pass

class FormatSelectionError(DownloaderError):
    """Lançada quando há um erro na seleção de formato de vídeo ou áudio."""
    pass

class FileSystemError(DownloaderError):
    """Lançada para erros relacionados ao sistema de arquivos (ex: permissão negada, disco cheio)."""
    pass
