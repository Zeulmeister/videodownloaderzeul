# src/gui/main_window.py

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import io
import datetime
from PIL import Image, ImageTk
import requests

from ..core.downloader import Downloader
from ..core.config import load_config
from ..core.exceptions import DownloaderError, NetworkError, InvalidURLError, FileSystemError, FormatSelectionError
from ..core.history import HistoryManager

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Super Downloader v7.1 - Playlist Robusta")
        self.root.geometry("800x750")

        self.config = load_config()
        self.downloader = Downloader(logger_callback=self.log)
        self.history_manager = HistoryManager()
        self.video_info = None
        self.available_formats = {'video': [], 'audio': []}

        self._create_widgets()
        self.load_history()

    def _create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        self._create_download_tab()
        self._create_history_tab()

    def _create_download_tab(self):
        download_frame = ttk.Frame(self.notebook)
        self.notebook.add(download_frame, text='Download')

        url_frame = ttk.LabelFrame(download_frame, text="URL do Vídeo")
        url_frame.pack(pady=5, padx=10, fill="x")
        
        search_widget_frame = ttk.Frame(url_frame)
        search_widget_frame.pack(pady=5, padx=10, fill="x", expand=True)
        self.url_entry = ttk.Entry(search_widget_frame, width=70)
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.search_button = ttk.Button(search_widget_frame, text="Procurar", command=self.fetch_video_info_thread)
        self.search_button.pack(side="left", padx=(5, 0))

        self.playlist_var = tk.BooleanVar()
        playlist_check = ttk.Checkbutton(url_frame, text="Baixar playlist inteira, se disponível", variable=self.playlist_var, command=self.fetch_video_info_thread)
        playlist_check.pack(pady=5, padx=10, anchor="w")

        info_options_frame = ttk.Frame(download_frame); info_options_frame.pack(pady=10, padx=10, fill="both", expand=True)
        info_frame = ttk.LabelFrame(info_options_frame, text="Informações"); info_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.thumbnail_label = ttk.Label(info_frame); self.thumbnail_label.pack(pady=10)
        self.title_label = ttk.Label(info_frame, text="Título: (Aguardando URL...)", wraplength=350, font=("Segoe UI", 10, "bold")); self.title_label.pack(anchor="w", pady=5, padx=10)
        self.uploader_label = ttk.Label(info_frame, text="Canal: ", wraplength=350); self.uploader_label.pack(anchor="w", pady=2, padx=10)
        self.details_label = ttk.Label(info_frame, text="Detalhes: ", wraplength=350); self.details_label.pack(anchor="w", pady=2, padx=10)
        options_frame = ttk.LabelFrame(info_options_frame, text="Opções de Download"); options_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        ttk.Label(options_frame, text="Qualidade de Vídeo:").pack(anchor="w", padx=10, pady=(10,0)); self.video_format_combo = ttk.Combobox(options_frame, state="readonly"); self.video_format_combo.pack(fill="x", padx=10, pady=5)
        ttk.Label(options_frame, text="Qualidade de Áudio:").pack(anchor="w", padx=10, pady=(10,0)); self.audio_format_combo = ttk.Combobox(options_frame, state="readonly"); self.audio_format_combo.pack(fill="x", padx=10, pady=5)
        action_log_frame = ttk.Frame(download_frame); action_log_frame.pack(pady=10, padx=10, fill="both", expand=True)
        buttons_frame = ttk.Frame(action_log_frame); buttons_frame.pack(pady=5)
        self.download_video_button = ttk.Button(buttons_frame, text="Baixar Vídeo Completo", command=self.start_video_download_thread, state="disabled"); self.download_video_button.pack(side="left", padx=5)
        self.download_audio_button = ttk.Button(buttons_frame, text="Baixar Apenas Áudio", command=self.start_audio_download_thread, state="disabled"); self.download_audio_button.pack(side="left", padx=5)
        log_frame = ttk.LabelFrame(action_log_frame, text="Logs"); log_frame.pack(fill="both", expand=True, pady=(10,0))
        self.log_text = tk.Text(log_frame, height=8, state="disabled", wrap="word"); self.log_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview); log_scrollbar.pack(side="right", fill="y", pady=5, padx=(0,5)); self.log_text.config(yscrollcommand=log_scrollbar.set)

    def fetch_video_info_thread(self):
        url = self.url_entry.get()
        if not url: return
        self.log(f"Buscando informações para a URL...", "info")
        self._set_ui_state(search_state='disabled', download_state='disabled')
        download_playlist = self.playlist_var.get()
        threading.Thread(target=self.run_fetch_info, args=(url, download_playlist), daemon=True).start()

    def run_fetch_info(self, url, download_playlist):
        try:
            self.video_info = self.downloader.extract_info(url, download_playlist=download_playlist)
            self.root.after(0, self.update_video_info_widgets)
        except (InvalidURLError, NetworkError, DownloaderError) as e:
            self.log(f"Erro ao buscar informações: {e}", "error")
            self.root.after(0, self.clear_video_info_widgets)
        finally:
            if self.video_info and self.video_info.get('entries', [self.video_info])[0] is not None:
                self.root.after(0, lambda: self._set_ui_state(search_state='normal', download_state='normal'))
            else:
                self.root.after(0, lambda: self._set_ui_state(search_state='normal', download_state='disabled'))

    def update_video_info_widgets(self):
        if not self.video_info: return
        
        is_playlist = self.playlist_var.get() and self.video_info.get('_type') == 'playlist'
        
        thumbnail_url = None
        if is_playlist:
            all_entries = self.video_info.get('entries', [])
            valid_entries = [entry for entry in all_entries if entry]
            total_count = self.video_info.get('entry_count') or len(all_entries)
            available_count = len(valid_entries)

            if available_count == 0:
                self.log("Nenhum vídeo disponível nesta playlist foi encontrado.", "error")
                self.clear_video_info_widgets(); return

            if available_count < total_count:
                self.log(f"Aviso: {total_count - available_count} vídeo(s) indisponível(is) e foram ignorados.", "warning")

            title = self.video_info.get('title', 'Título da playlist não encontrado')
            uploader = valid_entries[0].get('uploader', 'Canal não encontrado') if valid_entries else 'N/A'
            self.title_label.config(text=f"Playlist: {title}")
            self.uploader_label.config(text=f"Canal: {uploader}")
            self.details_label.config(text=f"Vídeos: {available_count} de {total_count} disponíveis")
            if valid_entries: thumbnail_url = valid_entries[0].get('thumbnail')
        else:
            title = self.video_info.get('title', 'Título não encontrado')
            uploader = self.video_info.get('uploader', 'Canal não encontrado')
            duration_seconds = self.video_info.get('duration', 0)
            duration_str = f"{duration_seconds // 60:02}:{duration_seconds % 60:02}" if duration_seconds else "N/A"
            self.title_label.config(text=f"Título: {title}")
            self.uploader_label.config(text=f"Canal: {uploader}")
            self.details_label.config(text=f"Duração: {duration_str}")
            thumbnail_url = self.video_info.get('thumbnail')

        self.populate_format_selectors()
        self._set_ui_state("normal", "normal")
        if thumbnail_url: threading.Thread(target=self._load_thumbnail, args=(thumbnail_url,), daemon=True).start()

    def populate_format_selectors(self):
        self.available_formats = {'video': [], 'audio': []}; video_display_list = []; audio_display_list = []
        
        is_playlist = self.playlist_var.get() and self.video_info.get('_type') == 'playlist'
        
        if is_playlist:
            valid_entries = [entry for entry in self.video_info.get('entries', []) if entry]
            if not valid_entries:
                self.log("Não foi possível encontrar formatos, pois não há vídeos válidos na playlist.", "error")
                self.video_format_combo.set("Erro"); self.audio_format_combo.set("Erro")
                return
            formats_source = valid_entries[0]
        else:
            formats_source = self.video_info

        try:
            video_formats = [f for f in formats_source.get('formats', []) if f and f.get('vcodec', 'none').startswith('avc1') and f.get('acodec') == 'none']
            audio_formats = [f for f in formats_source.get('formats', []) if f and f.get('ext') == 'm4a' and f.get('acodec', 'none').startswith('mp4a')]
            best_videos = {};
            for f in sorted(video_formats, key=lambda x: (x.get('filesize') or x.get('filesize_approx') or 0), reverse=True):
                height = f.get('height')
                if height and height not in best_videos: best_videos[height] = f
            sorted_videos = sorted(best_videos.values(), key=lambda x: (x.get('height') or 0), reverse=True)
            sorted_audios = sorted(audio_formats, key=lambda x: (x.get('abr') or 0), reverse=True)
            audio_display_list.append("FLAC (Melhor Qualidade)"); self.available_formats['audio'].append({'text': "FLAC (Melhor Qualidade)", 'id': 'flac'})
            for f in sorted_videos:
                filesize = self.format_bytes(f.get('filesize') or f.get('filesize_approx')); fps_str = f"({f['fps']}fps) " if f.get('fps') else ""
                display_text = f"{f.get('height')}p {fps_str}- {f.get('ext')} [{filesize}]"
                self.available_formats['video'].append({'text': display_text, 'id': f['format_id']}); video_display_list.append(display_text)
            for f in sorted_audios:
                filesize = self.format_bytes(f.get('filesize') or f.get('filesize_approx')); abr_val = f.get('abr')
                display_text = f"{round(abr_val)}kbps - {f.get('ext')} [{filesize}]" if abr_val else f"{f.get('ext')} [{filesize}]"
                self.available_formats['audio'].append({'text': display_text, 'id': f['format_id']}); audio_display_list.append(display_text)
        except Exception as e: self.log(f"Erro ao processar formatos: {e}", "error"); video_display_list, audio_display_list = [], []
        self.video_format_combo['values'] = video_display_list; self.audio_format_combo['values'] = audio_display_list
        if video_display_list: self.video_format_combo.current(0)
        else: self.video_format_combo.set("Nenhum formato compatível")
        if audio_display_list: self.audio_format_combo.current(0)
        else: self.audio_format_combo.set("Nenhum formato compatível")

    def start_video_download_thread(self):
        download_playlist = self.playlist_var.get()
        url = self.url_entry.get()
        if not url: messagebox.showwarning("URL Vazia", "Por favor, insira uma URL para baixar."); return
        try:
            selected_video_text = self.video_format_combo.get(); selected_audio_text = self.audio_format_combo.get()
            video_id = next((f['id'] for f in self.available_formats['video'] if f['text'] == selected_video_text), None)
            audio_id = next((f['id'] for f in self.available_formats['audio'] if f['text'] == selected_audio_text), None)
            if audio_id == 'flac': raise FormatSelectionError("FLAC é apenas para download de áudio. Escolha outro formato de áudio para baixar o vídeo completo.")
            if not video_id or not audio_id: raise FormatSelectionError("Selecione um formato de vídeo e áudio válido.")
            format_code = f"{video_id}+{audio_id}"
        except Exception as e: messagebox.showerror("Erro de Formato", str(e)); return
        self._set_ui_state('disabled', 'disabled')
        self.log(f"Preparando para baixar VÍDEO: {self.video_info.get('title', url)}", "info")
        threading.Thread(target=self.run_video_download, args=(url, format_code, download_playlist), daemon=True).start()

    def start_audio_download_thread(self):
        download_playlist = self.playlist_var.get()
        url = self.url_entry.get()
        if not url: messagebox.showwarning("URL Vazia", "Por favor, insira uma URL para baixar."); return
        try:
            selected_audio_text = self.audio_format_combo.get()
            if not selected_audio_text: raise FormatSelectionError("Selecione um formato de áudio.")
            audio_id = next((f['id'] for f in self.available_formats['audio'] if f['text'] == selected_audio_text), None)
            if not audio_id: raise FormatSelectionError("Formato de áudio inválido selecionado.")
        except Exception as e: messagebox.showerror("Erro de Formato", str(e)); return
        self._set_ui_state('disabled', 'disabled')
        self.log(f"Preparando para baixar ÁUDIO: {self.video_info.get('title', url)}", "info")
        threading.Thread(target=self.run_audio_download, args=(url, audio_id, download_playlist), daemon=True).start()

    # --- Métodos restantes (sem alterações significativas) ---
    def _create_widgets(self): self.notebook = ttk.Notebook(self.root); self.notebook.pack(pady=10, padx=10, fill="both", expand=True); self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change); self._create_download_tab(); self._create_history_tab()
    def _set_ui_state(self, search_state='normal', download_state='disabled'): self.url_entry.config(state=search_state); self.search_button.config(state=search_state); self.download_video_button.config(state=download_state); self.download_audio_button.config(state=download_state)
    def clear_video_info_widgets(self):
        self.title_label.config(text="Título: (Aguardando URL...)"); self.uploader_label.config(text="Canal: "); self.details_label.config(text="Detalhes: ")
        self.thumbnail_label.config(image=None); self.thumbnail_label.image = None; self.video_info = None
        self.video_format_combo['values'] = []; self.audio_format_combo['values'] = []
        self.video_format_combo.set(''); self.audio_format_combo.set('')
        self._set_ui_state('normal', 'disabled')
    def _create_history_tab(self):
        history_frame = ttk.Frame(self.notebook); self.notebook.add(history_frame, text='Histórico')
        history_actions_frame = ttk.Frame(history_frame); history_actions_frame.pack(fill="x", padx=10, pady=5)
        refresh_button = ttk.Button(history_actions_frame, text="Atualizar", command=self.load_history); refresh_button.pack(side="left")
        clear_button = ttk.Button(history_actions_frame, text="Limpar Histórico", command=self.clear_history); clear_button.pack(side="right")
        columns = ("title", "url", "date", "size", "status"); self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        self.history_tree.heading("title", text="Título"); self.history_tree.heading("url", text="URL"); self.history_tree.heading("date", text="Data"); self.history_tree.heading("size", text="Tamanho"); self.history_tree.heading("status", text="Status")
        self.history_tree.column("title", width=300); self.history_tree.column("url", width=150); self.history_tree.column("date", width=120, anchor="center"); self.history_tree.column("size", width=80, anchor="e"); self.history_tree.column("status", width=80, anchor="center")
        self.history_tree.pack(fill="both", expand=True, padx=10, pady=10)
        tree_scrollbar_y = ttk.Scrollbar(self.history_tree, orient="vertical", command=self.history_tree.yview); self.history_tree.configure(yscrollcommand=tree_scrollbar_y.set); tree_scrollbar_y.pack(side="right", fill="y")
        tree_scrollbar_x = ttk.Scrollbar(self.history_tree, orient="horizontal", command=self.history_tree.xview); self.history_tree.configure(xscrollcommand=tree_scrollbar_x.set); tree_scrollbar_x.pack(side="bottom", fill="x")
    def format_bytes(self, size_bytes):
        if not size_bytes or size_bytes == 0: return "N/A"
        power = 1024; n = 0; power_labels = {0: '', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
        while size_bytes >= power and n < len(power_labels): size_bytes /= power; n += 1
        return f"{size_bytes:.2f} {power_labels[n]}"
    def log(self, message, level="info"):
        self.log_text.config(state="normal"); tag = f"log_{level}"; self.log_text.tag_configure(tag, foreground={"info": "blue", "warning": "orange", "error": "red", "critical": "darkred"}.get(level, "black")); self.log_text.insert(tk.END, f"[{level.upper()}] {message}\n", tag); self.log_text.config(state="disabled"); self.log_text.see(tk.END)
    def _load_thumbnail(self, url):
        try:
            response = requests.get(url, timeout=10); response.raise_for_status(); img_data = response.content
            img = Image.open(io.BytesIO(img_data)); img.thumbnail((128, 72)); photo = ImageTk.PhotoImage(img)
            self.root.after(0, lambda: self._update_thumbnail_label(photo))
        except Exception as e: self.log(f"Não foi possível carregar a thumbnail: {e}", "warning")
    def _update_thumbnail_label(self, photo): self.thumbnail_label.config(image=photo); self.thumbnail_label.image = photo
    def load_history(self):
        for i in self.history_tree.get_children(): self.history_tree.delete(i)
        entries = self.history_manager.get_all_entries()
        for entry in entries:
            title, url, date_str, size_bytes, status = entry; date_obj = datetime.datetime.fromisoformat(date_str); display_date = date_obj.strftime("%d/%m/%Y %H:%M"); display_size = self.format_bytes(size_bytes)
            self.history_tree.insert("", tk.END, values=(title, url, display_date, display_size, status))
    def run_video_download(self, url, format_code, download_playlist):
        try:
            self.downloader.download(url, format_code, download_playlist=download_playlist)
            self.log("Download de vídeo concluído e salvo no histórico.", "info")
            self.root.after(0, self.load_history)
        except (InvalidURLError, NetworkError, FileSystemError, DownloaderError, FormatSelectionError) as e:
            self.log(f"Falha no Download: {e}", "error"); messagebox.showerror("Falha no Download", f"Não foi possível completar o download.\nDetalhes: {e}")
        finally: self._set_ui_state('normal', 'normal')
    def run_audio_download(self, url, audio_format, download_playlist):
        try:
            self.downloader.download_audio(url, audio_format, download_playlist=download_playlist)
            self.log("Download de áudio concluído e salvo no histórico.", "info")
            self.root.after(0, self.load_history)
        except (InvalidURLError, NetworkError, FileSystemError, DownloaderError, FormatSelectionError) as e:
            self.log(f"Falha no Download de Áudio: {e}", "error"); messagebox.showerror("Falha no Download", f"Não foi possível completar o download.\nDetalhes: {e}")
        finally: self._set_ui_state('normal', 'normal')
    def clear_history(self):
        if messagebox.askyesno("Confirmar", "Você tem certeza que deseja apagar todo o histórico de downloads? Esta ação não pode ser desfeita."): self.history_manager.clear_history(); self.load_history(); self.log("Histórico de downloads foi limpo.", "warning")
    def on_tab_change(self, event):
        if self.notebook.index(self.notebook.select()) == 1: self.load_history()

