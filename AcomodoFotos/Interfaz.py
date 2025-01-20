import customtkinter as ctk
from tkinter import filedialog, messagebox
import Español as organizador

class OrganizadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizador de Fotos y Videos")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        self.main_frame = ctk.CTkFrame(root, corner_radius=10)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.set_appearance_mode("System")  
        ctk.set_default_color_theme("blue")  

        self.api_key_label = ctk.CTkLabel(self.main_frame, text="OpenCage API Key:")
        self.api_key_label.pack()
    
        self.api_key_entry = ctk.CTkEntry(self.main_frame, width=400)
        self.api_key_entry.pack()
    
        self.base_folder_label = ctk.CTkLabel(self.main_frame, text="Carpeta de Google Takeout:")
        self.base_folder_label.pack()
    
        self.base_folder_entry = ctk.CTkEntry(self.main_frame, width=400, corner_radius= 10)
        self.base_folder_entry.pack()
      
        self.base_folder_button = ctk.CTkButton(self.main_frame, text="Seleccionar", command=self.select_base_folder)
        self.base_folder_button.pack()

        self.output_folder_label = ctk.CTkLabel(self.main_frame, text="Carpeta de Destino:")
        self.output_folder_label.pack()
       
        self.output_folder_entry = ctk.CTkEntry(self.main_frame, width=400)
        self.output_folder_entry.pack()
      
        self.output_folder_button = ctk.CTkButton(self.main_frame, text="Seleccionar", command=self.select_output_folder)
        self.output_folder_button.pack()
    
        self.start_button = ctk.CTkButton(self.main_frame, text="Iniciar Organización", command=self.start_organizing)
        self.start_button.pack()
      
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
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return

        organizador.OPENCAGE_API_KEY = api_key
        organizador.BASE_FOLDER = base_folder
        organizador.OUTPUT_FOLDER = output_folder

        try:
            organizador.main(api_key, base_folder, output_folder)  # Llamar a main con los argumentos
            messagebox.showinfo("Éxito", "Organización completada.")
        except Exception as e:
            messagebox.showerror("Error", f"Ha ocurrido un error: {e}")

if __name__ == "__main__":
    root = ctk.CTk()
    app = OrganizadorApp(root)
    root.mainloop()