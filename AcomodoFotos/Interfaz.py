import customtkinter as ctk
from tkinter import filedialog, messagebox
import Español as organizador
import webbrowser
import os

class OrganizadorApp:
    def __init__(self, root):
        self.root = root
        self.tituloVentana = "Photo and Video Organizer"
        self.labelApi = "Enter your Opencage API Key"
        self.baseFolder = "Photos folder:"
        self.outputFolder = "Destination folder:"
        self.startButton = "Start organization"
        self.botonSeleccionar = "Select"
        self.NodataTittle = "Error"
        self.NodataText = "All fields are required."
        self.finalTittle = "Success"
        self.finalText = "Organization completed"
        self.errorMessageTittle = "Error"
        self.errorMessageText = "An error occurred"
        self.helpText = "Documentation"
        self.labelApi2 = "Get API Key"
        self.root.title(self.tituloVentana)
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=10)
        self.help_button = ctk.CTkButton(
            self.header_frame,
            text=self.helpText,
            fg_color="transparent",
            text_color="black",
            hover=False,
            command=self.documentacionButton
        )
        self.help_button.pack(side="left")
        self.language_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.language_frame.pack(side="right")
        self.language_label = ctk.CTkLabel(
            self.language_frame,
            text="Select your language"
        )
        self.language_label.pack(side="left", padx=(0,5))
        self.language_combobox = ctk.CTkComboBox(
            self.language_frame,
            values=["English", "Español"],
            command=self.select_languaje
        )
        self.language_combobox.set("English")
        self.language_combobox.pack(side="left")

        self.main_frame = ctk.CTkFrame(root, corner_radius=10)
        self.main_frame.pack(padx=20, pady=[0, 50], fill="both", expand=True)
        self.api_key_label = ctk.CTkLabel(self.main_frame, text=self.labelApi, font=("aptos", 15, "bold"))
        self.api_key_label.pack(anchor="center")
        self.api_key_label2 = ctk.CTkButton(
            self.main_frame,
            text=self.labelApi2,
            text_color="blue",
            font=("arial", 12),
            cursor="hand2",
            command=self.hipervinculo,
            fg_color="transparent",
            hover=False
        )
        self.api_key_label2.pack()
        self.api_key_entry = ctk.CTkEntry(self.main_frame, width=500)
        self.api_key_entry.pack(anchor="center")

        self.base_folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.base_folder_frame.pack(pady=10)
        self.base_folder_label = ctk.CTkLabel(self.base_folder_frame, text=self.baseFolder, font=("aptos", 15, "bold"))
        self.base_folder_label.pack()
        self.base_folder_entry = ctk.CTkEntry(self.base_folder_frame, width=350)
        self.base_folder_entry.pack(side="left", anchor="center")
        self.base_folder_button = ctk.CTkButton(self.base_folder_frame, text=self.botonSeleccionar, command=self.select_base_folder)
        self.base_folder_button.pack(side="left", padx=5, anchor="center")

        self.output_folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.output_folder_frame.pack()
        self.output_folder_label = ctk.CTkLabel(self.output_folder_frame, text=self.outputFolder, font=("aptos", 15, "bold"))
        self.output_folder_label.pack()
        self.output_folder_entry = ctk.CTkEntry(self.output_folder_frame, width=350)
        self.output_folder_entry.pack(side="left", anchor="center")
        self.output_folder_button = ctk.CTkButton(self.output_folder_frame, text=self.botonSeleccionar, command=self.select_output_folder)
        self.output_folder_button.pack(side="left", anchor="center", padx=5)

        self.start_button = ctk.CTkButton(
            self.main_frame,
            text=self.startButton,
            command=self.start_organizing,
            width=100,
            height=50,
            fg_color="#63cffb",
            text_color="black",
            font=("aptos", 15, "bold")
        )
        self.start_button.pack(pady=20)

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

    def start_organizing(self):
        api_key = self.api_key_entry.get()
        base_folder = self.base_folder_entry.get()
        output_folder = self.output_folder_entry.get()
        if not api_key or not base_folder or not output_folder:
            messagebox.showerror(self.NodataTittle, self.NodataText)
            return
        organizador.OPENCAGE_API_KEY = api_key
        organizador.BASE_FOLDER = base_folder
        organizador.OUTPUT_FOLDER = output_folder
        try:
            organizador.main(api_key, base_folder, output_folder)
            messagebox.showinfo(self.finalTittle, self.finalText)
        except Exception as e:
            messagebox.showerror(self.errorMessageTittle, f"{self.errorMessageText} {e}")

    def hipervinculo(self):
        link = "https://opencagedata.com/dashboard"
        webbrowser.open(link)

    def select_languaje(self, selected_language):
        if selected_language == "Español":
            self.tituloVentana = "Organizador de Fotos y Videos"
            self.labelApi2 = "Inserta tu API Key de Opencage"
            self.baseFolder = "Carpeta de fotos:"
            self.outputFolder = "Carpeta de destino:"
            self.startButton = "Iniciar organización"
            self.botonSeleccionar = "Seleccionar"
            self.NodataTittle = "Error"
            self.NodataText = "Todos los campos son obligatorios."
            self.finalTittle = "Éxito"
            self.finalText = "Organización completada"
            self.errorMessageTittle = "Error"
            self.errorMessageText = "Ha ocurrido un error"
            self.helpText = "Documentacion"
        else:
            self.tituloVentana = "Photo and Video Organizer"
            self.labelApi2 = "Enter your Opencage API Key"
            self.baseFolder = "Photos folder:"
            self.outputFolder = "Destination folder:"
            self.startButton = "Start organization"
            self.botonSeleccionar = "Select"
            self.NodataTittle = "Error"
            self.NodataText = "All fields are required."
            self.finalTittle = "Success"
            self.finalText = "Organization completed"
            self.errorMessageTittle = "Error"
            self.errorMessageText = "An error occurred"
            self.helpText = "Documentation"

        self.root.title(self.tituloVentana)
        self.api_key_label.configure(text=self.labelApi2)
        self.base_folder_label.configure(text=self.baseFolder)
        self.base_folder_button.configure(text=self.botonSeleccionar)
        self.output_folder_label.configure(text=self.outputFolder)
        self.output_folder_button.configure(text=self.botonSeleccionar)
        self.start_button.configure(text=self.startButton)
        self.help_button.configure(text=self.helpText)

    def documentacionButton(self):
        link2 = "https://github.com/Diegoflores1591/Organizador_De_Google_Fotos"
        webbrowser.open(link2)

if __name__ == "__main__":
    root = ctk.CTk()
    app = OrganizadorApp(root)
    root.mainloop()
