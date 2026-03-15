import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import yt_dlp


class SpotifyStyleDownloaderApp:
    """
    App de escritorio en Tkinter para descargar audio en MP3.

    Características:
    - Interfaz oscura estilo Spotify
    - Barra de progreso real usando progress_hooks de yt-dlp
    - Descarga de portada (thumbnail)
    - Añade metadata cuando es posible
    - Convierte a MP3 con FFmpeg
    - Selector de carpeta
    - Logs en pantalla
    - Créditos fijos abajo

    IMPORTANTE:
    - Requiere Python
    - Requiere yt-dlp
    - Requiere FFmpeg instalado y accesible desde PATH
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Audio Downloader")
        self.root.geometry("980x720")
        self.root.minsize(920, 680)
        self.root.configure(bg="#121212")

        # -----------------------------
        # Variables de estado de la app
        # -----------------------------
        self.url_var = tk.StringVar()
        self.download_path = tk.StringVar(value=os.path.join(os.getcwd(), "descargas"))
        self.status_var = tk.StringVar(value="Listo para descargar")
        self.progress_label_var = tk.StringVar(value="0%")
        self.current_title_var = tk.StringVar(value="Sin descarga en curso")

        # Flags opcionales
        self.embed_thumbnail_var = tk.BooleanVar(value=True)
        self.add_metadata_var = tk.BooleanVar(value=True)
        self.download_thumbnail_var = tk.BooleanVar(value=True)

        # Si no existe la carpeta por defecto, se crea
        os.makedirs(self.download_path.get(), exist_ok=True)

        # Variable de control para evitar múltiples descargas simultáneas
        self.is_downloading = False

        # -----------------------------
        # Paleta estilo oscuro Spotify
        # -----------------------------
        self.colors = {
            "bg": "#121212",
            "panel": "#181818",
            "card": "#1e1e1e",
            "card_2": "#242424",
            "text": "#ffffff",
            "muted": "#b3b3b3",
            "border": "#2a2a2a",
            "green": "#1DB954",      # verde Spotify
            "green_hover": "#1ed760",
            "danger": "#ff4d4f",
            "warning": "#f5a623",
            "input_bg": "#2a2a2a",
            "log_bg": "#101010",
        }

        # Configuración visual para ttk.Progressbar
        self.setup_ttk_style()

        # Construcción de la interfaz
        self.build_ui()

    def setup_ttk_style(self) -> None:
        """
        Configura el estilo de ttk.Progressbar para que se vea mejor
        sobre fondo oscuro.
        """
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Spotify.Horizontal.TProgressbar",
            troughcolor="#2a2a2a",
            background=self.colors["green"],
            bordercolor="#2a2a2a",
            lightcolor=self.colors["green"],
            darkcolor=self.colors["green"],
            thickness=14,
        )

    def build_ui(self) -> None:
        """
        Crea toda la interfaz principal.
        """
        # Contenedor principal
        main = tk.Frame(self.root, bg=self.colors["bg"])
        main.pack(fill="both", expand=True, padx=24, pady=(24, 10))

        # Header
        self.build_header(main)

        # Cuerpo
        body = tk.Frame(main, bg=self.colors["bg"])
        body.pack(fill="both", expand=True, pady=(16, 0))

        # Columna izquierda: formulario y acciones
        left = tk.Frame(
            body,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Columna derecha: info y ajustes
        right = tk.Frame(
            body,
            bg=self.colors["card"],
            width=280,
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self.build_left_panel(left)
        self.build_right_panel(right)

        # Footer fijo abajo del todo
        self.build_footer()

    def build_header(self, parent: tk.Widget) -> None:
        """
        Cabecera superior de la aplicación.
        """
        header = tk.Frame(parent, bg=self.colors["bg"])
        header.pack(fill="x")

        logo = tk.Canvas(
            header,
            width=48,
            height=48,
            bg=self.colors["bg"],
            highlightthickness=0
        )
        logo.pack(side="left", padx=(0, 14))
        logo.create_oval(4, 4, 44, 44, fill=self.colors["green"], outline=self.colors["green"])
        logo.create_text(24, 24, text="♪", fill="black", font=("Segoe UI", 18, "bold"))

        title_wrap = tk.Frame(header, bg=self.colors["bg"])
        title_wrap.pack(side="left")

        tk.Label(
            title_wrap,
            text="Audio Downloader",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 24, "bold"),
        ).pack(anchor="w")

        tk.Label(
            title_wrap,
            text="Descarga local en MP3 con progreso real, portada y metadata",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 0))

    def build_left_panel(self, parent: tk.Widget) -> None:
        """
        Panel izquierdo: URL, carpeta, botones, progreso y logs.
        """
        wrap = tk.Frame(parent, bg=self.colors["card"])
        wrap.pack(fill="both", expand=True, padx=22, pady=22)

        tk.Label(
            wrap,
            text="Nuevo enlace",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        tk.Label(
            wrap,
            text="Pega un enlace de vídeo o playlist.",
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 18))

        # Campo URL
        tk.Label(
            wrap,
            text="Enlace",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        self.url_entry = tk.Entry(
            wrap,
            textvariable=self.url_var,
            font=("Segoe UI", 11),
            relief="flat",
            bd=0,
            bg=self.colors["input_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
        )
        self.url_entry.pack(fill="x", ipady=11)
        self.url_entry.configure(
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["green"],
        )

        # Carpeta
        tk.Label(
            wrap,
            text="Carpeta de destino",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(18, 6))

        folder_row = tk.Frame(wrap, bg=self.colors["card"])
        folder_row.pack(fill="x")

        self.folder_entry = tk.Entry(
            folder_row,
            textvariable=self.download_path,
            font=("Segoe UI", 11),
            relief="flat",
            bd=0,
            bg=self.colors["input_bg"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=11)
        self.folder_entry.configure(
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["green"],
        )

        self.folder_button = tk.Button(
            folder_row,
            text="Elegir",
            command=self.select_folder,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["green"],
            fg="black",
            activebackground=self.colors["green_hover"],
            activeforeground="black",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=18,
            pady=10,
        )
        self.folder_button.pack(side="left", padx=(10, 0))

        # Botones principales
        buttons_row = tk.Frame(wrap, bg=self.colors["card"])
        buttons_row.pack(fill="x", pady=(22, 18))

        self.download_button = tk.Button(
            buttons_row,
            text="Descargar MP3",
            command=self.start_download,
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["green"],
            fg="black",
            activebackground=self.colors["green_hover"],
            activeforeground="black",
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=22,
            pady=12,
        )
        self.download_button.pack(side="left")

        self.clear_button = tk.Button(
            buttons_row,
            text="Limpiar",
            command=self.clear_fields,
            font=("Segoe UI", 11, "bold"),
            bg=self.colors["card_2"],
            fg=self.colors["text"],
            activebackground="#303030",
            activeforeground=self.colors["text"],
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=22,
            pady=12,
        )
        self.clear_button.pack(side="left", padx=(10, 0))

        # Título actual
        tk.Label(
            wrap,
            text="Elemento actual",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        current_title = tk.Label(
            wrap,
            textvariable=self.current_title_var,
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
            wraplength=560,
            justify="left",
        )
        current_title.pack(anchor="w", pady=(6, 16))

        # Progreso
        progress_top = tk.Frame(wrap, bg=self.colors["card"])
        progress_top.pack(fill="x")

        tk.Label(
            progress_top,
            text="Progreso",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")

        tk.Label(
            progress_top,
            textvariable=self.progress_label_var,
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
        ).pack(side="right")

        self.progress = ttk.Progressbar(
            wrap,
            style="Spotify.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100,
            value=0,
        )
        self.progress.pack(fill="x", pady=(8, 8))

        self.status_label = tk.Label(
            wrap,
            textvariable=self.status_var,
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
        )
        self.status_label.pack(anchor="w", pady=(0, 18))

        # Logs
        tk.Label(
            wrap,
            text="Actividad",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        log_frame = tk.Frame(
            wrap,
            bg=self.colors["log_bg"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
        )
        log_frame.pack(fill="both", expand=True, pady=(8, 0))

        self.log_box = tk.Text(
            log_frame,
            bg=self.colors["log_bg"],
            fg="#d1d5db",
            font=("Consolas", 10),
            relief="flat",
            bd=0,
            insertbackground="#d1d5db",
            wrap="word",
            state="disabled",
        )
        self.log_box.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(log_frame, command=self.log_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=scrollbar.set)

    def build_right_panel(self, parent: tk.Widget) -> None:
        """
        Panel derecho: información y opciones extra.
        """
        wrap = tk.Frame(parent, bg=self.colors["card"])
        wrap.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(
            wrap,
            text="Opciones",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")

        tk.Label(
            wrap,
            text="Ajustes del procesamiento de audio.",
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 16))

        self.create_checkbox(
            wrap,
            "Descargar portada",
            self.download_thumbnail_var
        )

        self.create_checkbox(
            wrap,
            "Añadir metadata",
            self.add_metadata_var
        )

        self.create_checkbox(
            wrap,
            "Insertar portada en el MP3",
            self.embed_thumbnail_var
        )

        sep = tk.Frame(wrap, bg=self.colors["border"], height=1)
        sep.pack(fill="x", pady=18)

        tk.Label(
            wrap,
            text="Notas",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        notes = (
            "• Necesitas FFmpeg en el PATH.\n\n"
            "• La portada y metadata dependen del contenido disponible.\n\n"
            "• Para playlists, el proceso puede tardar bastante.\n\n"
            "• Esta app está pensada para uso local."
        )

        tk.Label(
            wrap,
            text=notes,
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
            justify="left",
            wraplength=220,
        ).pack(anchor="w", pady=(10, 0))

    def create_checkbox(self, parent: tk.Widget, text: str, variable: tk.BooleanVar) -> None:
        """
        Crea un checkbox con estilo oscuro.
        """
        cb = tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            bg=self.colors["card"],
            fg=self.colors["text"],
            activebackground=self.colors["card"],
            activeforeground=self.colors["text"],
            selectcolor=self.colors["card_2"],
            font=("Segoe UI", 10),
            anchor="w",
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        cb.pack(fill="x", anchor="w", pady=5)

    def build_footer(self) -> None:
        """
        Footer fijo abajo del todo.
        """
        footer = tk.Frame(self.root, bg=self.colors["bg"])
        footer.pack(side="bottom", fill="x")

        tk.Label(
            footer,
            text="Este software es para descargar contenido SIEMPRE con una autorización de su creador, no me hago responsable de su uso",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=("Segoe UI", 9),
            wraplength=900,
            justify="center",
        ).pack(pady=(4, 0))

        tk.Label(
            footer,
            text="Creado por Jesús Vicario Valadez",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(pady=(0, 6))

    def select_folder(self) -> None:
        """
        Abre el selector de carpeta.
        """
        folder = filedialog.askdirectory()
        if folder:
            self.download_path.set(folder)

    def clear_fields(self) -> None:
        """
        Limpia la URL y reinicia algunos estados visuales.
        """
        if self.is_downloading:
            messagebox.showinfo("Información", "No puedes limpiar mientras hay una descarga en curso.")
            return

        self.url_var.set("")
        self.current_title_var.set("Sin descarga en curso")
        self.status_var.set("Listo para descargar")
        self.progress_label_var.set("0%")
        self.set_progress(0)
        self.log("Campos limpiados.")

    def log(self, message: str) -> None:
        """
        Escribe una línea en el panel de logs.
        """
        self.log_box.config(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def thread_safe_log(self, message: str) -> None:
        """
        Manda un log al hilo principal de Tkinter.
        """
        self.root.after(0, lambda: self.log(message))

    def set_progress(self, value: float) -> None:
        """
        Actualiza la barra de progreso.
        """
        self.progress["value"] = max(0, min(100, value))

    def thread_safe_set_progress(self, value: float) -> None:
        """
        Actualiza el progreso desde un hilo secundario.
        """
        self.root.after(0, lambda: self.set_progress(value))
        self.root.after(0, lambda: self.progress_label_var.set(f"{int(value)}%"))

    def thread_safe_set_status(self, message: str) -> None:
        """
        Actualiza el texto de estado desde un hilo secundario.
        """
        self.root.after(0, lambda: self.status_var.set(message))

    def thread_safe_set_title(self, title: str) -> None:
        """
        Actualiza el título actual desde un hilo secundario.
        """
        self.root.after(0, lambda: self.current_title_var.set(title))

    def set_controls_state(self, enabled: bool) -> None:
        """
        Activa o desactiva controles para evitar acciones simultáneas.
        """
        state = "normal" if enabled else "disabled"
        self.download_button.config(state=state)
        self.clear_button.config(state=state)
        self.folder_button.config(state=state)
        self.url_entry.config(state=state)
        self.folder_entry.config(state=state)

    def start_download(self) -> None:
        """
        Valida los datos y lanza la descarga en un hilo aparte.
        """
        if self.is_downloading:
            messagebox.showinfo("Información", "Ya hay una descarga en curso.")
            return

        url = self.url_var.get().strip()
        folder = self.download_path.get().strip()

        if not url:
            messagebox.showwarning("Aviso", "Pega un enlace primero.")
            return

        if not folder:
            messagebox.showwarning("Aviso", "Elige una carpeta de descarga.")
            return

        os.makedirs(folder, exist_ok=True)

        self.is_downloading = True
        self.set_controls_state(False)
        self.status_var.set("Preparando descarga...")
        self.progress_label_var.set("0%")
        self.set_progress(0)
        self.log("Preparando descarga...")

        # Lanzamos la descarga en un hilo para no congelar la interfaz
        thread = threading.Thread(target=self.download_audio, args=(url, folder), daemon=True)
        thread.start()

    def progress_hook(self, data: dict) -> None:
        """
        Hook de progreso de yt-dlp.

        yt-dlp envía eventos con estado 'downloading' y 'finished'.
        Aquí calculamos el porcentaje real cuando hay datos disponibles.
        """
        status = data.get("status")

        if status == "downloading":
            filename = data.get("filename")
            if filename:
                title = os.path.basename(filename)
                self.thread_safe_set_title(title)

            downloaded = data.get("downloaded_bytes", 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate")

            if total:
                percent = (downloaded / total) * 100
                self.thread_safe_set_progress(percent)

            speed = data.get("speed")
            eta = data.get("eta")

            parts = ["Descargando audio"]
            if speed:
                parts.append(f"Velocidad: {self.format_bytes(speed)}/s")
            if eta is not None:
                parts.append(f"ETA: {eta}s")

            self.thread_safe_set_status(" | ".join(parts))

        elif status == "finished":
            self.thread_safe_set_progress(100)
            self.thread_safe_set_status("Descarga completada. Procesando MP3...")

    @staticmethod
    def format_bytes(num: float) -> str:
        """
        Convierte bytes a formato legible.
        """
        if not num:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(num)

        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.2f} {unit}"
            size /= 1024

        return f"{size:.2f} TB"

    def build_ydl_options(self, folder: str) -> dict:
        """
        Construye las opciones de yt-dlp según los ajustes marcados.
        """
        postprocessors = [
            {
                # Extrae el audio con FFmpeg
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

        # Añadir metadata si está activado
        if self.add_metadata_var.get():
            postprocessors.append(
                {
                    "key": "FFmpegMetadata"
                }
            )

        # Insertar portada dentro del archivo si está activado
        # Esto requiere que exista thumbnail descargada y soporte del contenedor/proceso
        if self.embed_thumbnail_var.get():
            postprocessors.append(
                {
                    "key": "EmbedThumbnail"
                }
            )

        options = {
            # Mejor audio disponible
            "format": "bestaudio/best",

            # Plantilla de salida
            "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),

            # Permite playlists completas
            "noplaylist": False,

            # Hook de progreso real
            "progress_hooks": [self.progress_hook],

            # Descarga de portada
            "writethumbnail": self.download_thumbnail_var.get(),

            # Intenta escribir metadata adicional
            "addmetadata": self.add_metadata_var.get(),

            # Postprocesadores
            "postprocessors": postprocessors,

            # Menos ruido en consola interna
            "quiet": True,
            "no_warnings": True,
        }

        return options

    def download_audio(self, url: str, folder: str) -> None:
        """
        Descarga y procesa el audio.
        """
        try:
            self.thread_safe_log("Iniciando descarga...")
            self.thread_safe_set_status("Conectando con la fuente...")

            ydl_opts = self.build_ydl_options(folder)

            # Logger simple opcional para capturar mensajes internos
            class YDLLogger:
                def __init__(self, app: "SpotifyStyleDownloaderApp"):
                    self.app = app

                def debug(self, msg):
                    # Evitamos spamear demasiado, pero algunas líneas útiles pueden servir
                    if "[download]" in msg or "[ExtractAudio]" in msg or "[Metadata]" in msg:
                        self.app.thread_safe_log(msg)

                def warning(self, msg):
                    self.app.thread_safe_log(f"Advertencia: {msg}")

                def error(self, msg):
                    self.app.thread_safe_log(f"Error: {msg}")

            ydl_opts["logger"] = YDLLogger(self)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Primero extraemos info para mostrar el título antes de descargar
                info = ydl.extract_info(url, download=False)

                # Si es playlist, el campo cambia; si es un solo vídeo, suele traer title
                if "entries" in info and info.get("title"):
                    title = f"Playlist: {info.get('title')}"
                else:
                    title = info.get("title", "Elemento sin título")

                self.thread_safe_set_title(title)
                self.thread_safe_log(f"Título detectado: {title}")

                # Ahora sí, descarga real
                ydl.download([url])

            self.thread_safe_set_status("Proceso terminado correctamente.")
            self.thread_safe_log("Descarga finalizada correctamente.")
            self.thread_safe_set_progress(100)

        except Exception as e:
            self.thread_safe_set_status("Ha ocurrido un error.")
            self.thread_safe_log(f"Error: {e}")

        finally:
            # Reactivamos la interfaz en el hilo principal
            def restore_ui():
                self.is_downloading = False
                self.set_controls_state(True)

            self.root.after(0, restore_ui)


if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifyStyleDownloaderApp(root)
    root.mainloop()