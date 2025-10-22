import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from core.shared.components.searchable_dropdown import SearchableDropdown
from modules.inventory_module.services.stock_service import StockService

class StockDetailsScreen(BaseScreen):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.stock_service = StockService()
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Current Stock Details", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Filter frame
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Product Filter:").pack(side="left", padx=10, pady=10)
        self.product_filter = SearchableDropdown(filter_frame, values=[], width=200, placeholder_text="All Products", command=self.filter_stock)
        self.product_filter.pack(side="left", padx=10, pady=10)
        
        ctk.CTkButton(filter_frame, text="Refresh", command=self.load_stock_details, height=30).pack(side="right", padx=10, pady=10)
        
        # Stock details list
        stock_frame = ctk.CTkScrollableFrame(self)
        stock_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Header
        header_frame = ctk.CTkFrame(stock_frame, fg_color="#e0e0e0")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        headers = ["Product", "Batch", "Current Stock", "Available", "Reserved", "Avg Cost", "Total Value", "Last Updated"]
        widths = [150, 100, 100, 100, 100, 100, 120, 120]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=10, weight="bold"), 
                        text_color="#333333", width=width).grid(row=0, column=i, padx=2, pady=5)
        
        self.stock_list_frame = ctk.CTkFrame(stock_frame)
        self.stock_list_frame.pack(fill="x", padx=5, pady=5)
        
        # Summary frame
        summary_frame = ctk.CTkFrame(self, height=60)
        summary_frame.pack(fill="x", padx=10, pady=5)
        summary_frame.pack_propagate(False)
        
        ctk.CTkLabel(summary_frame, text="Stock Summary", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(5, 0))
        
        self.summary_label = ctk.CTkLabel(summary_frame, text="", font=ctk.CTkFont(size=11))
        self.summary_label.pack(pady=5)
        
        self.load_products()
        self.load_stock_details()
    
    def load_products(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Product
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            query = session.query(Product)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Product.tenant_id == tenant_id)
            
            products = query.all()
            product_values = ["All Products"] + [f"{prod.id}:{prod.name}" for prod in products]
            self.product_filter.configure_values(product_values)
    
    def load_stock_details(self):
        # Clear existing stock details
        for widget in self.stock_list_frame.winfo_children():
            widget.destroy()
        
        try:
            product_id = None
            filter_value = self.product_filter.get().strip()
            if filter_value and filter_value != "All Products" and ':' in filter_value:
                product_id = int(filter_value.split(':')[0])
            
            from core.database.connection import db_manager
            from modules.inventory_module.models.stock_entities import StockBalance
            from modules.inventory_module.models.entities import Product
            from core.shared.utils.session_manager import session_manager
            from sqlalchemy.orm import joinedload
            
            with db_manager.get_session() as session:
                query = session.query(StockBalance).options(joinedload(StockBalance.product)).join(Product)
                
                if product_id:
                    query = query.filter(StockBalance.product_id == product_id)
                
                tenant_id = session_manager.get_current_tenant_id()
                if tenant_id:
                    query = query.filter(StockBalance.tenant_id == tenant_id)
                
                balances = query.filter(StockBalance.total_quantity > 0).all()
                
                # Process balances within session context
                balance_data = []
                for balance in balances:
                    # Extract all needed data while in session
                    balance_info = {
                        'product_name': balance.product.name,
                        'batch_number': balance.batch_number or "-",
                        'total_quantity': float(balance.total_quantity or 0),
                        'available_quantity': float(balance.available_quantity or 0),
                        'reserved_quantity': float(balance.reserved_quantity or 0),
                        'average_cost': float(balance.average_cost or 0),
                        'last_updated': balance.last_updated.strftime('%Y-%m-%d') if balance.last_updated else "-",
                        'danger_level': float(getattr(balance.product, 'danger_level', 0) or 0),
                        'reorder_level': float(getattr(balance.product, 'reorder_level', 0) or 0)
                    }
                    balance_data.append(balance_info)
            
            total_products = 0
            total_value = 0
            
            # Now create UI elements outside session
            for balance_info in balance_data:
                row_frame = ctk.CTkFrame(self.stock_list_frame, height=22)
                row_frame.pack(fill="x", padx=1, pady=0)
                row_frame.pack_propagate(False)
                
                value = balance_info['total_quantity'] * balance_info['average_cost']
                total_value += value
                total_products += 1
                
                # Color code based on stock level
                stock_color = "#333333"  # default
                if balance_info['total_quantity'] <= balance_info['danger_level']:
                    stock_color = "#dc3545"  # red for danger
                elif balance_info['total_quantity'] <= balance_info['reorder_level']:
                    stock_color = "#ffc107"  # yellow for low stock
                
                ctk.CTkLabel(row_frame, text=balance_info['product_name'], width=150, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=0, padx=2, pady=0, sticky="w")
                ctk.CTkLabel(row_frame, text=balance_info['batch_number'], width=100, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=1, padx=2, pady=0)
                ctk.CTkLabel(row_frame, text=f"{balance_info['total_quantity']:.2f}", width=100, font=ctk.CTkFont(size=9), text_color=stock_color, height=20).grid(row=0, column=2, padx=2, pady=0)
                ctk.CTkLabel(row_frame, text=f"{balance_info['available_quantity']:.2f}", width=100, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=3, padx=2, pady=0)
                ctk.CTkLabel(row_frame, text=f"{balance_info['reserved_quantity']:.2f}", width=100, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=4, padx=2, pady=0)
                ctk.CTkLabel(row_frame, text=f"₹{balance_info['average_cost']:.2f}", width=100, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=5, padx=2, pady=0)
                ctk.CTkLabel(row_frame, text=f"₹{value:.2f}", width=120, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=6, padx=2, pady=0)
                ctk.CTkLabel(row_frame, text=balance_info['last_updated'], width=120, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=7, padx=2, pady=0)
            
            # Update summary
            summary_text = f"Total Products: {total_products} | Total Inventory Value: ₹{total_value:.2f}"
            self.summary_label.configure(text=summary_text)
            
            if not balances:
                no_data_frame = ctk.CTkFrame(self.stock_list_frame)
                no_data_frame.pack(fill="x", padx=2, pady=20)
                ctk.CTkLabel(no_data_frame, text="No stock data available", font=ctk.CTkFont(size=12)).pack(pady=20)
        
        except Exception as e:
            self.show_message(f"Error loading stock details: {str(e)}", "error")
    
    def filter_stock(self, value):
        self.after(50, self.load_stock_details)