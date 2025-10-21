import customtkinter as ctk
from tkinter import ttk
from modules.account_module.ui.screens.base_screen import BaseScreen
from core.database.connection import db_manager
from modules.account_module.models.entities import AccountMaster, AccountGroup, Ledger
from core.shared.utils.session_manager import session_manager
from datetime import datetime, timedelta

class ReportsScreen(BaseScreen):
    def __init__(self, parent, module):
        super().__init__(parent, module, "Financial Reports")
        self.setup_ui()
    
    def setup_ui(self):
        # Report selection frame
        selection_frame = ctk.CTkFrame(self)
        selection_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(selection_frame, text="Select Report:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        
        self.report_var = ctk.StringVar()
        self.report_combo = ctk.CTkComboBox(
            selection_frame,
            variable=self.report_var,
            values=["Trial Balance", "Balance Sheet", "Profit & Loss", "Account Summary"],
            width=200
        )
        self.report_combo.pack(side="left", padx=10)
        
        # Date range
        ctk.CTkLabel(selection_frame, text="From:").pack(side="left", padx=(20, 5))
        self.from_date = ctk.CTkEntry(selection_frame, width=100, placeholder_text="YYYY-MM-DD")
        self.from_date.pack(side="left", padx=5)
        
        ctk.CTkLabel(selection_frame, text="To:").pack(side="left", padx=(10, 5))
        self.to_date = ctk.CTkEntry(selection_frame, width=100, placeholder_text="YYYY-MM-DD")
        self.to_date.pack(side="left", padx=5)
        
        # Set default dates (current month)
        today = datetime.now()
        first_day = today.replace(day=1)
        self.from_date.insert(0, first_day.strftime("%Y-%m-%d"))
        self.to_date.insert(0, today.strftime("%Y-%m-%d"))
        
        # Generate button
        generate_btn = ctk.CTkButton(selection_frame, text="Generate Report", command=self.generate_report)
        generate_btn.pack(side="left", padx=20)
        
        # Report display frame
        self.report_frame = ctk.CTkFrame(self)
        self.report_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Initial message
        welcome_label = ctk.CTkLabel(
            self.report_frame,
            text="Select a report type and click 'Generate Report' to view financial data",
            font=ctk.CTkFont(size=14)
        )
        welcome_label.pack(pady=50)
    
    def generate_report(self):
        if not self.report_var.get():
            self.show_message("Please select a report type")
            return
        
        # Clear existing content
        for widget in self.report_frame.winfo_children():
            widget.destroy()
        
        report_type = self.report_var.get()
        
        if report_type == "Trial Balance":
            self.generate_trial_balance()
        elif report_type == "Balance Sheet":
            self.generate_balance_sheet()
        elif report_type == "Profit & Loss":
            self.generate_profit_loss()
        elif report_type == "Account Summary":
            self.generate_account_summary()
    
    def generate_trial_balance(self):
        # Title
        title_label = ctk.CTkLabel(
            self.report_frame,
            text="Trial Balance",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Date range label
        date_label = ctk.CTkLabel(
            self.report_frame,
            text=f"From {self.from_date.get()} to {self.to_date.get()}",
            font=ctk.CTkFont(size=12)
        )
        date_label.pack(pady=5)
        
        # Treeview for trial balance
        columns = ("Account Code", "Account Name", "Debit", "Credit")
        tree = ttk.Treeview(self.report_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(self.report_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load data
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id() or 1
            accounts = session.query(AccountMaster, AccountGroup).join(
                AccountGroup, AccountMaster.account_group_id == AccountGroup.id
            ).filter(AccountMaster.tenant_id == tenant_id).all()
            
            total_debit = 0
            total_credit = 0
            
            for account, group in accounts:
                balance = account.current_balance
                if balance != 0:
                    if group.account_type in ['ASSET', 'EXPENSE'] and balance > 0:
                        debit = f"{balance:.2f}"
                        credit = ""
                        total_debit += balance
                    elif group.account_type in ['LIABILITY', 'EQUITY', 'INCOME'] and balance > 0:
                        debit = ""
                        credit = f"{balance:.2f}"
                        total_credit += balance
                    else:
                        debit = f"{abs(balance):.2f}" if balance < 0 else ""
                        credit = f"{balance:.2f}" if balance > 0 else ""
                        if balance < 0:
                            total_debit += abs(balance)
                        else:
                            total_credit += balance
                    
                    tree.insert("", "end", values=(
                        account.code,
                        account.name,
                        debit,
                        credit
                    ))
            
            # Add totals
            tree.insert("", "end", values=("", "TOTAL", f"{total_debit:.2f}", f"{total_credit:.2f}"))
    
    def generate_balance_sheet(self):
        # Title
        title_label = ctk.CTkLabel(
            self.report_frame,
            text="Balance Sheet",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Create two-column layout
        main_frame = ctk.CTkFrame(self.report_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Assets column
        assets_frame = ctk.CTkFrame(main_frame)
        assets_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(assets_frame, text="ASSETS", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Liabilities & Equity column
        liab_frame = ctk.CTkFrame(main_frame)
        liab_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(liab_frame, text="LIABILITIES & EQUITY", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Load and display data
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id() or 1
            accounts = session.query(AccountMaster, AccountGroup).join(
                AccountGroup, AccountMaster.account_group_id == AccountGroup.id
            ).filter(AccountMaster.tenant_id == tenant_id).all()
            
            assets_total = 0
            liab_equity_total = 0
            
            for account, group in accounts:
                if account.current_balance != 0:
                    if group.account_type == 'ASSET':
                        label = ctk.CTkLabel(assets_frame, text=f"{account.name}: {account.current_balance:.2f}")
                        label.pack(anchor="w", padx=10)
                        assets_total += account.current_balance
                    elif group.account_type in ['LIABILITY', 'EQUITY']:
                        label = ctk.CTkLabel(liab_frame, text=f"{account.name}: {account.current_balance:.2f}")
                        label.pack(anchor="w", padx=10)
                        liab_equity_total += account.current_balance
            
            # Totals
            ctk.CTkLabel(assets_frame, text=f"Total Assets: {assets_total:.2f}", 
                        font=ctk.CTkFont(weight="bold")).pack(pady=10)
            ctk.CTkLabel(liab_frame, text=f"Total Liab. & Equity: {liab_equity_total:.2f}", 
                        font=ctk.CTkFont(weight="bold")).pack(pady=10)
    
    def generate_profit_loss(self):
        # Title
        title_label = ctk.CTkLabel(
            self.report_frame,
            text="Profit & Loss Statement",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Treeview for P&L
        columns = ("Account", "Amount")
        tree = ttk.Treeview(self.report_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)
        
        scrollbar = ttk.Scrollbar(self.report_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load data
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id() or 1
            accounts = session.query(AccountMaster, AccountGroup).join(
                AccountGroup, AccountMaster.account_group_id == AccountGroup.id
            ).filter(
                AccountMaster.tenant_id == tenant_id,
                AccountGroup.account_type.in_(['INCOME', 'EXPENSE'])
            ).all()
            
            total_income = 0
            total_expense = 0
            
            # Income section
            tree.insert("", "end", values=("INCOME", ""))
            for account, group in accounts:
                if group.account_type == 'INCOME' and account.current_balance != 0:
                    tree.insert("", "end", values=(f"  {account.name}", f"{account.current_balance:.2f}"))
                    total_income += account.current_balance
            
            tree.insert("", "end", values=("Total Income", f"{total_income:.2f}"))
            tree.insert("", "end", values=("", ""))
            
            # Expense section
            tree.insert("", "end", values=("EXPENSES", ""))
            for account, group in accounts:
                if group.account_type == 'EXPENSE' and account.current_balance != 0:
                    tree.insert("", "end", values=(f"  {account.name}", f"{account.current_balance:.2f}"))
                    total_expense += account.current_balance
            
            tree.insert("", "end", values=("Total Expenses", f"{total_expense:.2f}"))
            tree.insert("", "end", values=("", ""))
            
            # Net profit/loss
            net_profit = total_income - total_expense
            tree.insert("", "end", values=("NET PROFIT/LOSS", f"{net_profit:.2f}"))
    
    def generate_account_summary(self):
        # Title
        title_label = ctk.CTkLabel(
            self.report_frame,
            text="Account Summary",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Summary cards frame
        cards_frame = ctk.CTkFrame(self.report_frame)
        cards_frame.pack(fill="x", padx=10, pady=10)
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id() or 1
            
            # Get account counts by type
            accounts = session.query(AccountMaster, AccountGroup).join(
                AccountGroup, AccountMaster.account_group_id == AccountGroup.id
            ).filter(AccountMaster.tenant_id == tenant_id).all()
            
            type_counts = {}
            type_balances = {}
            
            for account, group in accounts:
                acc_type = group.account_type
                type_counts[acc_type] = type_counts.get(acc_type, 0) + 1
                type_balances[acc_type] = type_balances.get(acc_type, 0) + account.current_balance
            
            # Create summary cards
            for i, (acc_type, count) in enumerate(type_counts.items()):
                card = ctk.CTkFrame(cards_frame)
                card.pack(side="left", fill="both", expand=True, padx=5)
                
                ctk.CTkLabel(card, text=acc_type, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
                ctk.CTkLabel(card, text=f"Accounts: {count}").pack()
                ctk.CTkLabel(card, text=f"Balance: {type_balances[acc_type]:.2f}").pack(pady=(0, 10))