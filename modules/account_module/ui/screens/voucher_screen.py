import customtkinter as ctk
from tkinter import ttk
from modules.account_module.ui.screens.base_screen import BaseScreen
from core.database.connection import db_manager
from modules.account_module.models.entities import Voucher, VoucherType
from core.shared.utils.session_manager import session_manager

class VoucherScreen(BaseScreen):
    def __init__(self, parent, module):
        super().__init__(parent, module, "Vouchers")
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        # Filter frame
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        # Voucher type filter
        ctk.CTkLabel(filter_frame, text="Type:").pack(side="left", padx=10)
        self.type_var = ctk.StringVar()
        self.type_combo = ctk.CTkComboBox(filter_frame, variable=self.type_var, width=150)
        self.type_combo.pack(side="left", padx=10)
        
        # Status filter
        ctk.CTkLabel(filter_frame, text="Status:").pack(side="left", padx=10)
        self.status_var = ctk.StringVar()
        self.status_combo = ctk.CTkComboBox(
            filter_frame, 
            variable=self.status_var,
            values=["All", "Posted", "Unposted"],
            width=100
        )
        self.status_combo.set("All")
        self.status_combo.pack(side="left", padx=10)
        
        # Filter button
        filter_btn = ctk.CTkButton(filter_frame, text="Filter", command=self.filter_data)
        filter_btn.pack(side="left", padx=10)
        
        # Vouchers treeview
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("Number", "Type", "Date", "Reference", "Amount", "Status", "Created By")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Button frame
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="View Details", command=self.view_details).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Post Voucher", command=self.post_voucher).pack(side="left", padx=10)
    
    def load_data(self):
        # Load voucher types
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id() or 1
            voucher_types = session.query(VoucherType).filter(VoucherType.tenant_id == tenant_id).all()
            type_names = ["All"] + [vt.name for vt in voucher_types]
            self.type_combo.configure(values=type_names)
            self.type_combo.set("All")
        
        self.filter_data()
    
    def filter_data(self):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        with db_manager.get_session() as session:
            tenant_id = session_manager.get_current_tenant_id() or 1
            query = session.query(Voucher, VoucherType).join(
                VoucherType, Voucher.voucher_type_id == VoucherType.id
            ).filter(Voucher.tenant_id == tenant_id)
            
            # Apply filters
            if self.type_var.get() and self.type_var.get() != "All":
                query = query.filter(VoucherType.name == self.type_var.get())
            
            if self.status_var.get() != "All":
                is_posted = self.status_var.get() == "Posted"
                query = query.filter(Voucher.is_posted == is_posted)
            
            vouchers = query.order_by(Voucher.voucher_date.desc()).all()
            
            for voucher, voucher_type in vouchers:
                status = "Posted" if voucher.is_posted else "Unposted"
                reference = voucher.reference_number or f"{voucher.reference_type}-{voucher.reference_id}" if voucher.reference_type else ""
                
                self.tree.insert("", "end", values=(
                    voucher.voucher_number,
                    voucher_type.name,
                    voucher.voucher_date.strftime("%Y-%m-%d"),
                    reference,
                    f"{voucher.total_amount:.2f}",
                    status,
                    voucher.created_by or ""
                ), tags=(voucher.id,))
    
    def view_details(self):
        selection = self.tree.selection()
        if not selection:
            self.show_message("Please select a voucher to view details")
            return
        
        item = self.tree.item(selection[0])
        voucher_id = item['tags'][0] if item['tags'] else None
        
        if voucher_id:
            self.show_voucher_details(voucher_id)
    
    def show_voucher_details(self, voucher_id):
        # Create details window
        details_window = ctk.CTkToplevel(self)
        details_window.title("Voucher Details")
        details_window.geometry("600x400")
        details_window.transient(self)
        details_window.grab_set()
        
        with db_manager.get_session() as session:
            voucher = session.query(Voucher).filter(Voucher.id == voucher_id).first()
            if voucher:
                # Voucher info
                info_frame = ctk.CTkFrame(details_window)
                info_frame.pack(fill="x", padx=20, pady=10)
                
                ctk.CTkLabel(info_frame, text=f"Voucher: {voucher.voucher_number}", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
                ctk.CTkLabel(info_frame, text=f"Date: {voucher.voucher_date.strftime('%Y-%m-%d')}").pack()
                ctk.CTkLabel(info_frame, text=f"Amount: {voucher.total_amount:.2f}").pack()
                if voucher.narration:
                    ctk.CTkLabel(info_frame, text=f"Narration: {voucher.narration}").pack()
    
    def post_voucher(self):
        selection = self.tree.selection()
        if not selection:
            self.show_message("Please select a voucher to post")
            return
        
        item = self.tree.item(selection[0])
        voucher_id = item['tags'][0] if item['tags'] else None
        
        if voucher_id:
            with db_manager.get_session() as session:
                voucher = session.query(Voucher).filter(Voucher.id == voucher_id).first()
                if voucher and not voucher.is_posted:
                    voucher.is_posted = True
                    session.commit()
                    self.show_message("Voucher posted successfully")
                    self.filter_data()
                elif voucher and voucher.is_posted:
                    self.show_message("Voucher is already posted")
                else:
                    self.show_message("Voucher not found")