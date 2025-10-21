import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.inventory_module.services.inventory_service import InventoryService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class InventoryScreen(BaseScreen):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.inventory_service = InventoryService()
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Inventory Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.go_back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Stock adjustment form
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(form_frame, text="Product ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.product_id_input = ctk.CTkEntry(form_frame, width=150)
        self.product_id_input.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Quantity Change:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.quantity_input = ctk.CTkEntry(form_frame, width=150)
        self.quantity_input.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkButton(form_frame, text="Update Stock", command=self.update_stock).grid(row=0, column=4, padx=5, pady=5)
        ctk.CTkButton(form_frame, text="Refresh", command=self.load_inventory).grid(row=0, column=5, padx=5, pady=5)
        
        # Inventory list
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(list_frame, text="Current Inventory:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        self.inventory_listbox = tk.Listbox(list_frame, height=15)
        self.inventory_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_inventory()
    
    @ExceptionMiddleware.handle_exceptions("InventoryScreen")
    def load_inventory(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Inventory, Product
        
        self.inventory_listbox.delete(0, tk.END)
        
        with db_manager.get_session() as session:
            inventory_items = session.query(Inventory).join(Product).all()
            for item in inventory_items:
                display_text = f"ID:{item.product_id} - {item.product.name} - Stock: {float(item.quantity)}"
                self.inventory_listbox.insert(tk.END, display_text)
    
    @ExceptionMiddleware.handle_exceptions("InventoryScreen")
    def update_stock(self):
        if not all([self.product_id_input.get(), self.quantity_input.get()]):
            self.show_message("Please enter product ID and quantity", "error")
            return
        
        try:
            product_id = int(self.product_id_input.get())
            quantity_change = float(self.quantity_input.get())
            
            self.inventory_service.update_stock(product_id, quantity_change)
            self.show_message("Stock updated successfully")
            
            self.product_id_input.delete(0, tk.END)
            self.quantity_input.delete(0, tk.END)
            self.load_inventory()
        except Exception as e:
            self.show_message(f"Error updating stock: {str(e)}", "error")
    
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