import customtkinter as ctk
from tkinter import ttk
from modules.account_module.ui.screens.base_screen import BaseScreen
from core.database.connection import db_manager
from modules.account_module.models.entities import Ledger, AccountMaster
from core.shared.utils.session_manager import session_manager

class LedgerScreen(BaseScreen):
    def __init__(self, parent, module):
        super().__init__(parent, module, "Ledger")
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        # Filter frame
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        # Account selection
        ctk.CTkLabel(filter_frame, text="Account:").pack(side="left", padx=10)
        self.account_var = ctk.StringVar()
        self.account_combo = ctk.CTkComboBox(filter_frame, variable=self.account_var, width=200)
        self.account_combo.pack(side="left", padx=10)
        
        # Filter button
        filter_btn = ctk.CTkButton(filter_frame, text="Filter", command=self.filter_data)
        filter_btn.pack(side="left", padx=10)
        
        # Treeview for ledger entries
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Date", "Voucher", "Narration", "Debit", "Credit", "Balance")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def load_data(self):
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id() or 1
            accounts = session.query(AccountMaster).filter(AccountMaster.tenant_id == tenant_id).all()
            account_names = [f"{acc.name} ({acc.code})" for acc in accounts]
            self.account_combo.configure(values=account_names)
    
    def filter_data(self):
        if not self.account_var.get():
            return
        
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id() or 1
            account_name = self.account_var.get().split(" (")[0]
            account = session.query(AccountMaster).filter(
                AccountMaster.name == account_name,
                AccountMaster.tenant_id == tenant_id
            ).first()
            
            if account:
                ledger_entries = session.query(Ledger).filter(
                    Ledger.account_id == account.id
                ).order_by(Ledger.transaction_date).all()
                
                for entry in ledger_entries:
                    self.tree.insert("", "end", values=(
                        entry.transaction_date.strftime("%Y-%m-%d"),
                        f"V-{entry.voucher_id}",
                        entry.narration or "",
                        f"{entry.debit_amount:.2f}" if entry.debit_amount > 0 else "",
                        f"{entry.credit_amount:.2f}" if entry.credit_amount > 0 else "",
                        f"{entry.balance:.2f}"
                    ))