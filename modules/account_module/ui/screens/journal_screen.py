import customtkinter as ctk
from tkinter import ttk
from modules.account_module.ui.screens.base_screen import BaseScreen
from core.database.connection import db_manager
from modules.account_module.models.entities import Journal, JournalDetail, AccountMaster
from core.shared.utils.session_manager import session_manager

class JournalScreen(BaseScreen):
    def __init__(self, parent, module):
        super().__init__(parent, module, "Journal Entries")
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        # Journal list frame
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Journal entries treeview
        columns = ("Date", "Voucher", "Total Debit", "Total Credit", "Status")
        self.journal_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.journal_tree.heading(col, text=col)
            self.journal_tree.column(col, width=120)
        
        scrollbar1 = ttk.Scrollbar(list_frame, orient="vertical", command=self.journal_tree.yview)
        self.journal_tree.configure(yscrollcommand=scrollbar1.set)
        
        self.journal_tree.pack(side="left", fill="both", expand=True)
        scrollbar1.pack(side="right", fill="y")
        
        # Bind selection event
        self.journal_tree.bind("<<TreeviewSelect>>", self.on_journal_select)
        
        # Journal details frame
        details_frame = ctk.CTkFrame(self)
        details_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(details_frame, text="Journal Details", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Journal details treeview
        detail_columns = ("Account", "Narration", "Debit", "Credit")
        self.detail_tree = ttk.Treeview(details_frame, columns=detail_columns, show="headings", height=8)
        
        for col in detail_columns:
            self.detail_tree.heading(col, text=col)
            self.detail_tree.column(col, width=150)
        
        scrollbar2 = ttk.Scrollbar(details_frame, orient="vertical", command=self.detail_tree.yview)
        self.detail_tree.configure(yscrollcommand=scrollbar2.set)
        
        self.detail_tree.pack(side="left", fill="both", expand=True)
        scrollbar2.pack(side="right", fill="y")
    
    def load_data(self):
        # Clear existing data
        for item in self.journal_tree.get_children():
            self.journal_tree.delete(item)
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id() or 1
            journals = session.query(Journal).filter(
                Journal.tenant_id == tenant_id
            ).order_by(Journal.journal_date.desc()).all()
            
            for journal in journals:
                status = "Balanced" if journal.is_balanced else "Unbalanced"
                self.journal_tree.insert("", "end", values=(
                    journal.journal_date.strftime("%Y-%m-%d"),
                    f"V-{journal.voucher_id}",
                    f"{journal.total_debit:.2f}",
                    f"{journal.total_credit:.2f}",
                    status
                ), tags=(journal.id,))
    
    def on_journal_select(self, event):
        selection = self.journal_tree.selection()
        if not selection:
            return
        
        # Clear details
        for item in self.detail_tree.get_children():
            self.detail_tree.delete(item)
        
        # Get journal ID from tags
        item = self.journal_tree.item(selection[0])
        journal_id = item['tags'][0] if item['tags'] else None
        
        if journal_id:
            with db_manager.get_session() as session:
                details = session.query(JournalDetail, AccountMaster).join(
                    AccountMaster, JournalDetail.account_id == AccountMaster.id
                ).filter(JournalDetail.journal_id == journal_id).all()
                
                for detail, account in details:
                    self.detail_tree.insert("", "end", values=(
                        f"{account.name} ({account.code})",
                        detail.narration or "",
                        f"{detail.debit_amount:.2f}" if detail.debit_amount > 0 else "",
                        f"{detail.credit_amount:.2f}" if detail.credit_amount > 0 else ""
                    ))