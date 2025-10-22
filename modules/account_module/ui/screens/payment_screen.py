import customtkinter as ctk
from tkinter import ttk
from modules.account_module.ui.screens.base_screen import BaseScreen
from core.database.connection import db_manager
from modules.account_module.models.entities import Payment, AccountMaster
from core.shared.utils.session_manager import session_manager

class PaymentScreen(BaseScreen):
    def __init__(self, parent, module):
        super().__init__(parent, module, "Payments")
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        # Filter frame
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        # Payment type filter
        ctk.CTkLabel(filter_frame, text="Type:").pack(side="left", padx=10)
        self.type_var = ctk.StringVar()
        self.type_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.type_var,
            values=["All", "CASH", "BANK", "CARD"],
            width=100
        )
        self.type_combo.set("All")
        self.type_combo.pack(side="left", padx=10)
        
        # Payment mode filter
        ctk.CTkLabel(filter_frame, text="Mode:").pack(side="left", padx=10)
        self.mode_var = ctk.StringVar()
        self.mode_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.mode_var,
            values=["All", "RECEIVED", "PAID"],
            width=100
        )
        self.mode_combo.set("All")
        self.mode_combo.pack(side="left", padx=10)
        
        # Filter button
        filter_btn = ctk.CTkButton(filter_frame, text="Filter", command=self.filter_data)
        filter_btn.pack(side="left", padx=10)
        
        # Payments treeview
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Number", "Date", "Type", "Mode", "Reference", "Amount", "Account", "Created By")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Summary frame
        summary_frame = ctk.CTkFrame(self)
        summary_frame.pack(fill="x", padx=20, pady=10)
        
        self.summary_label = ctk.CTkLabel(summary_frame, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.summary_label.pack(pady=10)
    
    def load_data(self):
        self.filter_data()
    
    def filter_data(self):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id() or 1
            query = session.query(Payment, AccountMaster).outerjoin(
                AccountMaster, Payment.account_id == AccountMaster.id
            ).filter(Payment.tenant_id == tenant_id)
            
            # Apply filters
            if self.type_var.get() != "All":
                query = query.filter(Payment.payment_type == self.type_var.get())
            
            if self.mode_var.get() != "All":
                query = query.filter(Payment.payment_mode == self.mode_var.get())
            
            payments = query.order_by(Payment.payment_date.desc()).all()
            
            total_received = 0
            total_paid = 0
            
            for payment, account in payments:
                account_name = account.name if account else "N/A"
                reference = f"{payment.reference_type}-{payment.reference_number}"
                
                self.tree.insert("", "end", values=(
                    payment.payment_number,
                    payment.payment_date.strftime("%Y-%m-%d"),
                    payment.payment_type,
                    payment.payment_mode,
                    reference,
                    f"{payment.amount:.2f}",
                    account_name,
                    payment.created_by or ""
                ))
                
                if payment.payment_mode == "RECEIVED":
                    total_received += payment.amount
                else:
                    total_paid += payment.amount
            
            # Update summary
            self.summary_label.configure(
                text=f"Total Received: {total_received:.2f} | Total Paid: {total_paid:.2f} | Net: {(total_received - total_paid):.2f}"
            )