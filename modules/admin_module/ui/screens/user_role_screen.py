import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen

class UserRoleScreen(BaseScreen):
    def __init__(self, parent, admin_module, **kwargs):
        self.admin_module = admin_module
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="User-Role Mapping", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.go_back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Placeholder content
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(content_frame, text="User-Role Mapping - Coming Soon", font=ctk.CTkFont(size=16)).pack(expand=True)
    
    def go_back_to_dashboard(self):
        """Go back to dashboard"""
        self.destroy()
        root = self
        while root.master:
            root = root.master
        for widget in root.winfo_children():
            widget.destroy()
        from modules.dashboard.modern_dashboard import ModernDashboard
        ModernDashboard(root)