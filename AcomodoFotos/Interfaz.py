import customtkinter as ctk
from tkinter import filedialog, messagebox
import organizador
import webbrowser

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


class OrganizadorApp:
    """
    Clase principal que crea la interfaz gráfica con CustomTkinter
    y gestiona la lógica para organizar fotos y videos.
    """
    def __init__(self, root):
        self.root = root

        # Ajustes de ventana
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        

        # Idioma por defecto
        self.selected_language = "English"
        # Cargamos los textos según idioma
        self.lang_texts = LANG_DICT[self.selected_language]

        # Configuramos título
        self.root.title(self.lang_texts["title"])

        # Creamos la interfaz
        self.create_header()
        self.create_main_frame()

    def create_header(self):
        """
        Crea la barra superior con el botón de ayuda y
        el selector de idioma.
        """
        self.header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=10)

        # Botón de documentación
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

        # Frame para selector de idioma
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
        """
        Crea el marco principal y los elementos de
        entrada y botones necesarios.
        """
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

    # -------------------------
    #  MÉTODOS DE LA APLICACIÓN
    # -------------------------

    def select_base_folder(self):
        """
        Abre un diálogo para seleccionar la carpeta base de fotos.
        """
        folder = filedialog.askdirectory()
        if folder:
            self.base_folder_entry.delete(0, ctk.END)
            self.base_folder_entry.insert(0, folder)

    def select_output_folder(self):
        """
        Abre un diálogo para seleccionar la carpeta de destino.
        """
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder_entry.delete(0, ctk.END)
            self.output_folder_entry.insert(0, folder)

    def start_organizing(self):
        """
        Inicia el proceso de organización llamando a la función principal
        del módulo 'Español' (organizador) con los datos ingresados.
        """
        api_key = self.api_key_entry.get()
        base_folder = self.base_folder_entry.get()
        output_folder = self.output_folder_entry.get()

        if not api_key or not base_folder or not output_folder:
            messagebox.showerror(
                self.lang_texts["error_no_data_title"],
                self.lang_texts["error_no_data_text"]
            )
            return

        organizador.OPENCAGE_API_KEY = api_key
        organizador.BASE_FOLDER = base_folder
        organizador.OUTPUT_FOLDER = output_folder

        try:
            organizador.main(api_key, base_folder, output_folder)
            messagebox.showinfo(
                self.lang_texts["success_title"],
                self.lang_texts["success_text"]
            )
        except Exception as e:
            messagebox.showerror(
                self.lang_texts["error_title"],
                f'{self.lang_texts["error_text"]} {e}'
            )

    def open_api_link(self):
        """
        Abre en el navegador la página de Opencage para obtener la API Key.
        """
        link = "https://opencagedata.com/dashboard"
        webbrowser.open(link)

    def open_documentation(self):
        """
        Abre la documentación (repositorio en GitHub) en el navegador.
        """
        link2 = "https://github.com/Diegoflores1591/Organizador_De_Google_Fotos"
        webbrowser.open(link2)

    def select_language(self, selected_language):
        """
        Actualiza los textos de la interfaz según el idioma seleccionado.
        """
        self.selected_language = selected_language
        self.lang_texts = LANG_DICT[self.selected_language]

        # Actualizamos el título y textos de la UI
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
