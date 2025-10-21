"""Audit Trail Screen"""
import customtkinter as ctk
from core.shared.components.data_grid import DataGrid
from core.shared.utils.session_manager import session_manager
from core.database.connection import db_manager
from modules.account_module.models.audit_trail import AuditTrail

class AuditTrailScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        title = ctk.CTkLabel(self, text="Audit Trail", font=("Arial", 20, "bold"))
        title.pack(pady=10)
        
        # Filter frame
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Entity Type:").pack(side="left", padx=5)
        self.entity_type = ctk.CTkComboBox(filter_frame, 
            values=["All", "VOUCHER", "LEDGER", "ACCOUNT", "PAYMENT", "JOURNAL"],
            width=150)
        self.entity_type.set("All")
        self.entity_type.pack(side="left", padx=5)
        
        ctk.CTkLabel(filter_frame, text="Search:").pack(side="left", padx=5)
        self.search_entry = ctk.CTkEntry(filter_frame, width=200)
        self.search_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(filter_frame, text="Search", command=self.load_data, width=100).pack(side="left", padx=5)
        
        # Data grid
        columns = [
            {"name": "Date/Time", "width": 150},
            {"name": "Entity Type", "width": 100},
            {"name": "Entity ID", "width": 80},
            {"name": "Action", "width": 100},
            {"name": "User", "width": 120},
            {"name": "Details", "width": 300}
        ]
        
        self.grid = DataGrid(self, columns)
        self.grid.pack(fill="both", expand=True, padx=10, pady=5)
    
    def load_data(self):
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id()
            
            query = session.query(AuditTrail).filter(
                AuditTrail.tenant_id == tenant_id
            )
            
            entity_type = self.entity_type.get()
            if entity_type != "All":
                query = query.filter(AuditTrail.entity_type == entity_type)
            
            search = self.search_entry.get()
            if search:
                query = query.filter(
                    (AuditTrail.username.ilike(f"%{search}%")) |
                    (AuditTrail.remarks.ilike(f"%{search}%"))
                )
            
            entries = query.order_by(AuditTrail.created_at.desc()).limit(500).all()
            
            data = []
            for entry in entries:
                details = ""
                if entry.new_value:
                    details = str(entry.new_value)[:100]
                
                data.append([
                    entry.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    entry.entity_type,
                    str(entry.entity_id),
                    entry.action,
                    entry.username or "",
                    details
                ])
            
            self.grid.load_data(data)
