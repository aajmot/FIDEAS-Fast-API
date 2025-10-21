import customtkinter as ctk
from core.shared.utils.logger import logger

class BaseScreen(ctk.CTkFrame):
    def __init__(self, parent, module, title):
        super().__init__(parent)
        self.module = module
        self.title = title
        self.pack(fill="both", expand=True)
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        logger.info(f"Initialized screen: {self.__class__.__name__}", "BaseScreen")
    
    def show_message(self, message, message_type="info"):
        # Create message popup
        popup = ctk.CTkToplevel(self)
        popup.title("Message")
        popup.geometry("300x100")
        popup.transient(self)
        popup.grab_set()
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (300 // 2)
        y = (popup.winfo_screenheight() // 2) - (100 // 2)
        popup.geometry(f"300x100+{x}+{y}")
        
        # Message label
        msg_label = ctk.CTkLabel(popup, text=message, wraplength=250)
        msg_label.pack(pady=20)
        
        # OK button
        ok_button = ctk.CTkButton(popup, text="OK", command=popup.destroy)
        ok_button.pack(pady=10)
        
        logger.info(f"Message displayed: {message}", "BaseScreen")