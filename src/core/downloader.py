# src/core/downloader.py

import yt_dlp
from .config import load_config
from .stats import StatsManager
from .exceptions import DownloaderError, NetworkError, InvalidURLError, FileSystemError, FormatSelectionError
from . import validators
from .cache import CacheManager
from .history import HistoryManager

class Downloader:
    class _YdlLogger:
        def __init__(self, gui_log_callback):
            self.log = gui_log_callback
        def debug(self, msg): pass
        def warning(self, msg): self.log(msg, 'warning')
        def error(self, msg): self.log(msg, 'error')

    def __init__(self, logger_callback=print):
        self.config = load_config()
        self.stats_manager = StatsManager()
        self.logger = logger_callback
        self.ydl_logger = self._YdlLogger(logger_callback)
        self.cache_manager = CacheManager()
        self.history_manager = HistoryManager()

    def _get_base_ydl_opts(self, download_playlist=False):
        """Retorna as opções base para o yt-dlp, incluindo o controle de playlist."""
        return {
            'outtmpl': f"{self.config.get('download_path', 'downloads')}/%(title)s.%(ext)s",
            'progress_hooks': [self._progress_hook],
            'logger': self.ydl_logger,
            'noplaylist': not download_playlist,
            'ignoreerrors': download_playlist, # Ignora erros em vídeos individuais de uma playlist
            'merge_output_format': 'mp4',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
        }
    
    def _validate_prerequisites(self, url: str):
        self.logger("Executando validações de pré-requisitos...", "info")
        validators.validate_url(url); download_path = self.config.get('download_path', 'downloads'); validators.validate_download_path(download_path); validators.validate_disk_space(download_path)
        self.logger("Validações concluídas com sucesso.", "info")

    def _progress_hook(self, d):
        if d['status'] == 'finished': self.stats_manager.increment_download_count(); self.stats_manager.add_bytes_downloaded(d.get('total_bytes', 0))

    def extract_info(self, url: str, download_playlist: bool = False) -> dict:
        self._validate_prerequisites(url)
        if not download_playlist:
            cached_info = self.cache_manager.get_info(url)
            if cached_info: self.logger(f"Informações para '{cached_info.get('title', url)}' encontradas no cache.", "info"); return cached_info
        
        self.logger(f"Buscando informações para '{url}' na web... (Playlist: {'Sim' if download_playlist else 'Não'})", "info")
        try:
            opts = self._get_base_ydl_opts(download_playlist=download_playlist); opts['progress_hooks'] = []
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not download_playlist: self.cache_manager.save_info(url, info)
                self.logger(f"Informações para '{info.get('title')}' obtidas com sucesso.", "info")
                return info
        except yt_dlp.utils.DownloadError as e: raise DownloaderError(f"Não foi possível extrair informações: {e}") from e
        except Exception as e: raise DownloaderError(f"Um erro inesperado ocorreu ao extrair informações: {e}") from e

    def download(self, url: str, format_code: str, download_playlist: bool = False):
        self._validate_prerequisites(url)
        self.logger(f"Iniciando download para: {url} | Formato: '{format_code}' | Playlist: {'Sim' if download_playlist else 'Não'}", "info")
        if not format_code: raise FormatSelectionError("Nenhum formato de download foi selecionado.")
        ydl_opts = self._get_base_ydl_opts(download_playlist=download_playlist); ydl_opts['format'] = format_code
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: info = ydl.extract_info(url, download=True)
            entry_list = info.get('entries') if download_playlist else [info]
            for entry in entry_list:
                if entry: self.history_manager.add_entry(title=entry.get('title', 'Título desconhecido'), url=entry.get('webpage_url', url), size_bytes=entry.get('filesize', 0) or entry.get('filesize_approx', 0))
            self.logger("Download salvo no histórico com sucesso.", "info")
        except yt_dlp.utils.DownloadError as e:
            error_message = str(e).lower()
            if "unsupported url" in error_message or "invalid url" in error_message: raise InvalidURLError(f"A URL fornecida não é suportada ou é inválida: {url}")
            if "name or service not known" in error_message or "no route to host" in error_message: raise NetworkError("Erro de rede. Verifique sua conexão com a internet.")
            if "permission denied" in error_message or "disk quota exceeded" in error_message: raise FileSystemError("Erro de sistema de arquivos. Verifique as permissões ou espaço em disco.")
            raise DownloaderError(f"Ocorreu um erro durante o download: {e}")
        except Exception as e:
            self.logger(f"Erro inesperado capturado: {e}", "critical"); raise DownloaderError(f"Um erro inesperado ocorreu: {e}")

    def download_audio(self, url: str, audio_format: str, download_playlist: bool = False):
        self._validate_prerequisites(url)
        self.logger(f"Iniciando download de áudio para: {url} | Formato: {audio_format} | Playlist: {'Sim' if download_playlist else 'Não'}", "info")
        ydl_opts = self._get_base_ydl_opts(download_playlist=download_playlist)
        if audio_format == 'flac':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'flac'}]
        else:
            ydl_opts['format'] = audio_format
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: info = ydl.extract_info(url, download=True)
            entry_list = info.get('entries') if download_playlist else [info]
            for entry in entry_list:
                if entry: self.history_manager.add_entry(title=entry.get('title', 'Título desconhecido'), url=entry.get('webpage_url', url), size_bytes=entry.get('filesize', 0) or entry.get('filesize_approx', 0))
            self.logger("Download de áudio salvo no histórico com sucesso.", "info")
        except yt_dlp.utils.DownloadError as e: raise DownloaderError(f"Ocorreu um erro durante o download do áudio: {e}")
        except Exception as e: self.logger(f"Erro inesperado capturado: {e}", "critical"); raise DownloaderError(f"Um erro inesperado ocorreu: {e}")
