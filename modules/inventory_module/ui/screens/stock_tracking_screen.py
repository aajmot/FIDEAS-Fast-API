import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from core.shared.components.base_screen import BaseScreen
from core.shared.components.searchable_dropdown import SearchableDropdown
from modules.inventory_module.services.stock_service import StockService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class StockTrackingScreen(BaseScreen):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.stock_service = StockService()
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Stock Tracking", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Tab view
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create tabs
        self.tab_view.add("Stock Summary")
        self.tab_view.add("Transactions")
        self.tab_view.add("Stock Balances")
        
        self.setup_summary_tab()
        self.setup_transactions_tab()
        self.setup_balances_tab()
        
        self.load_products()
    
    def setup_summary_tab(self):
        summary_frame = self.tab_view.tab("Stock Summary")
        
        # Filter frame
        filter_frame = ctk.CTkFrame(summary_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Product Filter:").pack(side="left", padx=10, pady=10)
        self.product_filter = SearchableDropdown(filter_frame, values=[], width=200, placeholder_text="All Products", command=self.filter_summary)
        self.product_filter.pack(side="left", padx=10, pady=10)
        
        ctk.CTkButton(filter_frame, text="Refresh", command=self.load_summary, height=30).pack(side="right", padx=10, pady=10)
        
        # Summary list
        summary_list_frame = ctk.CTkScrollableFrame(summary_frame)
        summary_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Header
        header_frame = ctk.CTkFrame(summary_list_frame, fg_color="#e0e0e0")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        headers = ["Product", "Total Stock", "Available", "Avg Cost", "Total Value"]
        widths = [200, 100, 100, 100, 120]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=11, weight="bold"), 
                        text_color="#333333", width=width).grid(row=0, column=i, padx=2, pady=5)
        
        self.summary_list_frame = ctk.CTkFrame(summary_list_frame)
        self.summary_list_frame.pack(fill="x", padx=5, pady=5)
        
        self.load_summary()
    
    def setup_transactions_tab(self):
        transactions_frame = self.tab_view.tab("Transactions")
        
        # Filter frame
        filter_frame = ctk.CTkFrame(transactions_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Product Filter:").pack(side="left", padx=10, pady=10)
        self.transaction_product_filter = SearchableDropdown(filter_frame, values=[], width=200, placeholder_text="All Products", command=self.filter_transactions)
        self.transaction_product_filter.pack(side="left", padx=10, pady=10)
        
        ctk.CTkButton(filter_frame, text="Refresh", command=self.load_transactions, height=30).pack(side="right", padx=10, pady=10)
        
        # Transactions list
        transactions_list_frame = ctk.CTkScrollableFrame(transactions_frame)
        transactions_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Header
        header_frame = ctk.CTkFrame(transactions_list_frame, fg_color="#e0e0e0")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        headers = ["Date", "Product", "Type", "Source", "Reference", "Batch", "Quantity", "Price"]
        widths = [100, 150, 60, 80, 120, 80, 80, 80]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=10, weight="bold"), 
                        text_color="#333333", width=width).grid(row=0, column=i, padx=1, pady=5)
        
        self.transactions_list_frame = ctk.CTkFrame(transactions_list_frame)
        self.transactions_list_frame.pack(fill="x", padx=5, pady=5)
        
        self.load_transactions()
    
    def setup_balances_tab(self):
        balances_frame = self.tab_view.tab("Stock Balances")
        
        # Filter frame
        filter_frame = ctk.CTkFrame(balances_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Product Filter:").pack(side="left", padx=10, pady=10)
        self.balance_product_filter = SearchableDropdown(filter_frame, values=[], width=200, placeholder_text="All Products", command=self.filter_balances)
        self.balance_product_filter.pack(side="left", padx=10, pady=10)
        
        ctk.CTkButton(filter_frame, text="Refresh", command=self.load_balances, height=30).pack(side="right", padx=10, pady=10)
        
        # Balances list
        balances_list_frame = ctk.CTkScrollableFrame(balances_frame)
        balances_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Header
        header_frame = ctk.CTkFrame(balances_list_frame, fg_color="#e0e0e0")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        headers = ["Product", "Batch", "Total Qty", "Available", "Reserved", "Avg Cost", "Value"]
        widths = [150, 100, 80, 80, 80, 80, 100]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=10, weight="bold"), 
                        text_color="#333333", width=width).grid(row=0, column=i, padx=2, pady=5)
        
        self.balances_list_frame = ctk.CTkFrame(balances_list_frame)
        self.balances_list_frame.pack(fill="x", padx=5, pady=5)
        
        self.load_balances()
    
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
            self.transaction_product_filter.configure_values(product_values)
            self.balance_product_filter.configure_values(product_values)
    
    def load_summary(self):
        # Clear existing summary
        for widget in self.summary_list_frame.winfo_children():
            widget.destroy()
        
        try:
            summary_data = self.stock_service.get_product_stock_summary()
            
            for i, summary in enumerate(summary_data):
                row_frame = ctk.CTkFrame(self.summary_list_frame, height=22)
                row_frame.pack(fill="x", padx=1, pady=0)
                row_frame.pack_propagate(False)
                
                total_value = float(summary.total_stock or 0) * float(summary.avg_cost or 0)
                
                ctk.CTkLabel(row_frame, text=summary.name, width=200, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=0, padx=2, pady=0, sticky="w")
                ctk.CTkLabel(row_frame, text=f"{float(summary.total_stock or 0):.2f}", width=100, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=1, padx=2, pady=0)
                ctk.CTkLabel(row_frame, text=f"{float(summary.available_stock or 0):.2f}", width=100, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=2, padx=2, pady=0)
                ctk.CTkLabel(row_frame, text=f"₹{float(summary.avg_cost or 0):.2f}", width=100, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=3, padx=2, pady=0)
                ctk.CTkLabel(row_frame, text=f"₹{total_value:.2f}", width=120, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=4, padx=2, pady=0)
        
        except Exception as e:
            self.show_message(f"Error loading summary: {str(e)}", "error")
    
    def load_transactions(self):
        # Clear existing transactions
        for widget in self.transactions_list_frame.winfo_children():
            widget.destroy()
        
        try:
            from core.database.connection import db_manager
            from modules.inventory_module.models.stock_entities import StockTransaction
            from modules.inventory_module.models.entities import Product
            from core.shared.utils.session_manager import session_manager
            
            product_id = None
            filter_value = self.transaction_product_filter.get().strip()
            if filter_value and filter_value != "All Products" and ':' in filter_value:
                product_id = int(filter_value.split(':')[0])
            
            with db_manager.get_session() as session:
                query = session.query(StockTransaction).join(Product)
                tenant_id = session_manager.get_current_tenant_id()
                if tenant_id:
                    query = query.filter(Product.tenant_id == tenant_id)
                if product_id:
                    query = query.filter(StockTransaction.product_id == product_id)
                
                transactions = query.order_by(StockTransaction.transaction_date.desc()).all()
                
                for transaction in transactions:
                    row_frame = ctk.CTkFrame(self.transactions_list_frame, height=20)
                    row_frame.pack(fill="x", padx=1, pady=0)
                    row_frame.pack_propagate(False)
                    
                    date_str = transaction.transaction_date.strftime('%Y-%m-%d') if transaction.transaction_date else ''
                    type_color = "#28a745" if transaction.transaction_type == "IN" else "#dc3545"
                    
                    ctk.CTkLabel(row_frame, text=date_str, width=100, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=0, padx=1, pady=0)
                    ctk.CTkLabel(row_frame, text=transaction.product.name, width=150, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=1, padx=1, pady=0, sticky="w")
                    ctk.CTkLabel(row_frame, text=transaction.transaction_type, width=60, font=ctk.CTkFont(size=8), text_color=type_color, height=18).grid(row=0, column=2, padx=1, pady=0)
                    ctk.CTkLabel(row_frame, text=transaction.transaction_source, width=80, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=3, padx=1, pady=0)
                    ctk.CTkLabel(row_frame, text=transaction.reference_number, width=120, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=4, padx=1, pady=0)
                    ctk.CTkLabel(row_frame, text=transaction.batch_number or "", width=80, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=5, padx=1, pady=0)
                    ctk.CTkLabel(row_frame, text=f"{float(transaction.quantity):.2f}", width=80, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=6, padx=1, pady=0)
                    ctk.CTkLabel(row_frame, text=f"₹{float(transaction.unit_price):.2f}", width=80, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=7, padx=1, pady=0)
        
        except Exception as e:
            self.show_message(f"Error loading transactions: {str(e)}", "error")
    
    def load_balances(self):
        # Clear existing balances
        for widget in self.balances_list_frame.winfo_children():
            widget.destroy()
        
        try:
            from core.database.connection import db_manager
            from modules.inventory_module.models.stock_entities import StockBalance
            from modules.inventory_module.models.entities import Product
            from core.shared.utils.session_manager import session_manager
            
            product_id = None
            filter_value = self.balance_product_filter.get().strip()
            if filter_value and filter_value != "All Products" and ':' in filter_value:
                product_id = int(filter_value.split(':')[0])
            
            with db_manager.get_session() as session:
                query = session.query(StockBalance).join(Product)
                tenant_id = session_manager.get_current_tenant_id()
                if tenant_id:
                    query = query.filter(Product.tenant_id == tenant_id)
                if product_id:
                    query = query.filter(StockBalance.product_id == product_id)
                
                balances = query.all()
                
                for balance in balances:
                    row_frame = ctk.CTkFrame(self.balances_list_frame, height=20)
                    row_frame.pack(fill="x", padx=1, pady=0)
                    row_frame.pack_propagate(False)
                    
                    value = float(balance.total_quantity) * float(balance.average_cost)
                    
                    ctk.CTkLabel(row_frame, text=balance.product.name, width=150, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=0, padx=2, pady=0, sticky="w")
                    ctk.CTkLabel(row_frame, text=balance.batch_number or "", width=100, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=1, padx=2, pady=0)
                    ctk.CTkLabel(row_frame, text=f"{float(balance.total_quantity):.2f}", width=80, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=2, padx=2, pady=0)
                    ctk.CTkLabel(row_frame, text=f"{float(balance.available_quantity):.2f}", width=80, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=3, padx=2, pady=0)
                    ctk.CTkLabel(row_frame, text=f"{float(balance.reserved_quantity):.2f}", width=80, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=4, padx=2, pady=0)
                    ctk.CTkLabel(row_frame, text=f"₹{float(balance.average_cost):.2f}", width=80, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=5, padx=2, pady=0)
                    ctk.CTkLabel(row_frame, text=f"₹{value:.2f}", width=100, font=ctk.CTkFont(size=8), height=18).grid(row=0, column=6, padx=2, pady=0)
        
        except Exception as e:
            self.show_message(f"Error loading balances: {str(e)}", "error")
    
    def filter_summary(self, value):
        self.after(50, self.load_summary)
    
    def filter_transactions(self, value):
        self.after(50, self.load_transactions)
    
    def filter_balances(self, value):
        self.after(50, self.load_balances)