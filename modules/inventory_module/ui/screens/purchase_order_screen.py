import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from core.shared.components.base_screen import BaseScreen
from core.shared.components.searchable_dropdown import SearchableDropdown
from modules.inventory_module.services.purchase_order_service import PurchaseOrderService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class PurchaseOrderScreen(BaseScreen):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.purchase_order_service = PurchaseOrderService()
        self.selected_order = None
        self.order_items = []
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Purchase Order", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Tab view
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create tabs
        self.tab_view.add("Create Order")
        self.tab_view.add("View Orders")
        
        self.setup_create_tab()
        self.setup_view_tab()
    
    def setup_create_tab(self):
        create_frame = self.tab_view.tab("Create Order")
        
        # Order Info Frame
        info_frame = ctk.CTkFrame(create_frame)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        # Row 1
        ctk.CTkLabel(info_frame, text="PO Number:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.po_number_input = ctk.CTkEntry(info_frame, width=150)
        self.po_number_input.grid(row=0, column=1, padx=5, pady=5)
        self.generate_po_number()
        
        ctk.CTkLabel(info_frame, text="Supplier:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.supplier_combo = SearchableDropdown(
            info_frame, 
            values=[], 
            width=200, 
            placeholder_text="Search supplier...",
            command=self.on_supplier_select
        )
        self.supplier_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(info_frame, text="Date:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.date_input = ctk.CTkEntry(info_frame, width=120, placeholder_text="YYYY-MM-DD")
        self.date_input.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.date_input.grid(row=0, column=5, padx=5, pady=5)
        
        # Row 2 - Supplier Info
        ctk.CTkLabel(info_frame, text="Supplier Name:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.supplier_name_label = ctk.CTkLabel(info_frame, text="", width=150, anchor="w")
        self.supplier_name_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(info_frame, text="Tax ID:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.tax_id_label = ctk.CTkLabel(info_frame, text="", width=200, anchor="w")
        self.tax_id_label.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        
        # Main content frame with items and summary side by side
        content_frame = ctk.CTkFrame(create_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Items Frame (left side)
        items_frame = ctk.CTkFrame(content_frame)
        items_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Items header with Add button
        items_header = ctk.CTkFrame(items_frame)
        items_header.pack(fill="x", pady=5)
        
        ctk.CTkLabel(items_header, text="Order Items", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        ctk.CTkButton(items_header, text="+ Add Item", command=self.add_item_row, height=25, width=80).pack(side="right", padx=10)
        
        # Items Grid Header
        header_frame = ctk.CTkFrame(items_frame, fg_color="#e0e0e0")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        headers = ["Product", "Batch No", "MRP", "Price", "Qty", "Free Qty", "GST%", "SGST", "CGST", "Disc%", "DiscAmt", "Total"]
        widths = [120, 80, 70, 70, 50, 50, 50, 50, 50, 50, 70, 70]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=9, weight="bold"), 
                        text_color="#333333", width=width).grid(row=0, column=i, padx=1, pady=5)
        
        # Scrollable items frame
        self.items_scroll_frame = ctk.CTkScrollableFrame(items_frame, height=120)
        self.items_scroll_frame.pack(fill="x", padx=5, pady=5)
        
        # Summary Frame (right side)
        summary_frame = ctk.CTkFrame(content_frame, width=220)
        summary_frame.pack(side="right", fill="y", padx=(5, 0))
        summary_frame.pack_propagate(False)
        
        ctk.CTkLabel(summary_frame, text="Order Summary", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(5, 10))
        
        # Summary fields
        summary_grid = ctk.CTkFrame(summary_frame)
        summary_grid.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(summary_grid, text="Subtotal:", font=ctk.CTkFont(size=10)).grid(row=0, column=0, padx=3, pady=1, sticky="w")
        self.subtotal_label = ctk.CTkLabel(summary_grid, text="₹0.00", font=ctk.CTkFont(size=10, weight="bold"))
        self.subtotal_label.grid(row=0, column=1, padx=3, pady=1)
        
        ctk.CTkLabel(summary_grid, text="Discount %:", font=ctk.CTkFont(size=10)).grid(row=1, column=0, padx=3, pady=1, sticky="w")
        self.discount_percent_input = ctk.CTkEntry(summary_grid, width=60, height=25)
        self.discount_percent_input.insert(0, "0")
        self.discount_percent_input.bind("<KeyRelease>", self.calculate_totals)
        self.discount_percent_input.grid(row=1, column=1, padx=3, pady=1)
        
        ctk.CTkLabel(summary_grid, text="Discount Amt:", font=ctk.CTkFont(size=10)).grid(row=2, column=0, padx=3, pady=1, sticky="w")
        self.discount_amount_label = ctk.CTkLabel(summary_grid, text="₹0.00", font=ctk.CTkFont(size=10))
        self.discount_amount_label.grid(row=2, column=1, padx=3, pady=1)
        
        ctk.CTkLabel(summary_grid, text="Round Off:", font=ctk.CTkFont(size=10)).grid(row=3, column=0, padx=3, pady=1, sticky="w")
        self.roundoff_input = ctk.CTkEntry(summary_grid, width=60, height=25)
        self.roundoff_input.insert(0, "0")
        self.roundoff_input.bind("<KeyRelease>", self.calculate_totals)
        self.roundoff_input.grid(row=3, column=1, padx=3, pady=1)
        
        ctk.CTkLabel(summary_grid, text="Total Amount:", font=ctk.CTkFont(size=10, weight="bold")).grid(row=4, column=0, padx=3, pady=1, sticky="w")
        self.total_amount_label = ctk.CTkLabel(summary_grid, text="₹0.00", font=ctk.CTkFont(size=11, weight="bold"))
        self.total_amount_label.grid(row=4, column=1, padx=3, pady=1)
        
        # Action Buttons in summary frame
        button_frame = ctk.CTkFrame(summary_frame)
        button_frame.pack(fill="x", padx=5, pady=10)
        
        ctk.CTkButton(button_frame, text="Save Order", command=self.save_order, height=28, width=90, font=ctk.CTkFont(size=10)).pack(pady=2)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=28, width=90, font=ctk.CTkFont(size=10)).pack(pady=2)
        
        self.load_suppliers()
        self.load_products()
        self.add_item_row()  # Add first row
    
    def generate_po_number(self):
        po_number = f"PO-{datetime.now().strftime('%d%m%Y%H%M%S%f')[:-3]}"
        self.po_number_input.delete(0, tk.END)
        self.po_number_input.insert(0, po_number)
        self.po_number_input.configure(state="readonly")
    
    def setup_view_tab(self):
        view_frame = self.tab_view.tab("View Orders")
        
        # Clear existing content
        for widget in view_frame.winfo_children():
            widget.destroy()
        
        # Initialize pagination
        self.current_page = 1
        self.page_size = 100
        
        # Header with pagination info
        header_frame = ctk.CTkFrame(view_frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Purchase Orders", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
        
        # Pagination controls
        pagination_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        pagination_frame.pack(side="right", padx=10, pady=10)
        
        self.prev_btn = ctk.CTkButton(pagination_frame, text="◀ Prev", command=self.prev_page, width=60, height=25)
        self.prev_btn.pack(side="left", padx=2)
        
        self.page_label = ctk.CTkLabel(pagination_frame, text="Page 1", font=ctk.CTkFont(size=10))
        self.page_label.pack(side="left", padx=5)
        
        self.next_btn = ctk.CTkButton(pagination_frame, text="Next ▶", command=self.next_page, width=60, height=25)
        self.next_btn.pack(side="left", padx=2)
        
        # Orders list with action buttons
        orders_frame = ctk.CTkScrollableFrame(view_frame)
        orders_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Header
        header_frame = ctk.CTkFrame(orders_frame, fg_color="#e0e0e0")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        headers = ["PO Number", "Supplier", "Date", "Total", "Status", "Actions"]
        widths = [150, 120, 100, 100, 80, 150]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=11, weight="bold"), 
                        text_color="#333333", width=width).grid(row=0, column=i, padx=2, pady=5)
        
        self.orders_list_frame = ctk.CTkFrame(orders_frame)
        self.orders_list_frame.pack(fill="x", padx=5, pady=5)
        
        # Refresh button
        ctk.CTkButton(view_frame, text="Refresh", command=self.load_orders, height=30).pack(pady=5)
        
        self.load_orders()
    
    def load_orders(self):
        # Clear existing orders
        for widget in self.orders_list_frame.winfo_children():
            widget.destroy()
        
        # Get paginated orders
        orders = self.purchase_order_service.get_all(page=self.current_page, page_size=self.page_size)
        total_count = self.purchase_order_service.get_total_count()
        total_pages = (total_count + self.page_size - 1) // self.page_size
        
        # Update pagination controls
        self.page_label.configure(text=f"Page {self.current_page} of {total_pages} ({total_count} orders)")
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < total_pages else "disabled")
        
        for i, order in enumerate(orders):
            row_frame = ctk.CTkFrame(self.orders_list_frame, height=22)
            row_frame.pack(fill="x", padx=1, pady=0)
            row_frame.pack_propagate(False)
            
            # Order details
            ctk.CTkLabel(row_frame, text=order.po_number, width=150, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=0, padx=1, pady=0)
            ctk.CTkLabel(row_frame, text=order.supplier_name, width=120, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=1, padx=1, pady=0)
            ctk.CTkLabel(row_frame, text=order.order_date.strftime('%Y-%m-%d') if order.order_date else '', width=100, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=2, padx=1, pady=0)
            ctk.CTkLabel(row_frame, text=f"₹{float(order.total_amount):.2f}", width=100, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=3, padx=1, pady=0)
            ctk.CTkLabel(row_frame, text=order.status, width=80, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=4, padx=1, pady=0)
            
            # Action icons - direct placement
            view_label = ctk.CTkLabel(row_frame, text="👁", font=ctk.CTkFont(size=14), cursor="hand2", width=30, height=20)
            view_label.grid(row=0, column=5, padx=2, pady=0)
            view_label.bind("<Button-1>", lambda e, oid=order.id: self.view_order(oid))
            
            print_label = ctk.CTkLabel(row_frame, text="🖨", font=ctk.CTkFont(size=14), cursor="hand2", width=30, height=20)
            print_label.grid(row=0, column=6, padx=2, pady=0)
            print_label.bind("<Button-1>", lambda e, oid=order.id: self.print_order(oid))
            
            # Reverse button - only show if not already reversed
            if order.status != 'reversed':
                reverse_label = ctk.CTkLabel(row_frame, text="↩", font=ctk.CTkFont(size=14), cursor="hand2", width=30, height=20)
                reverse_label.grid(row=0, column=7, padx=2, pady=0)
                reverse_label.bind("<Button-1>", lambda e, oid=order.id: self.reverse_order(oid))
    
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_orders()
    
    def next_page(self):
        total_count = self.purchase_order_service.get_total_count()
        total_pages = (total_count + self.page_size - 1) // self.page_size
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_orders()
    
    def view_order(self, order_id):
        # Clear current tab content and show order details
        view_frame = self.tab_view.tab("View Orders")
        for widget in view_frame.winfo_children():
            widget.destroy()
        
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import PurchaseOrder, PurchaseOrderItem, Product
        
        with db_manager.get_session() as session:
            order = session.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
            if not order:
                self.show_message("Order not found", "error")
                return
            
            # Header with back button
            header_frame = ctk.CTkFrame(view_frame)
            header_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(header_frame, text="Purchase Order Details", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
            ctk.CTkButton(header_frame, text="Back", command=self.setup_view_tab, width=80).pack(side="right", padx=10, pady=10)
            
            # Order info
            info_frame = ctk.CTkFrame(view_frame)
            info_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(info_frame, text=f"PO Number: {order.po_number}", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=2)
            ctk.CTkLabel(info_frame, text=f"Supplier: {order.supplier.name}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            ctk.CTkLabel(info_frame, text=f"Date: {order.order_date.strftime('%Y-%m-%d') if order.order_date else ''}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            
            # Items
            items_frame = ctk.CTkFrame(view_frame, height=200)
            items_frame.pack(fill="x", padx=10, pady=5)
            items_frame.pack_propagate(False)
            
            ctk.CTkLabel(items_frame, text="Order Items", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)
            
            # Items header
            items_header = ctk.CTkFrame(items_frame, fg_color="#e0e0e0")
            items_header.pack(fill="x", padx=5, pady=(5, 0))
            
            headers = ["Product", "Quantity", "Unit Price", "MRP", "Total"]
            widths = [150, 80, 100, 100, 100]
            for i, (header, width) in enumerate(zip(headers, widths)):
                ctk.CTkLabel(items_header, text=header, font=ctk.CTkFont(size=10, weight="bold"), width=width).grid(row=0, column=i, padx=2, pady=3, sticky="w")
            
            # Items list
            items_scroll = ctk.CTkScrollableFrame(items_frame, height=150)
            items_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            
            items = session.query(PurchaseOrderItem).join(Product).filter(PurchaseOrderItem.purchase_order_id == order_id).all()
            
            for item in items:
                item_frame = ctk.CTkFrame(items_scroll, height=22)
                item_frame.pack(fill="x", padx=2, pady=1)
                item_frame.pack_propagate(False)
                
                ctk.CTkLabel(item_frame, text=item.product.name, width=150, font=ctk.CTkFont(size=9)).grid(row=0, column=0, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=str(float(item.quantity)), width=80, font=ctk.CTkFont(size=9)).grid(row=0, column=1, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=f"₹{float(item.unit_price):.2f}", width=100, font=ctk.CTkFont(size=9)).grid(row=0, column=2, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=f"₹{float(item.mrp):.2f}", width=100, font=ctk.CTkFont(size=9)).grid(row=0, column=3, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=f"₹{float(item.total_amount):.2f}", width=100, font=ctk.CTkFont(size=9)).grid(row=0, column=4, padx=2, pady=1, sticky="w")
            
            # Summary
            summary_frame = ctk.CTkFrame(view_frame, height=80)
            summary_frame.pack(fill="x", padx=10, pady=5)
            summary_frame.pack_propagate(False)
            
            ctk.CTkLabel(summary_frame, text="Order Summary", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(5, 10))
            
            summary_grid = ctk.CTkFrame(summary_frame, fg_color="transparent")
            summary_grid.pack(side="right", padx=10, pady=5)
            
            if float(order.discount_amount) > 0:
                ctk.CTkLabel(summary_grid, text=f"Discount: {float(order.discount_percent):.1f}% (₹{float(order.discount_amount):.2f})", font=ctk.CTkFont(size=11)).pack(anchor="e")
            if float(order.roundoff) != 0:
                ctk.CTkLabel(summary_grid, text=f"Round Off: ₹{float(order.roundoff):.2f}", font=ctk.CTkFont(size=11)).pack(anchor="e")
            ctk.CTkLabel(summary_grid, text=f"Total Amount: ₹{float(order.total_amount):.2f}", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="e")
    
    def print_order(self, order_id):
        # Clear current tab content and show print view
        view_frame = self.tab_view.tab("View Orders")
        for widget in view_frame.winfo_children():
            widget.destroy()
        
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import PurchaseOrder, PurchaseOrderItem, Product
        
        with db_manager.get_session() as session:
            order = session.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
            if not order:
                self.show_message("Order not found", "error")
                return
            
            # Header with back button
            header_frame = ctk.CTkFrame(view_frame)
            header_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(header_frame, text="Print Purchase Order", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
            button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            button_frame.pack(side="right", padx=10, pady=10)
            ctk.CTkButton(button_frame, text="Print", command=lambda: self.show_message("Print functionality will be implemented"), width=70).pack(side="right", padx=5)
            ctk.CTkButton(button_frame, text="Back", command=self.setup_view_tab, width=70).pack(side="right", padx=5)
            
            # Print content with A4-like format
            content_frame = ctk.CTkScrollableFrame(view_frame)
            content_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Company header
            ctk.CTkLabel(content_frame, text="PURCHASE ORDER", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
            
            # Order details
            details_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            details_frame.pack(fill="x", pady=10)
            
            left_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            left_frame.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(left_frame, text=f"PO Number: {order.po_number}", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(left_frame, text=f"Date: {order.order_date.strftime('%d/%m/%Y') if order.order_date else ''}", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x")
            
            right_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            right_frame.pack(side="right", fill="x", expand=True)
            
            ctk.CTkLabel(right_frame, text=f"Supplier: {order.supplier.name}", font=ctk.CTkFont(size=11), anchor="e").pack(fill="x")
            
            # Items table
            table_frame = ctk.CTkFrame(content_frame)
            table_frame.pack(fill="x", pady=10)
            
            # Table header
            header_frame = ctk.CTkFrame(table_frame, fg_color="#e0e0e0")
            header_frame.pack(fill="x")
            
            headers = ["Item", "Qty", "Rate", "GST%", "Amount"]
            for i, header in enumerate(headers):
                ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=i, padx=10, pady=5, sticky="w")
            
            # Items
            items = session.query(PurchaseOrderItem).join(Product).filter(PurchaseOrderItem.purchase_order_id == order_id).all()
            
            for i, item in enumerate(items):
                item_frame = ctk.CTkFrame(table_frame, fg_color="white" if i % 2 == 0 else "#f9f9f9", height=25)
                item_frame.pack(fill="x")
                item_frame.pack_propagate(False)
                
                ctk.CTkLabel(item_frame, text=item.product.name, font=ctk.CTkFont(size=9)).grid(row=0, column=0, padx=10, pady=3, sticky="w")
                ctk.CTkLabel(item_frame, text=str(float(item.quantity)), font=ctk.CTkFont(size=9)).grid(row=0, column=1, padx=10, pady=3, sticky="w")
                ctk.CTkLabel(item_frame, text=f"₹{float(item.unit_price):.2f}", font=ctk.CTkFont(size=9)).grid(row=0, column=2, padx=10, pady=3, sticky="w")
                ctk.CTkLabel(item_frame, text=f"{float(item.gst_rate):.1f}%", font=ctk.CTkFont(size=9)).grid(row=0, column=3, padx=10, pady=3, sticky="w")
                ctk.CTkLabel(item_frame, text=f"₹{float(item.total_amount):.2f}", font=ctk.CTkFont(size=9)).grid(row=0, column=4, padx=10, pady=3, sticky="w")
            
            # Total section
            total_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            total_frame.pack(fill="x", pady=10)
            
            total_right = ctk.CTkFrame(total_frame, fg_color="transparent")
            total_right.pack(side="right")
            
            if float(order.discount_amount) > 0:
                ctk.CTkLabel(total_right, text=f"Discount ({float(order.discount_percent):.1f}%): ₹{float(order.discount_amount):.2f}", font=ctk.CTkFont(size=10), anchor="e").pack(fill="x")
            if float(order.roundoff) != 0:
                ctk.CTkLabel(total_right, text=f"Round Off: ₹{float(order.roundoff):.2f}", font=ctk.CTkFont(size=10), anchor="e").pack(fill="x")
            ctk.CTkLabel(total_right, text=f"Total Amount: ₹{float(order.total_amount):.2f}", font=ctk.CTkFont(size=12, weight="bold"), anchor="e").pack(fill="x")
    
    def reverse_order(self, order_id):
        """Show confirmation dialog and reverse order"""
        import tkinter.messagebox as msgbox
        import tkinter.simpledialog as simpledialog
        
        # Confirmation dialog with disclaimer
        result = msgbox.askyesno(
            "Reverse Purchase Order",
            "WARNING: This will reverse ALL transactions related to this purchase order including:\n\n"
            "• Stock transactions (items will be removed from inventory)\n"
            "• Accounting entries (Inventory and AP accounts will be reversed)\n\n"
            "This action cannot be undone. Are you sure you want to proceed?",
            icon="warning"
        )
        
        if result:
            # Ask for reason
            reason = simpledialog.askstring(
                "Reversal Reason",
                "Please enter the reason for reversing this order:"
            )
            
            if reason and reason.strip():
                try:
                    self.purchase_order_service.reverse_order(order_id, reason.strip())
                    self.show_message("Purchase order reversed successfully")
                    self.load_orders()  # Refresh the list
                except Exception as e:
                    self.show_message(f"Error reversing order: {str(e)}", "error")
            else:
                self.show_message("Reversal cancelled - reason is required", "warning")
    
    def load_suppliers(self):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Supplier
        from core.shared.utils.session_manager import session_manager
        
        with db_manager.get_session() as session:
            query = session.query(Supplier)
            tenant_id = session_manager.get_current_tenant_id()
            if tenant_id:
                query = query.filter(Supplier.tenant_id == tenant_id)
            suppliers = query.all()
            self.suppliers_dict = {sup.id: {'name': sup.name, 'tax_id': sup.tax_id or ''} for sup in suppliers}
            supplier_values = [f"{sup.id}:{sup.name}" for sup in suppliers]
            self.supplier_combo.configure_values(supplier_values)
    
    def on_supplier_select(self, value):
        if value and ':' in value:
            supplier_id = int(value.split(':')[0])
            supplier_info = self.suppliers_dict.get(supplier_id, {})
            self.supplier_name_label.configure(text=supplier_info.get('name', ''))
            self.tax_id_label.configure(text=supplier_info.get('tax_id', ''))
    
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
            self.product_values = [f"{prod.id}:{prod.name}" for prod in products]
    
    def add_item_row(self):
        row_frame = ctk.CTkFrame(self.items_scroll_frame, height=35)
        row_frame.pack(fill="x", padx=2, pady=1)
        row_frame.pack_propagate(False)
        
        # Searchable Product dropdown
        product_combo = SearchableDropdown(
            row_frame, 
            values=self.product_values, 
            width=120, 
            height=28,
            placeholder_text="Search product...",
            command=lambda v, r=row_frame: self.on_product_select(v, r)
        )
        product_combo.configure_values(self.product_values)  # Ensure values are set
        product_combo.grid(row=0, column=0, padx=1, pady=2)
        
        # Batch number entry (free text)
        batch_entry = ctk.CTkEntry(row_frame, width=80, font=ctk.CTkFont(size=9))
        batch_entry.grid(row=0, column=1, padx=1, pady=2)
        
        # Entry fields
        entries = {}
        fields = ["mrp", "price", "qty", "free_qty", "gst", "sgst", "cgst", "disc_percent", "disc_amount", "total"]
        widths = [70, 70, 50, 50, 50, 50, 50, 50, 70, 70]
        
        for i, (field, width) in enumerate(zip(fields, widths), 2):
            entry = ctk.CTkEntry(row_frame, width=width, font=ctk.CTkFont(size=9))
            entry.insert(0, "0")
            entry.grid(row=0, column=i, padx=1, pady=2)
            entries[field] = entry
            
            # Bind calculation events (exclude free_qty from calculations)
            if field in ["price", "qty", "gst", "disc_percent"]:
                entry.bind("<KeyRelease>", lambda e, r=row_frame: self.calculate_row_total(r))
        
        # Remove button
        remove_btn = ctk.CTkButton(row_frame, text="×", width=20, height=20, 
                                  command=lambda: self.remove_item_row(row_frame))
        remove_btn.grid(row=0, column=len(fields)+2, padx=1, pady=2)
        
        # Store references
        row_frame.product_combo = product_combo
        row_frame.batch_entry = batch_entry
        row_frame.entries = entries
        row_frame.remove_btn = remove_btn
        
        self.order_items.append(row_frame)
    
    def on_product_select(self, value, row_frame):
        if value and ':' in value:
            product_id = int(value.split(':')[0])
            # Auto-populate MRP and Price from product
            self.populate_product_prices(product_id, row_frame)
    
    def populate_product_prices(self, product_id, row_frame):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Product
        
        with db_manager.get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                mrp = float(product.price)
                purchase_price = mrp * 0.8  # 20% less than MRP
                
                # Update MRP field
                row_frame.entries["mrp"].delete(0, tk.END)
                row_frame.entries["mrp"].insert(0, f"{mrp:.2f}")
                
                # Update Price field
                row_frame.entries["price"].delete(0, tk.END)
                row_frame.entries["price"].insert(0, f"{purchase_price:.2f}")
                
                # Update GST field if available
                if product.gst_percentage:
                    row_frame.entries["gst"].delete(0, tk.END)
                    row_frame.entries["gst"].insert(0, f"{float(product.gst_percentage):.1f}")
                
                # Trigger calculation
                self.calculate_row_total(row_frame)
    
    def remove_item_row(self, row_frame):
        if len(self.order_items) > 1:  # Keep at least one row
            row_frame.destroy()
            self.order_items.remove(row_frame)
            self.calculate_totals()
    
    def calculate_row_total(self, row_frame):
        try:
            entries = row_frame.entries
            
            price = float(entries["price"].get() or 0)
            qty = float(entries["qty"].get() or 0)  # Only paid quantity for calculations
            # free_qty is not included in calculations
            gst_rate = float(entries["gst"].get() or 0)
            disc_percent = float(entries["disc_percent"].get() or 0)
            
            # Calculate base amount (only for paid quantity)
            base_amount = price * qty
            
            # Calculate discount
            disc_amount = base_amount * (disc_percent / 100)
            entries["disc_amount"].delete(0, tk.END)
            entries["disc_amount"].insert(0, f"{disc_amount:.2f}")
            
            # Amount after discount
            discounted_amount = base_amount - disc_amount
            
            # Calculate GST
            sgst = cgst = (discounted_amount * gst_rate / 100) / 2
            entries["sgst"].delete(0, tk.END)
            entries["sgst"].insert(0, f"{sgst:.2f}")
            entries["cgst"].delete(0, tk.END)
            entries["cgst"].insert(0, f"{cgst:.2f}")
            
            # Total amount (free quantity not included)
            total = discounted_amount + sgst + cgst
            entries["total"].delete(0, tk.END)
            entries["total"].insert(0, f"{total:.2f}")
            
            self.calculate_totals()
            
        except ValueError:
            pass
    
    def calculate_totals(self, event=None):
        try:
            subtotal = 0
            for row_frame in self.order_items:
                total = float(row_frame.entries["total"].get() or 0)
                subtotal += total
            
            # Update subtotal
            self.subtotal_label.configure(text=f"₹{subtotal:.2f}")
            
            # Calculate overall discount
            discount_percent = float(self.discount_percent_input.get() or 0)
            discount_amount = subtotal * (discount_percent / 100)
            self.discount_amount_label.configure(text=f"₹{discount_amount:.2f}")
            
            # Calculate final total
            roundoff = float(self.roundoff_input.get() or 0)
            final_total = subtotal - discount_amount + roundoff
            self.total_amount_label.configure(text=f"₹{final_total:.2f}")
            
        except ValueError:
            pass
    
    @ExceptionMiddleware.handle_exceptions("PurchaseOrderScreen")
    def save_order(self):
        if not self.supplier_combo.get():
            self.show_message("Please select supplier", "error")
            return
        
        try:
            # Collect order data
            supplier_id = int(self.supplier_combo.get().split(':')[0])
            
            order_data = {
                'po_number': self.po_number_input.get(),
                'supplier_id': supplier_id,
                'order_date': datetime.strptime(self.date_input.get(), '%Y-%m-%d'),
                'total_amount': float(self.total_amount_label.cget("text").replace('₹', '')),
                'discount_percent': float(self.discount_percent_input.get() or 0),
                'discount_amount': float(self.discount_amount_label.cget("text").replace('₹', '')),
                'roundoff': float(self.roundoff_input.get() or 0)
            }
            
            # Collect items data
            items_data = []
            for row_frame in self.order_items:
                if row_frame.product_combo.get():
                    product_id = int(row_frame.product_combo.get().split(':')[0])
                    item_data = {
                        'product_id': product_id,
                        'quantity': float(row_frame.entries["qty"].get() or 0),
                        'unit_price': float(row_frame.entries["price"].get() or 0),
                        'mrp': float(row_frame.entries["mrp"].get() or 0),
                        'gst_rate': float(row_frame.entries["gst"].get() or 0),
                        'discount_percent': float(row_frame.entries["disc_percent"].get() or 0),
                        'discount_amount': float(row_frame.entries["disc_amount"].get() or 0),
                        'total_amount': float(row_frame.entries["total"].get() or 0)
                    }
                    items_data.append(item_data)
            
            if not items_data:
                self.show_message("Please add at least one item", "error")
                return
            
            # Save order
            self.purchase_order_service.create_with_items(order_data, items_data)
            self.show_message("Purchase order saved successfully")
            self.load_orders()  # Refresh orders list
            self.clear_form()
            
        except Exception as e:
            self.show_message(f"Error saving order: {str(e)}", "error")
    
    def clear_form(self):
        # Generate new PO number
        self.po_number_input.configure(state="normal")
        self.generate_po_number()
        
        self.supplier_combo.clear()
        self.supplier_name_label.configure(text="")
        self.tax_id_label.configure(text="")
        self.date_input.delete(0, tk.END)
        self.date_input.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Clear all item rows
        for row_frame in self.order_items[:]:
            row_frame.destroy()
        self.order_items.clear()
        
        # Reset summary
        self.discount_percent_input.delete(0, tk.END)
        self.discount_percent_input.insert(0, "0")
        self.roundoff_input.delete(0, tk.END)
        self.roundoff_input.insert(0, "0")
        
        # Add first row
        self.add_item_row()
        self.calculate_totals()