import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.clinic_module.services.billing_service import BillingService
from modules.clinic_module.services.patient_service import PatientService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class BillingScreen(BaseScreen):
    def __init__(self, parent, clinic_module, **kwargs):
        self.clinic_module = clinic_module
        self.billing_service = BillingService()
        self.patient_service = PatientService()
        self.selected_invoice = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Healthcare Billing", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Form fields
        ctk.CTkLabel(form_frame, text="Patient:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.patient_var = ctk.StringVar()
        self.patient_dropdown = ctk.CTkComboBox(form_frame, variable=self.patient_var, width=200)
        self.patient_dropdown.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Consultation Fee:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.consultation_fee_input = ctk.CTkEntry(form_frame, width=150)
        self.consultation_fee_input.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Medication Amount:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.medication_amount_input = ctk.CTkEntry(form_frame, width=150)
        self.medication_amount_input.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Other Charges:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.other_charges_input = ctk.CTkEntry(form_frame, width=150)
        self.other_charges_input.grid(row=1, column=3, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create Invoice", command=self.save_invoice, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'invoice_number', 'title': 'Invoice #', 'width': 120},
            {'key': 'patient_name', 'title': 'Patient', 'width': 150},
            {'key': 'total_amount', 'title': 'Amount', 'width': 100},
            {'key': 'payment_status', 'title': 'Status', 'width': 100}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_invoice_select,
            on_delete=self.on_invoice_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_patients()
        self.load_invoices()
    
    def load_patients(self):
        patients = self.patient_service.get_all(tenant_id=1)
        patient_options = [f"{p.patient_number} - {p.first_name} {p.last_name}" for p in patients]
        self.patient_dropdown.configure(values=patient_options)
    
    @ExceptionMiddleware.handle_exceptions("BillingScreen")
    def load_invoices(self):
        from core.database.connection import db_manager
        from modules.clinic_module.models.entities import Invoice, Patient
        
        invoices_data = []
        
        with db_manager.get_session() as session:
            query = session.query(Invoice).join(Patient)
            query = query.filter(Invoice.tenant_id == 1, Invoice.payment_status == 'pending')
            invoices = query.all()
            
            for invoice in invoices:
                invoice_data = {
                    'id': invoice.id,
                    'invoice_number': invoice.invoice_number,
                    'patient_name': f"{invoice.patient.first_name} {invoice.patient.last_name}",
                    'total_amount': f"${invoice.total_amount}",
                    'payment_status': invoice.payment_status
                }
                invoices_data.append(invoice_data)
        
        self.data_grid.set_data(invoices_data)
    
    def on_invoice_select(self, invoice_data):
        self.selected_invoice = invoice_data
        # Load invoice details for editing
        from core.database.connection import db_manager
        from modules.clinic_module.models.entities import Invoice, InvoiceItem
        
        with db_manager.get_session() as session:
            invoice = session.query(Invoice).filter(Invoice.id == invoice_data['id']).first()
            if invoice:
                # Find patient in dropdown
                patient_text = f"{invoice.patient.patient_number} - {invoice.patient.first_name} {invoice.patient.last_name}"
                self.patient_var.set(patient_text)
                
                # Calculate amounts from invoice items
                medication_amount = 0
                other_charges = 0
                
                for item in invoice.invoice_items:
                    if item.item_type == 'medication':
                        medication_amount += float(item.total_price)
                    elif item.item_type == 'service':
                        other_charges += float(item.total_price)
                
                # Fill form fields
                self.consultation_fee_input.delete(0, tk.END)
                self.consultation_fee_input.insert(0, str(invoice.consultation_fee or 0))
                self.medication_amount_input.delete(0, tk.END)
                self.medication_amount_input.insert(0, str(medication_amount))
                self.other_charges_input.delete(0, tk.END)
                self.other_charges_input.insert(0, str(other_charges))
        
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("BillingScreen")
    def save_invoice(self):
        patient_text = self.patient_var.get()
        if not patient_text:
            self.show_message("Please select a patient", "error")
            return
        
        try:
            patient_number = patient_text.split(" - ")[0]
            patients = self.patient_service.get_all(tenant_id=1)
            patient = next((p for p in patients if p.patient_number == patient_number), None)
            
            if not patient:
                self.show_message("Patient not found", "error")
                return
            
            consultation_fee = float(self.consultation_fee_input.get() or 0)
            medication_amount = float(self.medication_amount_input.get() or 0)
            other_charges = float(self.other_charges_input.get() or 0)
            total_amount = consultation_fee + medication_amount + other_charges
            
            if total_amount <= 0:
                self.show_message("Please enter at least one charge amount", "error")
                return
            
            invoice_data = {
                'patient_id': patient.id,
                'consultation_fee': consultation_fee,
                'total_amount': total_amount,
                'final_amount': total_amount,
                'payment_method': 'cash',
                'tenant_id': 1
            }
            
            # Create invoice items
            items_data = []
            print(f"DEBUG: consultation_fee={consultation_fee}, medication_amount={medication_amount}, other_charges={other_charges}")
            
            if consultation_fee > 0:
                items_data.append({
                    'item_type': 'consultation',
                    'description': 'Medical Consultation',
                    'quantity': 1,
                    'unit_price': consultation_fee,
                    'total_price': consultation_fee
                })
            
            if medication_amount > 0:
                items_data.append({
                    'item_type': 'medication',
                    'description': 'Medications',
                    'quantity': 1,
                    'unit_price': medication_amount,
                    'total_price': medication_amount
                })
            
            if other_charges > 0:
                items_data.append({
                    'item_type': 'service',
                    'description': 'Other Charges',
                    'quantity': 1,
                    'unit_price': other_charges,
                    'total_price': other_charges
                })
            
            print(f"DEBUG: items_data = {items_data}")
            print(f"DEBUG: invoice_data = {invoice_data}")
            
            if self.selected_invoice:
                # For updates, also update invoice items
                from core.database.connection import db_manager
                from modules.clinic_module.models.entities import InvoiceItem
                
                with db_manager.get_session() as session:
                    # Delete existing items
                    session.query(InvoiceItem).filter(InvoiceItem.invoice_id == self.selected_invoice['id']).delete()
                    
                    # Add new items
                    for item_data in items_data:
                        item = InvoiceItem(
                            invoice_id=self.selected_invoice['id'],
                            item_type=item_data['item_type'],
                            product_id=item_data.get('product_id'),
                            description=item_data['description'],
                            quantity=item_data.get('quantity', 1),
                            unit_price=item_data['unit_price'],
                            total_price=item_data['total_price']
                        )
                        session.add(item)
                    session.commit()
                
                self.billing_service.update(self.selected_invoice['id'], invoice_data)
                self.show_message("Invoice updated successfully")
            else:
                self.billing_service.create_invoice(invoice_data, items_data)
                self.show_message("Invoice created successfully")
            
            self.clear_form()
            self.load_invoices()
        except Exception as e:
            self.show_message(f"Error creating invoice: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_invoice = None
        self.patient_var.set("")
        self.consultation_fee_input.delete(0, tk.END)
        self.medication_amount_input.delete(0, tk.END)
        self.other_charges_input.delete(0, tk.END)
        self.save_btn.configure(text="Create Invoice")
    @ExceptionMiddleware.handle_exceptions("BillingScreen")
    def on_invoice_delete(self, invoices_data):
        """Handle invoice deletion"""
        try:
            for invoice_data in invoices_data:
                self.billing_service.delete(invoice_data['id'])
            
            self.show_message(f"Successfully deleted {len(invoices_data)} invoice(s)")
            self.clear_form()
            self.load_invoices()
            return True
        except Exception as e:
            self.show_message(f"Error deleting invoices: {str(e)}", "error")
            return False