import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from core.shared.components.base_screen import BaseScreen
from core.shared.components.searchable_dropdown import SearchableDropdown
from modules.inventory_module.services.sales_order_service import SalesOrderService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class SalesOrderScreen(BaseScreen):
    def __init__(self, parent, inventory_module, **kwargs):
        self.inventory_module = inventory_module
        self.sales_order_service = SalesOrderService()
        self.selected_order = None
        self.order_items = []
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Sales Order", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
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
        ctk.CTkLabel(info_frame, text="SO Number:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.so_number_input = ctk.CTkEntry(info_frame, width=150)
        self.so_number_input.grid(row=0, column=1, padx=5, pady=5)
        self.generate_so_number()
        
        ctk.CTkLabel(info_frame, text="Phone:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.customer_input = SearchableDropdown(
            info_frame, 
            values=[], 
            width=200, 
            placeholder_text="Search phone...",
            command=self.on_customer_select,
            allow_add_new=True
        )
        self.customer_input.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(info_frame, text="Date:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.date_input = ctk.CTkEntry(info_frame, width=120, placeholder_text="YYYY-MM-DD")
        self.date_input.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.date_input.grid(row=0, column=5, padx=5, pady=5)
        
        self.selected_customer_id = None
        self.customers_dict = {}
        
        # Row 2 - Customer Info
        ctk.CTkLabel(info_frame, text="Customer ID:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.customer_id_entry = ctk.CTkEntry(info_frame, width=150, state="readonly")
        self.customer_id_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(info_frame, text="Customer Name:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.customer_name_entry = ctk.CTkEntry(info_frame, width=200)
        self.customer_name_entry.grid(row=1, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(info_frame, text="Email:").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        self.customer_email_entry = ctk.CTkEntry(info_frame, width=120)
        self.customer_email_entry.grid(row=1, column=5, padx=5, pady=5)
        
        # Row 3 - Tax ID
        ctk.CTkLabel(info_frame, text="Tax ID:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.customer_tax_id_entry = ctk.CTkEntry(info_frame, width=150)
        self.customer_tax_id_entry.grid(row=2, column=1, padx=5, pady=5)
        
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
        
        headers = ["Product", "Batch No", "MRP", "Qty", "Free Qty", "GST%", "SGST", "CGST", "Disc%", "DiscAmt", "Total"]
        widths = [120, 80, 70, 50, 50, 50, 50, 50, 50, 70, 70]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=9, weight="bold"), 
                        text_color="#333333", width=width).grid(row=0, column=i, padx=1, pady=5)
        
        # Scrollable items frame
        self.items_scroll_frame = ctk.CTkScrollableFrame(items_frame, height=120)
        self.items_scroll_frame.pack(fill="x", padx=5, pady=5)
        
        # Summary Frame (right side)
        summary_frame = ctk.CTkFrame(content_frame, width=200)
        summary_frame.pack(side="right", fill="y", padx=(5, 0))
        summary_frame.pack_propagate(False)
        
        ctk.CTkLabel(summary_frame, text="Order Summary", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(3, 5))
        
        # Summary fields
        summary_grid = ctk.CTkFrame(summary_frame)
        summary_grid.pack(fill="x", padx=3, pady=3)
        
        ctk.CTkLabel(summary_grid, text="Subtotal:", font=ctk.CTkFont(size=9)).grid(row=0, column=0, padx=2, pady=1, sticky="w")
        self.subtotal_label = ctk.CTkLabel(summary_grid, text="₹0.00", font=ctk.CTkFont(size=9, weight="bold"))
        self.subtotal_label.grid(row=0, column=1, padx=2, pady=1)
        
        ctk.CTkLabel(summary_grid, text="Discount %:", font=ctk.CTkFont(size=9)).grid(row=1, column=0, padx=2, pady=1, sticky="w")
        self.discount_percent_input = ctk.CTkEntry(summary_grid, width=50, height=20)
        self.discount_percent_input.insert(0, "0")
        self.discount_percent_input.bind("<KeyRelease>", self.calculate_totals)
        self.discount_percent_input.grid(row=1, column=1, padx=2, pady=1)
        
        ctk.CTkLabel(summary_grid, text="Discount Amt:", font=ctk.CTkFont(size=9)).grid(row=2, column=0, padx=2, pady=1, sticky="w")
        self.discount_amount_label = ctk.CTkLabel(summary_grid, text="₹0.00", font=ctk.CTkFont(size=9))
        self.discount_amount_label.grid(row=2, column=1, padx=2, pady=1)
        
        ctk.CTkLabel(summary_grid, text="Round Off:", font=ctk.CTkFont(size=9)).grid(row=3, column=0, padx=2, pady=1, sticky="w")
        self.roundoff_input = ctk.CTkEntry(summary_grid, width=50, height=20)
        self.roundoff_input.insert(0, "0")
        self.roundoff_input.bind("<KeyRelease>", self.calculate_totals)
        self.roundoff_input.grid(row=3, column=1, padx=2, pady=1)
        
        ctk.CTkLabel(summary_grid, text="Total Amount:", font=ctk.CTkFont(size=9, weight="bold")).grid(row=4, column=0, padx=2, pady=1, sticky="w")
        self.total_amount_label = ctk.CTkLabel(summary_grid, text="₹0.00", font=ctk.CTkFont(size=10, weight="bold"))
        self.total_amount_label.grid(row=4, column=1, padx=2, pady=1)
        
        # Action Buttons in summary frame
        button_frame = ctk.CTkFrame(summary_frame)
        button_frame.pack(fill="x", padx=3, pady=5)
        
        ctk.CTkButton(button_frame, text="Save Order", command=self.save_order, height=25, width=80, font=ctk.CTkFont(size=9)).pack(pady=1)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, width=80, font=ctk.CTkFont(size=9)).pack(pady=1)
        
        self.load_products()
        self.load_recent_customers()
        self.add_item_row()  # Add first row
    
    def generate_so_number(self):
        so_number = f"SO-{datetime.now().strftime('%d%m%Y%H%M%S%f')[:-3]}"
        self.so_number_input.delete(0, tk.END)
        self.so_number_input.insert(0, so_number)
        self.so_number_input.configure(state="readonly")
    
    def load_recent_customers(self):
        """Load last 10 customers by phone number"""
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Customer
        from core.shared.utils.session_manager import session_manager
        
        try:
            with db_manager.get_session() as session:
                query = session.query(Customer)
                
                tenant_id = session_manager.get_current_tenant_id()
                if tenant_id:
                    query = query.filter(Customer.tenant_id == tenant_id)
                
                # Get last 10 customers ordered by ID (most recent)
                customers = query.order_by(Customer.id.desc()).limit(10).all()
                
                # Build customers dictionary and phone list
                self.customers_dict = {}
                phone_list = []
                
                for customer in customers:
                    phone_display = f"{customer.phone} - {customer.name}"
                    phone_list.append(phone_display)
                    self.customers_dict[phone_display] = {
                        'id': customer.id,
                        'name': customer.name,
                        'phone': customer.phone,
                        'email': customer.email
                    }
                
                self.customer_input.configure_values(phone_list)
        except Exception as e:
            print(f"Load customers error: {e}")
    
    def on_customer_select(self, value):
        if value and value in self.customers_dict:
            customer_data = self.customers_dict[value]
            self.select_customer(customer_data)
        else:
            # Clear customer fields for new customer entry
            self.selected_customer_id = None
            self.customer_id_entry.configure(state="normal")
            self.customer_id_entry.delete(0, tk.END)
            self.customer_id_entry.configure(state="readonly")
            
            self.customer_name_entry.configure(state="normal")
            self.customer_name_entry.delete(0, tk.END)
            
            self.customer_email_entry.configure(state="normal")
            self.customer_email_entry.delete(0, tk.END)
            
            self.customer_tax_id_entry.configure(state="normal")
            self.customer_tax_id_entry.delete(0, tk.END)
    

    
    def select_customer(self, customer_data):
        self.selected_customer_id = customer_data['id']
        
        # Fill customer ID (readonly)
        self.customer_id_entry.configure(state="normal")
        self.customer_id_entry.delete(0, tk.END)
        self.customer_id_entry.insert(0, str(customer_data['id']))
        self.customer_id_entry.configure(state="readonly")
        
        # Fill customer details and make readonly
        self.customer_name_entry.delete(0, tk.END)
        self.customer_name_entry.insert(0, customer_data['name'])
        self.customer_name_entry.configure(state="readonly")
        
        self.customer_email_entry.delete(0, tk.END)
        self.customer_email_entry.insert(0, customer_data['email'] or "")
        self.customer_email_entry.configure(state="readonly")
        
        # Tax ID field (customers don't have tax_id in current model, so leave empty)
        self.customer_tax_id_entry.delete(0, tk.END)
        self.customer_tax_id_entry.configure(state="readonly")
    
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
        fields = ["mrp", "qty", "free_qty", "gst", "sgst", "cgst", "disc_percent", "disc_amount", "total"]
        widths = [70, 50, 50, 50, 50, 50, 50, 70, 70]
        
        for i, (field, width) in enumerate(zip(fields, widths), 2):
            entry = ctk.CTkEntry(row_frame, width=width, font=ctk.CTkFont(size=9))
            entry.insert(0, "0")
            entry.grid(row=0, column=i, padx=1, pady=2)
            entries[field] = entry
            
            # Bind calculation events (exclude free_qty from calculations)
            if field in ["mrp", "qty", "gst", "disc_percent"]:
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
            # Auto-populate MRP from product
            self.populate_product_prices(product_id, row_frame)
    
    def populate_product_prices(self, product_id, row_frame):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Product
        
        with db_manager.get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                mrp = float(product.price)
                
                # Update MRP field (use MRP as selling price)
                row_frame.entries["mrp"].delete(0, tk.END)
                row_frame.entries["mrp"].insert(0, f"{mrp:.2f}")
                
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
            
            mrp = float(entries["mrp"].get() or 0)
            qty = float(entries["qty"].get() or 0)  # Only paid quantity for calculations
            # free_qty is not included in calculations
            gst_rate = float(entries["gst"].get() or 0)
            disc_percent = float(entries["disc_percent"].get() or 0)
            
            # Calculate base amount (only for paid quantity)
            base_amount = mrp * qty
            
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
                if hasattr(row_frame, 'entries') and 'total' in row_frame.entries:
                    total_value = row_frame.entries["total"].get()
                    if total_value:
                        subtotal += float(total_value)
            
            # Update subtotal
            self.subtotal_label.configure(text=f"₹{subtotal:.2f}")
            
            # Calculate overall discount
            discount_value = self.discount_percent_input.get()
            discount_percent = float(discount_value) if discount_value else 0
            discount_amount = subtotal * (discount_percent / 100)
            self.discount_amount_label.configure(text=f"₹{discount_amount:.2f}")
            
            # Calculate final total
            roundoff_value = self.roundoff_input.get()
            roundoff = float(roundoff_value) if roundoff_value else 0
            final_total = subtotal - discount_amount + roundoff
            self.total_amount_label.configure(text=f"₹{final_total:.2f}")
            
        except (ValueError, AttributeError):
            pass
    
    @ExceptionMiddleware.handle_exceptions("SalesOrderScreen")
    def save_order(self):
        # Handle new customer creation if not selected from dropdown
        if not self.selected_customer_id:
            customer_phone = self.customer_input.get().strip()
            # Extract phone number if it's in "phone - name" format
            if ' - ' in customer_phone:
                customer_phone = customer_phone.split(' - ')[0]
            
            customer_name = self.customer_name_entry.get().strip() or "Customer"
            customer_email = self.customer_email_entry.get().strip()
            
            if not customer_phone:
                self.show_message("Please enter customer phone number or select existing customer", "error")
                return
            
            # Search for existing customer by phone
            try:
                from core.database.connection import db_manager
                from modules.inventory_module.models.entities import Customer
                from core.shared.utils.session_manager import session_manager
                
                with db_manager.get_session() as session:
                    existing_customer = session.query(Customer).filter(
                        Customer.phone == customer_phone,
                        Customer.tenant_id == session_manager.get_current_tenant_id()
                    ).first()
                    
                    if existing_customer:
                        self.selected_customer_id = existing_customer.id
                        return
            except Exception:
                pass  # Continue with new customer creation
            
            # Create new customer
            try:
                from core.database.connection import db_manager
                from modules.inventory_module.models.entities import Customer
                from core.shared.utils.session_manager import session_manager
                
                with db_manager.get_session() as session:
                    new_customer = Customer(
                        name=customer_name,
                        phone=customer_phone,
                        email=customer_email if customer_email else None,
                        tenant_id=session_manager.get_current_tenant_id(),
                        created_by=session_manager.get_current_username()
                    )
                    session.add(new_customer)
                    session.flush()
                    self.selected_customer_id = new_customer.id
                    session.commit()
                    # Refresh customer list
                    self.load_recent_customers()
            except Exception as e:
                self.show_message(f"Error creating customer: {str(e)}", "error")
                return
        
        try:
            # Collect order data
            order_data = {
                'order_number': self.so_number_input.get(),
                'customer_id': self.selected_customer_id,
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
                        'batch_number': row_frame.batch_entry.get(),
                        'quantity': float(row_frame.entries["qty"].get() or 0),
                        'free_quantity': float(row_frame.entries["free_qty"].get() or 0),
                        'unit_price': float(row_frame.entries["mrp"].get() or 0),
                        'gst_rate': float(row_frame.entries["gst"].get() or 0),
                        'discount_percent': float(row_frame.entries["disc_percent"].get() or 0),
                        'discount_amount': float(row_frame.entries["disc_amount"].get() or 0),
                        'total_price': float(row_frame.entries["total"].get() or 0)
                    }
                    items_data.append(item_data)
            
            if not items_data:
                self.show_message("Please add at least one item", "error")
                return
            
            # Save order
            self.sales_order_service.create_with_items(order_data, items_data)
            self.show_message("Sales order saved successfully")
            self.load_orders()  # Refresh orders list
            self.clear_form()
            
        except Exception as e:
            self.show_message(f"Error saving order: {str(e)}", "error")
    
    def clear_form(self):
        # Generate new SO number
        self.so_number_input.configure(state="normal")
        self.generate_so_number()
        
        self.customer_input.clear()
        self.selected_customer_id = None
        
        # Clear customer ID
        self.customer_id_entry.configure(state="normal")
        self.customer_id_entry.delete(0, tk.END)
        self.customer_id_entry.configure(state="readonly")
        
        # Clear and enable customer fields for new customer
        self.customer_name_entry.configure(state="normal")
        self.customer_name_entry.delete(0, tk.END)
        self.customer_email_entry.configure(state="normal")
        self.customer_email_entry.delete(0, tk.END)
        self.customer_tax_id_entry.configure(state="normal")
        self.customer_tax_id_entry.delete(0, tk.END)
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
        
        ctk.CTkLabel(header_frame, text="Sales Orders", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
        
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
        
        headers = ["SO Number", "Customer", "Date", "Total", "Status", "Actions"]
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
        orders = self.sales_order_service.get_all(page=self.current_page, page_size=self.page_size)
        total_count = self.sales_order_service.get_total_count()
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
            ctk.CTkLabel(row_frame, text=order.order_number, width=150, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=0, padx=1, pady=0)
            ctk.CTkLabel(row_frame, text=order.customer_name, width=120, font=ctk.CTkFont(size=9), height=20).grid(row=0, column=1, padx=1, pady=0)
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
        total_count = self.sales_order_service.get_total_count()
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
        from modules.inventory_module.models.entities import SalesOrder, SalesOrderItem, Product
        
        with db_manager.get_session() as session:
            order = session.query(SalesOrder).filter(SalesOrder.id == order_id).first()
            if not order:
                self.show_message("Order not found", "error")
                return
            
            # Header with back button
            header_frame = ctk.CTkFrame(view_frame)
            header_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(header_frame, text="Sales Order Details", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
            ctk.CTkButton(header_frame, text="Back", command=self.setup_view_tab, width=80).pack(side="right", padx=10, pady=10)
            
            # Order info
            info_frame = ctk.CTkFrame(view_frame)
            info_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(info_frame, text=f"SO Number: {order.order_number}", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=2)
            ctk.CTkLabel(info_frame, text=f"Customer: {order.customer.name}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            if order.customer.phone:
                ctk.CTkLabel(info_frame, text=f"Phone: {order.customer.phone}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            ctk.CTkLabel(info_frame, text=f"Date: {order.order_date.strftime('%Y-%m-%d') if order.order_date else ''}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            
            # Items
            items_frame = ctk.CTkFrame(view_frame, height=200)
            items_frame.pack(fill="x", padx=10, pady=5)
            items_frame.pack_propagate(False)
            
            ctk.CTkLabel(items_frame, text="Order Items", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)
            
            # Items header
            items_header = ctk.CTkFrame(items_frame, fg_color="#e0e0e0")
            items_header.pack(fill="x", padx=5, pady=(5, 0))
            
            headers = ["Product", "Quantity", "Free Qty", "Unit Price", "Total"]
            widths = [150, 80, 80, 100, 100]
            for i, (header, width) in enumerate(zip(headers, widths)):
                ctk.CTkLabel(items_header, text=header, font=ctk.CTkFont(size=10, weight="bold"), width=width).grid(row=0, column=i, padx=2, pady=3, sticky="w")
            
            # Items list
            items_scroll = ctk.CTkScrollableFrame(items_frame, height=150)
            items_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            
            items = session.query(SalesOrderItem).join(Product).filter(SalesOrderItem.sales_order_id == order_id).all()
            
            for item in items:
                item_frame = ctk.CTkFrame(items_scroll, height=22)
                item_frame.pack(fill="x", padx=2, pady=1)
                item_frame.pack_propagate(False)
                
                ctk.CTkLabel(item_frame, text=item.product.name, width=150, font=ctk.CTkFont(size=9)).grid(row=0, column=0, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=str(float(item.quantity)), width=80, font=ctk.CTkFont(size=9)).grid(row=0, column=1, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=str(float(getattr(item, 'free_quantity', 0))), width=80, font=ctk.CTkFont(size=9)).grid(row=0, column=2, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=f"₹{float(item.unit_price):.2f}", width=100, font=ctk.CTkFont(size=9)).grid(row=0, column=3, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=f"₹{float(item.total_price):.2f}", width=100, font=ctk.CTkFont(size=9)).grid(row=0, column=4, padx=2, pady=1, sticky="w")
            
            # Summary
            summary_frame = ctk.CTkFrame(view_frame, height=80)
            summary_frame.pack(fill="x", padx=10, pady=5)
            summary_frame.pack_propagate(False)
            
            ctk.CTkLabel(summary_frame, text="Order Summary", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(5, 10))
            
            summary_grid = ctk.CTkFrame(summary_frame, fg_color="transparent")
            summary_grid.pack(side="right", padx=10, pady=5)
            
            if hasattr(order, 'discount_amount') and float(order.discount_amount) > 0:
                ctk.CTkLabel(summary_grid, text=f"Discount: {float(order.discount_percent):.1f}% (₹{float(order.discount_amount):.2f})", font=ctk.CTkFont(size=11)).pack(anchor="e")
            if hasattr(order, 'roundoff') and float(order.roundoff) != 0:
                ctk.CTkLabel(summary_grid, text=f"Round Off: ₹{float(order.roundoff):.2f}", font=ctk.CTkFont(size=11)).pack(anchor="e")
            ctk.CTkLabel(summary_grid, text=f"Total Amount: ₹{float(order.total_amount):.2f}", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="e")
    
    def print_order(self, order_id):
        # Clear current tab content and show print view
        view_frame = self.tab_view.tab("View Orders")
        for widget in view_frame.winfo_children():
            widget.destroy()
        
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import SalesOrder, SalesOrderItem, Product
        
        with db_manager.get_session() as session:
            order = session.query(SalesOrder).filter(SalesOrder.id == order_id).first()
            if not order:
                self.show_message("Order not found", "error")
                return
            
            # Header with back button
            header_frame = ctk.CTkFrame(view_frame)
            header_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(header_frame, text="Print Sales Order", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
            button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            button_frame.pack(side="right", padx=10, pady=10)
            ctk.CTkButton(button_frame, text="Print", command=lambda: self.show_message("Print functionality will be implemented"), width=70).pack(side="right", padx=5)
            ctk.CTkButton(button_frame, text="Back", command=self.setup_view_tab, width=70).pack(side="right", padx=5)
            
            # Print content with A4-like format
            content_frame = ctk.CTkScrollableFrame(view_frame)
            content_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Company header
            ctk.CTkLabel(content_frame, text="SALES ORDER", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
            
            # Order details
            details_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            details_frame.pack(fill="x", pady=10)
            
            left_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            left_frame.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(left_frame, text=f"SO Number: {order.order_number}", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(left_frame, text=f"Date: {order.order_date.strftime('%d/%m/%Y') if order.order_date else ''}", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x")
            
            right_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            right_frame.pack(side="right", fill="x", expand=True)
            
            ctk.CTkLabel(right_frame, text=f"Customer: {order.customer.name}", font=ctk.CTkFont(size=11), anchor="e").pack(fill="x")
            ctk.CTkLabel(right_frame, text=f"Phone: {order.customer.phone}", font=ctk.CTkFont(size=11), anchor="e").pack(fill="x")
            
            # Items table
            table_frame = ctk.CTkFrame(content_frame)
            table_frame.pack(fill="x", pady=10)
            
            # Table header
            header_frame = ctk.CTkFrame(table_frame, fg_color="#e0e0e0")
            header_frame.pack(fill="x")
            
            headers = ["Item", "Qty", "Free", "Rate", "Amount"]
            for i, header in enumerate(headers):
                ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=i, padx=10, pady=5, sticky="w")
            
            # Items
            items = session.query(SalesOrderItem).join(Product).filter(SalesOrderItem.sales_order_id == order_id).all()
            
            for i, item in enumerate(items):
                item_frame = ctk.CTkFrame(table_frame, fg_color="white" if i % 2 == 0 else "#f9f9f9", height=25)
                item_frame.pack(fill="x")
                item_frame.pack_propagate(False)
                
                ctk.CTkLabel(item_frame, text=item.product.name, font=ctk.CTkFont(size=9)).grid(row=0, column=0, padx=10, pady=3, sticky="w")
                ctk.CTkLabel(item_frame, text=str(float(item.quantity)), font=ctk.CTkFont(size=9)).grid(row=0, column=1, padx=10, pady=3, sticky="w")
                ctk.CTkLabel(item_frame, text=str(float(getattr(item, 'free_quantity', 0))), font=ctk.CTkFont(size=9)).grid(row=0, column=2, padx=10, pady=3, sticky="w")
                ctk.CTkLabel(item_frame, text=f"₹{float(item.unit_price):.2f}", font=ctk.CTkFont(size=9)).grid(row=0, column=3, padx=10, pady=3, sticky="w")
                ctk.CTkLabel(item_frame, text=f"₹{float(item.total_price):.2f}", font=ctk.CTkFont(size=9)).grid(row=0, column=4, padx=10, pady=3, sticky="w")
            
            # Total section
            total_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            total_frame.pack(fill="x", pady=10)
            
            total_right = ctk.CTkFrame(total_frame, fg_color="transparent")
            total_right.pack(side="right")
            
            ctk.CTkLabel(total_right, text=f"Total Amount: ₹{float(order.total_amount):.2f}", font=ctk.CTkFont(size=12, weight="bold"), anchor="e").pack(fill="x")
    
    def reverse_order(self, order_id):
        """Show confirmation dialog and reverse order"""
        import tkinter.messagebox as msgbox
        import tkinter.simpledialog as simpledialog
        
        # Confirmation dialog with disclaimer
        result = msgbox.askyesno(
            "Reverse Sales Order",
            "WARNING: This will reverse ALL transactions related to this sales order including:\n\n"
            "• Stock transactions (items will be added back to inventory)\n"
            "• Accounting entries (AR and Sales accounts will be reversed)\n\n"
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
                    self.sales_order_service.reverse_order(order_id, reason.strip())
                    self.show_message("Sales order reversed successfully")
                    self.load_orders()  # Refresh the list
                except Exception as e:
                    self.show_message(f"Error reversing order: {str(e)}", "error")
            else:
                self.show_message("Reversal cancelled - reason is required", "warning")