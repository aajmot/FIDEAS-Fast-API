import customtkinter as ctk
from tkinter import ttk
from modules.account_module.ui.screens.base_screen import BaseScreen
from core.database.connection import db_manager
from modules.account_module.models.entities import AccountMaster, AccountGroup
from core.shared.utils.session_manager import session_manager
from core.shared.components.import_mixin import ImportMixin

class AccountMasterScreen(BaseScreen, ImportMixin):
    def __init__(self, parent, module):
        super().__init__(parent, module, "Chart of Accounts")
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        # Filter frame
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        # Account type filter
        ctk.CTkLabel(filter_frame, text="Type:").pack(side="left", padx=10)
        self.type_var = ctk.StringVar()
        self.type_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.type_var,
            values=["All", "ASSET", "LIABILITY", "EQUITY", "INCOME", "EXPENSE"],
            width=120
        )
        self.type_combo.set("All")
        self.type_combo.pack(side="left", padx=10)
        
        # Status filter
        ctk.CTkLabel(filter_frame, text="Status:").pack(side="left", padx=10)
        self.status_var = ctk.StringVar()
        self.status_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.status_var,
            values=["All", "Active", "Inactive"],
            width=100
        )
        self.status_combo.set("All")
        self.status_combo.pack(side="left", padx=10)
        
        # Filter button
        filter_btn = ctk.CTkButton(filter_frame, text="Filter", command=self.filter_data)
        filter_btn.pack(side="left", padx=10)
        
        # Import buttons
        self.add_import_button(filter_frame)
        
        # Accounts treeview
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Code", "Name", "Group", "Type", "Opening Balance", "Current Balance", "Status")
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
        
        self.summary_label = ctk.CTkLabel(summary_frame, text="", font=ctk.CTkFont(size=12))
        self.summary_label.pack(pady=5)
    
    def load_data(self):
        self.filter_data()
    
    def filter_data(self):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id() or 1
            query = session.query(AccountMaster, AccountGroup).join(
                AccountGroup, AccountMaster.account_group_id == AccountGroup.id
            ).filter(AccountMaster.tenant_id == tenant_id)
            
            # Apply filters
            if self.type_var.get() != "All":
                query = query.filter(AccountGroup.account_type == self.type_var.get())
            
            if self.status_var.get() != "All":
                is_active = self.status_var.get() == "Active"
                query = query.filter(AccountMaster.is_active == is_active)
            
            accounts = query.order_by(AccountMaster.code).all()
            
            # Summary counters
            type_summary = {"ASSET": 0, "LIABILITY": 0, "EQUITY": 0, "INCOME": 0, "EXPENSE": 0}
            total_balance = 0
            
            for account, group in accounts:
                status = "Active" if account.is_active else "Inactive"
                
                self.tree.insert("", "end", values=(
                    account.code,
                    account.name,
                    f"{group.name} ({group.code})",
                    group.account_type,
                    f"{account.opening_balance:.2f}",
                    f"{account.current_balance:.2f}",
                    status
                ))
                
                type_summary[group.account_type] += 1
                total_balance += account.current_balance
            
            # Update summary
            summary_text = f"Total Accounts: {len(accounts)} | "
            summary_text += " | ".join([f"{k}: {v}" for k, v in type_summary.items() if v > 0])
            summary_text += f" | Total Balance: {total_balance:.2f}"
            
            self.summary_label.configure(text=summary_text)
    
    def download_template(self):
        template_data = {
            'Name': ['Cash Account', 'Bank Account', 'Sales Revenue'],
            'Code': ['1001', '1002', '4001'],
            'Account Group': ['Cash', 'Bank', 'Sales'],
            'Opening Balance': [1000.00, 5000.00, 0.00]
        }
        self.create_template_file(template_data, 'accounts')
    
    def import_from_excel(self):
        def process_account_row(row, index):
            name = str(row['Name']).strip()
            code = str(row['Code']).strip()
            group_name = str(row['Account Group']).strip()
            opening_balance = float(row.get('Opening Balance', 0))
            
            if not name or not code:
                return False
            
            # Find account group by name
            with db_manager.get_session() as session:
                tenant_id = session_manager.get_current_tenant_id() or 1
                group = session.query(AccountGroup).filter(
                    AccountGroup.name == group_name,
                    AccountGroup.tenant_id == tenant_id
                ).first()
                
                if not group:
                    raise Exception(f"Account group '{group_name}' not found")
                
                account_data = {
                    'name': name,
                    'code': code,
                    'account_group_id': group.id,
                    'opening_balance': opening_balance,
                    'current_balance': opening_balance,
                    'tenant_id': tenant_id
                }
                
                account = AccountMaster(**account_data)
                session.add(account)
                session.commit()
            
            return True
        
        self.process_import_file(['Name', 'Code', 'Account Group'], process_account_row, 'accounts')