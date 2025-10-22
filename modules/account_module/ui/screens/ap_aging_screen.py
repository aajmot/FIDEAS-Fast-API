"""AP Aging Report Screen"""
import customtkinter as ctk
from datetime import datetime
from core.shared.components.data_grid import DataGrid
from core.shared.utils.session_manager import session_manager
from core.database.connection import db_manager
from modules.account_module.models.entities import Ledger, AccountMaster, Voucher
from sqlalchemy import func

class APAgingScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        title = ctk.CTkLabel(self, text="AP Aging Report", font=("Arial", 20, "bold"))
        title.pack(pady=10)
        
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="As of Date:").pack(side="left", padx=5)
        self.date_entry = ctk.CTkEntry(filter_frame, width=150)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(filter_frame, text="Refresh", command=self.load_data, width=100).pack(side="left", padx=5)
        
        self.summary_frame = ctk.CTkFrame(self)
        self.summary_frame.pack(fill="x", padx=10, pady=5)
        
        columns = [
            {"name": "Bill #", "width": 120},
            {"name": "Date", "width": 100},
            {"name": "Reference", "width": 120},
            {"name": "Amount", "width": 100},
            {"name": "Balance", "width": 100},
            {"name": "Days", "width": 80},
            {"name": "Current", "width": 100},
            {"name": "31-60", "width": 100},
            {"name": "61-90", "width": 100},
            {"name": "Over 90", "width": 100}
        ]
        
        self.grid = DataGrid(self, columns)
        self.grid.pack(fill="both", expand=True, padx=10, pady=5)
    
    def load_data(self):
        try:
            as_of_date = datetime.strptime(self.date_entry.get(), "%Y-%m-%d").date()
        except:
            as_of_date = datetime.now().date()
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            ap_account = session.query(AccountMaster).filter(
                AccountMaster.code == 'AP001',
                AccountMaster.tenant_id == tenant_id
            ).first()
            
            if not ap_account:
                return
            
            bills = session.query(
                Voucher.id, Voucher.voucher_number, Voucher.voucher_date,
                Voucher.total_amount, Voucher.reference_number
            ).join(Ledger).filter(
                Ledger.account_id == ap_account.id,
                Ledger.credit_amount > 0,
                Voucher.voucher_date <= as_of_date,
                Voucher.tenant_id == tenant_id
            ).all()
            
            data = []
            totals = {"current": 0, "31_60": 0, "61_90": 0, "over_90": 0, "total": 0}
            
            for bill in bills:
                days = (as_of_date - bill.voucher_date.date()).days
                
                paid = session.query(func.coalesce(func.sum(Ledger.debit_amount), 0)).filter(
                    Ledger.voucher_id == bill.id,
                    Ledger.account_id == ap_account.id
                ).scalar() or 0
                
                balance = float(bill.total_amount) - float(paid)
                
                if balance > 0.01:
                    current = balance if days <= 30 else 0
                    d31_60 = balance if 31 <= days <= 60 else 0
                    d61_90 = balance if 61 <= days <= 90 else 0
                    over_90 = balance if days > 90 else 0
                    
                    data.append([
                        bill.voucher_number,
                        bill.voucher_date.strftime("%Y-%m-%d"),
                        bill.reference_number or "",
                        f"{bill.total_amount:,.2f}",
                        f"{balance:,.2f}",
                        str(days),
                        f"{current:,.2f}",
                        f"{d31_60:,.2f}",
                        f"{d61_90:,.2f}",
                        f"{over_90:,.2f}"
                    ])
                    
                    totals["current"] += current
                    totals["31_60"] += d31_60
                    totals["61_90"] += d61_90
                    totals["over_90"] += over_90
                    totals["total"] += balance
            
            self.grid.load_data(data)
            self.update_summary(totals)
    
    def update_summary(self, totals):
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(self.summary_frame, text=f"Total: ₹{totals['total']:,.2f}", 
                    font=("Arial", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(self.summary_frame, text=f"Current: ₹{totals['current']:,.2f}").pack(side="left", padx=10)
        ctk.CTkLabel(self.summary_frame, text=f"31-60: ₹{totals['31_60']:,.2f}").pack(side="left", padx=10)
        ctk.CTkLabel(self.summary_frame, text=f"61-90: ₹{totals['61_90']:,.2f}").pack(side="left", padx=10)
        ctk.CTkLabel(self.summary_frame, text=f"Over 90: ₹{totals['over_90']:,.2f}").pack(side="left", padx=10)
