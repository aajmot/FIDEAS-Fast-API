import customtkinter as ctk
import tkinter.messagebox as messagebox
from core.shared.utils.logger import logger

class BaseScreen(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.setup_ui()
        logger.info(f"Initialized screen: {self.__class__.__name__}", "BaseScreen")
    
    def setup_ui(self):
        self.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Configure grid for responsiveness
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def show_message(self, message: str, message_type: str = "info"):
        if message_type == "error":
            messagebox.showerror("Error", message)
        elif message_type == "warning":
            messagebox.showwarning("Warning", message)
        else:
            messagebox.showinfo("Information", message)
        logger.info(f"Message displayed: {message}", "BaseScreen")
    
    def create_button(self, text: str, callback=None):
        btn = ctk.CTkButton(
            self,
            text=text,
            height=40,
            command=callback
        )
        return btn
    
    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()
    
    def back_to_dashboard(self):
        # Clear current screen and show dashboard welcome
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Show welcome message
        welcome_label = ctk.CTkLabel(
            self.parent,
            text="Welcome to FIDEAS Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        welcome_label.pack(pady=(20, 10))
        
        info_label = ctk.CTkLabel(
            self.parent,
            text="Reports and analytics will be displayed here",
            font=ctk.CTkFont(size=14)
        )
        info_label.pack(pady=5)