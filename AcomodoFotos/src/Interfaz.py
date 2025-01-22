import customtkinter as ctk
from tkinter import filedialog, messagebox
import webbrowser
import os
import logging
import organizador

# Diccionario que agrupa todos los textos de la interfaz por idioma
LANG_DICT = {
    "English": {
        "title": "Photo Organizer",
        "api_label": "Enter your Opencage API Key",
        "api_button_label": "Get API Key",
        "photos_label": "Photos folder:",
        "destination_label": "Destination folder:",
        "select_button": "Select",
        "start_button": "Start organization",
        "help_button": "Documentation",
        "error_no_data_title": "Error",
        "error_no_data_text": "All fields are required.",
        "error_title": "Error",
        "error_text": "An error occurred",
        "success_title": "Success",
        "success_text": "Organization completed",
    },
    "Español": {
        "title": "Organizador de Fotos",
        "api_label": "Inserta tu API Key de Opencage",
        "api_button_label": "Obtener API Key",
        "photos_label": "Carpeta de fotos:",
        "destination_label": "Carpeta de destino:",
        "select_button": "Seleccionar",
        "start_button": "Iniciar organización",
        "help_button": "Documentacion",
        "error_no_data_title": "Error",
        "error_no_data_text": "Todos los campos son obligatorios.",
        "error_title": "Error",
        "error_text": "Ha ocurrido un error",
        "success_title": "Éxito",
        "success_text": "Organización completada",
    }
}


class LabelLogHandler(logging.Handler):
    """
    Handler personalizado que muestra SOLO el último mensaje
    en un label (status_label). Cada log nuevo sobreescribe el anterior.
    """
    def __init__(self, label):
        super().__init__()
        self.label = label

    def emit(self, record):
        msg = self.format(record)
        # Actualizamos el label con el último mensaje
        self.label.configure(text=msg)
        self.label.update_idletasks()


class OrganizadorApp:
    """
    Clase principal que crea la interfaz gráfica con CustomTkinter
    y gestiona la lógica para organizar fotos y videos.
    """
    def __init__(self, root):
        self.root = root

        # Ajustes de ventana
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Idioma por defecto
        self.selected_language = "English"
        self.lang_texts = LANG_DICT[self.selected_language]
        self.root.title(self.lang_texts["title"])

        # Creamos la interfaz
        self.create_header()
        self.create_main_frame()

        # Agregamos el handler de logging que actualizará el label
        self.attach_logger_to_label()

    def create_header(self):
        self.header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=10)

        self.help_button = ctk.CTkButton(
            self.header_frame,
            text=self.lang_texts["help_button"],
            fg_color="transparent",
            text_color="blue",
            hover=False,
            command=self.open_documentation,
            cursor="hand2"
        )
        self.help_button.pack(side="left")

        self.language_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.language_frame.pack(side="right")

        self.language_label = ctk.CTkLabel(self.language_frame, text="Select your language")
        self.language_label.pack(side="left", padx=(0, 5))

        self.language_combobox = ctk.CTkComboBox(
            self.language_frame,
            values=["English", "Español"],
            command=self.select_language
        )
        self.language_combobox.set("English")
        self.language_combobox.pack(side="left")

    def create_main_frame(self):
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=10)
        self.main_frame.pack(padx=20, pady=[0, 50], fill="both", expand=True)

        # Etiqueta de API Key
        self.api_key_label = ctk.CTkLabel(
            self.main_frame,
            text=self.lang_texts["api_label"],
            font=("aptos", 15, "bold")
        )
        self.api_key_label.pack(anchor="center")

        # Botón para abrir enlace de API Key
        self.api_key_button = ctk.CTkButton(
            self.main_frame,
            text=self.lang_texts["api_button_label"],
            text_color="blue",
            font=("arial", 12),
            cursor="hand2",
            command=self.open_api_link,
            fg_color="transparent",
            hover=False
        )
        self.api_key_button.pack()

        # Entrada de texto para la API Key
        self.api_key_entry = ctk.CTkEntry(self.main_frame, width=500)
        self.api_key_entry.pack(anchor="center")

        # Sección carpeta base (fotos)
        self.base_folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.base_folder_frame.pack(pady=10)

        self.base_folder_label = ctk.CTkLabel(
            self.base_folder_frame,
            text=self.lang_texts["photos_label"],
            font=("aptos", 15, "bold")
        )
        self.base_folder_label.pack()

        self.base_folder_entry = ctk.CTkEntry(self.base_folder_frame, width=350)
        self.base_folder_entry.pack(side="left", anchor="center")

        self.base_folder_button = ctk.CTkButton(
            self.base_folder_frame,
            text=self.lang_texts["select_button"],
            command=self.select_base_folder
        )
        self.base_folder_button.pack(side="left", padx=5, anchor="center")

        # Sección carpeta destino
        self.output_folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.output_folder_frame.pack()

        self.output_folder_label = ctk.CTkLabel(
            self.output_folder_frame,
            text=self.lang_texts["destination_label"],
            font=("aptos", 15, "bold")
        )
        self.output_folder_label.pack()

        self.output_folder_entry = ctk.CTkEntry(self.output_folder_frame, width=350)
        self.output_folder_entry.pack(side="left", anchor="center")

        self.output_folder_button = ctk.CTkButton(
            self.output_folder_frame,
            text=self.lang_texts["select_button"],
            command=self.select_output_folder
        )
        self.output_folder_button.pack(side="left", anchor="center", padx=5)

        # Botón iniciar organización
        self.start_button = ctk.CTkButton(
            self.main_frame,
            text=self.lang_texts["start_button"],
            command=self.start_organizing,
            width=100,
            height=50,
            fg_color="#63cffb",
            text_color="black",
            font=("aptos", 15, "bold")
        )
        self.start_button.pack(pady=20)

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            orientation="horizontal",
            mode="determinate"
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        # Label para mostrar el ÚLTIMO mensaje de logging
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            fg_color="transparent",
            wraplength=500
        )
        self.status_label.pack(pady=(5, 0))

    def attach_logger_to_label(self):
        """
        Crea un handler que captura los logs y muestra el último mensaje en self.status_label
        en el nivel DEBUG (para ver todos).
        """
        label_handler = LabelLogHandler(self.status_label)
        label_handler.setLevel(logging.DEBUG)  # Mostrar todos los niveles en el label

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%d-%m-%Y %H:%M:%S')
        label_handler.setFormatter(formatter)

        logger = logging.getLogger()          # Root logger
        logger.setLevel(logging.DEBUG)        # Nivel DEBUG global
        logger.addHandler(label_handler)

    def start_organizing(self):
        api_key = self.api_key_entry.get()
        base_folder = self.base_folder_entry.get()
        output_folder = self.output_folder_entry.get()

        if not api_key or not base_folder or not output_folder:
            messagebox.showerror(
                self.lang_texts["error_no_data_title"],
                self.lang_texts["error_no_data_text"]
            )
            return

        # Actualizamos variables globales (opcional)
        organizador.OPENCAGE_API_KEY = api_key
        organizador.BASE_FOLDER = base_folder
        organizador.OUTPUT_FOLDER = output_folder

        self.total_files = self.count_files(base_folder)
        self.processed_files = 0

        if self.total_files == 0:
            messagebox.showinfo("Info", "No hay archivos de foto o video en la carpeta origen.")
            return

        self.progress_bar.set(0)

        try:
            organizador.main(
                api_key,
                base_folder,
                output_folder,
                progress_callback=self.file_processed_callback
            )
            messagebox.showinfo(
                self.lang_texts["success_title"],
                self.lang_texts["success_text"]
            )
        except Exception as e:
            messagebox.showerror(
                self.lang_texts["error_title"],
                f'{self.lang_texts["error_text"]} {e}'
            )

    def file_processed_callback(self):
        self.processed_files += 1
        fraction = self.processed_files / self.total_files
        self.progress_bar.set(fraction)
        self.root.update_idletasks()

    def count_files(self, folder):
        valid_extensions = ('.jpg', '.jpeg', '.png', '.mp4', '.mov', '.mkv', '.avi')
        total = 0
        for root, _, files in os.walk(folder):
            for f in files:
                if os.path.splitext(f)[1].lower() in valid_extensions:
                    total += 1
        return total

    def select_base_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.base_folder_entry.delete(0, ctk.END)
            self.base_folder_entry.insert(0, folder)

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder_entry.delete(0, ctk.END)
            self.output_folder_entry.insert(0, folder)

    def open_api_link(self):
        webbrowser.open("https://opencagedata.com/dashboard")

    def open_documentation(self):
        webbrowser.open("https://github.com/Diegoflores1591/Organizador_De_Google_Fotos")

    def select_language(self, selected_language):
        self.selected_language = selected_language
        self.lang_texts = LANG_DICT[self.selected_language]

        self.root.title(self.lang_texts["title"])
        self.api_key_label.configure(text=self.lang_texts["api_label"])
        self.api_key_button.configure(text=self.lang_texts["api_button_label"])
        self.base_folder_label.configure(text=self.lang_texts["photos_label"])
        self.base_folder_button.configure(text=self.lang_texts["select_button"])
        self.output_folder_label.configure(text=self.lang_texts["destination_label"])
        self.output_folder_button.configure(text=self.lang_texts["select_button"])
        self.start_button.configure(text=self.lang_texts["start_button"])
        self.help_button.configure(text=self.lang_texts["help_button"])


if __name__ == "__main__":
    root = ctk.CTk()
    app = OrganizadorApp(root)
    root.mainloop()
