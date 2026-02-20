"""
YouTube Video / Ses İndirici — customtkinter + yt-dlp
Maks 1080p MP4 veya WAV ses.  Tüm konsol pencereleri bastırılmıştır.
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path

# ─── Konsol pencerelerini global olarak bastır ────────────────────────────────
# yt-dlp ve ffmpeg'in açtığı tüm alt süreçlerde siyah pencere görünmesini engeller.
if sys.platform == "win32":
    _original_popen_init = subprocess.Popen.__init__

    def _silent_popen_init(self, *args, **kwargs):
        kwargs.setdefault("creationflags", 0)
        kwargs["creationflags"] |= subprocess.CREATE_NO_WINDOW
        _original_popen_init(self, *args, **kwargs)

    subprocess.Popen.__init__ = _silent_popen_init


import customtkinter as ctk
import yt_dlp


# ─── Otomatik güncelleme (arka planda) ────────────────────────────────────────
def _auto_update_ytdlp() -> None:
    """Uygulama açılırken yt-dlp'yi sessizce günceller."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


threading.Thread(target=_auto_update_ytdlp, daemon=True).start()


# ─── İlk açılışta kısayol oluştur (yalnızca Windows) ────────────────────────
def _create_shortcuts() -> None:
    """Masaüstü ve Başlat Menüsü kısayollarını ilk açılışta oluşturur."""
    if sys.platform != "win32":
        return

    APP_DIR = Path(__file__).resolve().parent
    MARKER = APP_DIR / ".shortcuts_created"
    if MARKER.exists():
        return  # Daha önce oluşturulmuş, tekrar yapma

    # pythonw.exe yolu (konsol penceresi açmadan çalıştırır)
    pythonw = Path(sys.executable).parent / "pythonw.exe"
    if not pythonw.exists():
        pythonw = Path(sys.executable)  # fallback

    script = str(APP_DIR / "app.py")
    shortcut_name = "YouTube Indirici.lnk"
    desktop = Path.home() / "Desktop"
    start_menu = Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs"

    ps_template = """
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("{lnk_path}")
$sc.TargetPath = "{target}"
$sc.Arguments = '"{script}"'
$sc.WorkingDirectory = "{workdir}"
$sc.WindowStyle = 7
$sc.Description = "YouTube Video / Ses Indirici"
$sc.Save()
""".strip()

    for folder in (desktop, start_menu):
        try:
            lnk = str(folder / shortcut_name)
            ps = ps_template.format(
                lnk_path=lnk,
                target=str(pythonw),
                script=script,
                workdir=str(APP_DIR),
            )
            subprocess.run(
                ["powershell", "-Command", ps],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    MARKER.touch()  # Bir daha çalışmasın


threading.Thread(target=_create_shortcuts, daemon=True).start()


# ─── Ayarlar ──────────────────────────────────────────────────────────────────
DOWNLOADS_DIR = str(Path.home() / "Downloads")
APP_TITLE = "YouTube İndirici"
WINDOW_SIZE = "520x380"

# Format seçenekleri
FORMAT_VIDEO = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]"
FORMAT_AUDIO = "bestaudio/best"

MODE_VIDEO = "Video (1080p MP4)"
MODE_AUDIO = "Sadece Ses (WAV)"


# ─── Uygulama ────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._build_ui()

    # ── Arayüz ────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # Ana çerçeve
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Başlık
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="🎬  YouTube İndirici",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.title_label.pack(pady=(20, 5))

        # Alt başlık
        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Video veya ses olarak indir",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.subtitle_label.pack(pady=(0, 15))

        # URL girişi
        self.url_entry = ctk.CTkEntry(
            self.main_frame,
            placeholder_text="YouTube bağlantısını buraya yapıştır…",
            width=420,
            height=40,
            font=ctk.CTkFont(size=14),
        )
        self.url_entry.pack(pady=(0, 12))

        # ── Format seçimi ─────────────────────────────────────────────────
        self.format_var = ctk.StringVar(value=MODE_VIDEO)

        format_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        format_frame.pack(pady=(0, 12))

        self.radio_video = ctk.CTkRadioButton(
            format_frame,
            text=MODE_VIDEO,
            variable=self.format_var,
            value=MODE_VIDEO,
            font=ctk.CTkFont(size=13),
            radiobutton_width=20,
            radiobutton_height=20,
        )
        self.radio_video.pack(side="left", padx=(0, 25))

        self.radio_audio = ctk.CTkRadioButton(
            format_frame,
            text=MODE_AUDIO,
            variable=self.format_var,
            value=MODE_AUDIO,
            font=ctk.CTkFont(size=13),
            radiobutton_width=20,
            radiobutton_height=20,
        )
        self.radio_audio.pack(side="left")

        # İndir butonu
        self.download_btn = ctk.CTkButton(
            self.main_frame,
            text="⬇  İndir",
            width=420,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._on_download,
        )
        self.download_btn.pack(pady=(0, 12))

        # İlerleme çubuğu
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=420, height=10)
        self.progress_bar.pack(pady=(0, 5))
        self.progress_bar.set(0)

        # Durum yazısı
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.status_label.pack(pady=(0, 10))

    # ── İndirme tetikleme ─────────────────────────────────────────────────
    def _on_download(self) -> None:
        url = self.url_entry.get().strip()
        if not url:
            self._set_status("⚠️  Lütfen bir URL girin.", "orange")
            return

        # Arayüzü kilitle
        self.download_btn.configure(state="disabled", text="İndiriliyor…")
        self.progress_bar.set(0)
        self._set_status("⏳ Hazırlanıyor…", "gray")

        mode = self.format_var.get()
        thread = threading.Thread(target=self._download, args=(url, mode), daemon=True)
        thread.start()

    # ── yt-dlp ile indirme ────────────────────────────────────────────────
    def _download(self, url: str, mode: str) -> None:
        if mode == MODE_AUDIO:
            opts = {
                "format": FORMAT_AUDIO,
                "outtmpl": os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                }],
                "progress_hooks": [self._progress_hook],
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
            }
        else:
            opts = {
                "format": FORMAT_VIDEO,
                "format_sort": ["fps"],
                "merge_output_format": "mp4",
                "outtmpl": os.path.join(DOWNLOADS_DIR, "%(title)s.%(ext)s"),
                "progress_hooks": [self._progress_hook],
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
            }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            ext = "WAV" if mode == MODE_AUDIO else "MP4"
            self._finish_success(ext)
        except Exception as exc:
            self._finish_error(str(exc))

    # ── İlerleme hook ─────────────────────────────────────────────────────
    def _progress_hook(self, d: dict) -> None:
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = downloaded / total
                self.after(0, self.progress_bar.set, pct)
                self.after(
                    0,
                    self._set_status,
                    f"⬇  İndiriliyor… %{int(pct * 100)}",
                    "#3b82f6",
                )
        elif d["status"] == "finished":
            self.after(0, self.progress_bar.set, 1.0)
            self.after(0, self._set_status, "🔄 İşleniyor…", "gray")

    # ── Sonuç bildirimleri ────────────────────────────────────────────────
    def _finish_success(self, ext: str) -> None:
        self.after(0, self.progress_bar.set, 1.0)
        self.after(0, self._set_status, f"✅ {ext} olarak indirildi!", "#22c55e")
        self.after(0, self._reset_button)

    def _finish_error(self, msg: str) -> None:
        short = (msg[:60] + "…") if len(msg) > 60 else msg
        self.after(0, self.progress_bar.set, 0)
        self.after(0, self._set_status, f"❌ Hata: {short}", "#ef4444")
        self.after(0, self._reset_button)

    # ── Yardımcılar ──────────────────────────────────────────────────────
    def _set_status(self, text: str, color: str = "gray") -> None:
        self.status_label.configure(text=text, text_color=color)

    def _reset_button(self) -> None:
        self.download_btn.configure(state="normal", text="⬇  İndir")


# ─── Giriş noktası ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
