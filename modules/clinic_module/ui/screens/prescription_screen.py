import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from core.shared.components.base_screen import BaseScreen
from modules.clinic_module.services.prescription_service import PrescriptionService
from modules.clinic_module.services.patient_service import PatientService
from modules.clinic_module.services.doctor_service import DoctorService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class PrescriptionScreen(BaseScreen):
    def __init__(self, parent, clinic_module, **kwargs):
        self.clinic_module = clinic_module
        self.prescription_service = PrescriptionService()
        self.patient_service = PatientService()
        self.doctor_service = DoctorService()
        self.selected_prescription = None
        self.prescription_items = []
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Prescription Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Tab view
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create tabs
        self.tab_view.add("Create Prescription")
        self.tab_view.add("View Prescriptions")
        
        self.setup_create_tab()
        self.setup_view_tab()
    
    def setup_create_tab(self):
        create_frame = self.tab_view.tab("Create Prescription")
        
        # Prescription Info Frame
        info_frame = ctk.CTkFrame(create_frame)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        # Row 1
        ctk.CTkLabel(info_frame, text="RX Number:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.rx_number_input = ctk.CTkEntry(info_frame, width=150)
        self.rx_number_input.grid(row=0, column=1, padx=5, pady=5)
        self.generate_rx_number()
        
        ctk.CTkLabel(info_frame, text="Patient:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.patient_var = ctk.StringVar()
        self.patient_dropdown = ctk.CTkComboBox(info_frame, variable=self.patient_var, width=200)
        self.patient_dropdown.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(info_frame, text="Date:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.date_input = ctk.CTkEntry(info_frame, width=120, placeholder_text="YYYY-MM-DD")
        self.date_input.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.date_input.grid(row=0, column=5, padx=5, pady=5)
        
        # Row 2
        ctk.CTkLabel(info_frame, text="Doctor:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.doctor_var = ctk.StringVar()
        self.doctor_dropdown = ctk.CTkComboBox(info_frame, variable=self.doctor_var, width=200)
        self.doctor_dropdown.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        
        ctk.CTkLabel(info_frame, text="Instructions:").grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.instructions_input = ctk.CTkEntry(info_frame, width=300)
        self.instructions_input.grid(row=1, column=4, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Main content frame with items and summary side by side
        content_frame = ctk.CTkFrame(create_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Items Frame (full width)
        items_frame = ctk.CTkFrame(content_frame)
        items_frame.pack(fill="both", expand=True)
        
        # Items header with Add button
        items_header = ctk.CTkFrame(items_frame)
        items_header.pack(fill="x", pady=5)
        
        ctk.CTkLabel(items_header, text="Prescription Items", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10)
        ctk.CTkButton(items_header, text="+ Add Item", command=self.add_item_row, height=25, width=80).pack(side="right", padx=10)
        
        # Items Grid Header
        header_frame = ctk.CTkFrame(items_frame, fg_color="#e0e0e0")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        headers = ["Type", "Medicine/Test", "Dosage", "Frequency", "Duration", "Notes"]
        widths = [80, 150, 100, 100, 100, 150]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(header_frame, text=header, font=ctk.CTkFont(size=9, weight="bold"), 
                        text_color="#333333", width=width).grid(row=0, column=i, padx=1, pady=5)
        
        # Scrollable items frame
        self.items_scroll_frame = ctk.CTkScrollableFrame(items_frame, height=200)
        self.items_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Action Buttons
        button_frame = ctk.CTkFrame(create_frame)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Save Prescription", command=self.save_prescription, height=30, width=150)
        self.save_btn.pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=30, width=100).pack(side="left", padx=5)
        
        self.load_dropdowns()
        self.add_item_row()  # Add first row
    
    def generate_rx_number(self):
        rx_number = f"RX-{datetime.now().strftime('%d%m%Y%H%M%S%f')[:-3]}"
        self.rx_number_input.delete(0, tk.END)
        self.rx_number_input.insert(0, rx_number)
        self.rx_number_input.configure(state="readonly")
    
    def load_dropdowns(self):
        # Load patients
        patients = self.patient_service.get_all(tenant_id=1)
        patient_options = [f"{p.patient_number} - {p.first_name} {p.last_name}" for p in patients]
        self.patient_dropdown.configure(values=patient_options)
        
        # Load doctors
        doctors = self.doctor_service.get_all(tenant_id=1)
        doctor_options = [f"{d.employee_id} - Dr. {d.first_name} {d.last_name}" for d in doctors]
        self.doctor_dropdown.configure(values=doctor_options)
    
    def add_item_row(self):
        row_frame = ctk.CTkFrame(self.items_scroll_frame, height=35)
        row_frame.pack(fill="x", padx=2, pady=1)
        row_frame.pack_propagate(False)
        
        # Type dropdown
        type_var = ctk.StringVar(value="medicine")
        type_combo = ctk.CTkComboBox(row_frame, variable=type_var, values=["medicine", "test"], width=80, command=lambda v, r=row_frame: self.on_item_type_change(v, r))
        type_combo.grid(row=0, column=0, padx=1, pady=2)
        
        # Item dropdown
        item_var = ctk.StringVar()
        item_combo = ctk.CTkComboBox(row_frame, variable=item_var, width=150)
        item_combo.grid(row=0, column=1, padx=1, pady=2)
        
        # Entry fields
        dosage_entry = ctk.CTkEntry(row_frame, width=100, font=ctk.CTkFont(size=9))
        dosage_entry.grid(row=0, column=2, padx=1, pady=2)
        
        frequency_entry = ctk.CTkEntry(row_frame, width=100, font=ctk.CTkFont(size=9))
        frequency_entry.grid(row=0, column=3, padx=1, pady=2)
        
        duration_entry = ctk.CTkEntry(row_frame, width=100, font=ctk.CTkFont(size=9))
        duration_entry.grid(row=0, column=4, padx=1, pady=2)
        
        notes_entry = ctk.CTkEntry(row_frame, width=150, font=ctk.CTkFont(size=9))
        notes_entry.grid(row=0, column=5, padx=1, pady=2)
        
        # Remove button
        remove_btn = ctk.CTkButton(row_frame, text="×", width=20, height=20, 
                                  command=lambda: self.remove_item_row(row_frame))
        remove_btn.grid(row=0, column=6, padx=1, pady=2)
        
        # Store references
        row_frame.type_combo = type_combo
        row_frame.item_combo = item_combo
        row_frame.dosage_entry = dosage_entry
        row_frame.frequency_entry = frequency_entry
        row_frame.duration_entry = duration_entry
        row_frame.notes_entry = notes_entry
        row_frame.remove_btn = remove_btn
        
        self.prescription_items.append(row_frame)
        self.load_items_for_type("medicine", row_frame)
    
    def on_item_type_change(self, value, row_frame):
        self.load_items_for_type(value, row_frame)
    
    def load_items_for_type(self, item_type, row_frame):
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Product, Category
        from sqlalchemy import or_
        
        options = []
        with db_manager.get_session() as session:
            category_name = 'Medicine' if item_type == 'medicine' else 'Test'
            parent_alias = session.query(Category).filter(Category.name == category_name).subquery()
            
            query = session.query(Product).join(Category)
            query = query.filter(
                or_(
                    Category.name == category_name,
                    Category.parent_id.in_(session.query(parent_alias.c.id))
                )
            )
            query = query.filter(Product.tenant_id == 1)
            
            products = query.all()
            options = [f"{p.code} - {p.name}" for p in products]
        
        row_frame.item_combo.configure(values=options)
        row_frame.item_combo.set("")
    
    def remove_item_row(self, row_frame):
        if len(self.prescription_items) > 1:
            row_frame.destroy()
            self.prescription_items.remove(row_frame)
    

    
    @ExceptionMiddleware.handle_exceptions("PrescriptionScreen")
    def save_prescription(self):
        if not all([self.patient_var.get(), self.doctor_var.get()]):
            self.show_message("Please select patient and doctor", "error")
            return
        
        # Check if at least one item has content
        has_items = any(item.item_combo.get() for item in self.prescription_items)
        if not has_items:
            self.show_message("Please add at least one medicine or test", "error")
            return
        
        try:
            # Get patient and doctor IDs
            patient_text = self.patient_var.get()
            patient_number = patient_text.split(" - ")[0]
            patients = self.patient_service.get_all(tenant_id=1)
            patient = next((p for p in patients if p.patient_number == patient_number), None)
            
            doctor_text = self.doctor_var.get()
            doctor_id = doctor_text.split(" - ")[0]
            doctors = self.doctor_service.get_all(tenant_id=1)
            doctor = next((d for d in doctors if d.employee_id == doctor_id), None)
            
            if not all([patient, doctor]):
                self.show_message("Invalid patient or doctor selection", "error")
                return
            
            prescription_data = {
                'patient_id': patient.id,
                'doctor_id': doctor.id,
                'instructions': self.instructions_input.get(),
                'tenant_id': 1
            }
            
            # Convert prescription items to database format
            items_data = []
            from modules.inventory_module.models.entities import Product
            from core.database.connection import db_manager
            
            with db_manager.get_session() as session:
                for item in self.prescription_items:
                    if item.item_combo.get():
                        item_code = item.item_combo.get().split(" - ")[0]
                        product = session.query(Product).filter(Product.code == item_code, Product.tenant_id == 1).first()
                        
                        if product:
                            items_data.append({
                                'product_id': product.id,
                                'dosage': item.dosage_entry.get(),
                                'frequency': item.frequency_entry.get(),
                                'duration': item.duration_entry.get(),
                                'instructions': f"{item.type_combo.get().title()}: {item.notes_entry.get()}"
                            })
            
            if not items_data:
                self.show_message("No valid items found", "error")
                return
            
            self.prescription_service.create(prescription_data, items_data)
            self.show_message("Prescription created successfully")
            self.load_prescriptions()
            self.clear_form()
            
        except Exception as e:
            self.show_message(f"Error creating prescription: {str(e)}", "error")
    
    def clear_form(self):
        # Generate new RX number
        self.rx_number_input.configure(state="normal")
        self.generate_rx_number()
        
        self.patient_var.set("")
        self.doctor_var.set("")
        self.instructions_input.delete(0, tk.END)
        self.date_input.delete(0, tk.END)
        self.date_input.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Clear all item rows
        for row_frame in self.prescription_items[:]:
            row_frame.destroy()
        self.prescription_items.clear()
        
        # Add first row
        self.add_item_row()
    
    def setup_view_tab(self):
        view_frame = self.tab_view.tab("View Prescriptions")
        
        # Header
        header_frame = ctk.CTkFrame(view_frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Prescriptions", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
        
        # Prescriptions list
        prescriptions_frame = ctk.CTkScrollableFrame(view_frame)
        prescriptions_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Header
        list_header_frame = ctk.CTkFrame(prescriptions_frame, fg_color="#e0e0e0")
        list_header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        headers = ["RX Number", "Patient", "Doctor", "Date", "Actions"]
        widths = [120, 150, 150, 100, 100]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(list_header_frame, text=header, font=ctk.CTkFont(size=11, weight="bold"), 
                        text_color="#333333", width=width).grid(row=0, column=i, padx=2, pady=5)
        
        self.prescriptions_list_frame = ctk.CTkFrame(prescriptions_frame)
        self.prescriptions_list_frame.pack(fill="x", padx=5, pady=5)
        
        # Refresh button
        ctk.CTkButton(view_frame, text="Refresh", command=self.load_prescriptions, height=30).pack(pady=5)
        
        self.load_prescriptions()
    
    @ExceptionMiddleware.handle_exceptions("PrescriptionScreen")
    def load_prescriptions(self):
        # Clear existing prescriptions
        for widget in self.prescriptions_list_frame.winfo_children():
            widget.destroy()
        
        from core.database.connection import db_manager
        from modules.clinic_module.models.entities import Prescription, Patient, Doctor
        
        with db_manager.get_session() as session:
            query = session.query(Prescription).join(Patient).join(Doctor)
            query = query.filter(Prescription.tenant_id == 1)
            prescriptions = query.all()
            
            for i, prescription in enumerate(prescriptions):
                row_frame = ctk.CTkFrame(self.prescriptions_list_frame, height=30)
                row_frame.pack(fill="x", padx=1, pady=1)
                row_frame.pack_propagate(False)
                
                # Prescription details
                ctk.CTkLabel(row_frame, text=prescription.prescription_number, width=120, font=ctk.CTkFont(size=9)).grid(row=0, column=0, padx=2, pady=2)
                ctk.CTkLabel(row_frame, text=f"{prescription.patient.first_name} {prescription.patient.last_name}", width=150, font=ctk.CTkFont(size=9)).grid(row=0, column=1, padx=2, pady=2)
                ctk.CTkLabel(row_frame, text=f"Dr. {prescription.doctor.first_name} {prescription.doctor.last_name}", width=150, font=ctk.CTkFont(size=9)).grid(row=0, column=2, padx=2, pady=2)
                ctk.CTkLabel(row_frame, text=prescription.prescription_date.strftime('%Y-%m-%d'), width=100, font=ctk.CTkFont(size=9)).grid(row=0, column=3, padx=2, pady=2)
                
                # Action buttons
                view_btn = ctk.CTkLabel(row_frame, text="👁", font=ctk.CTkFont(size=14), cursor="hand2", width=30)
                view_btn.grid(row=0, column=4, padx=5, pady=2)
                view_btn.bind("<Button-1>", lambda e, pid=prescription.id: self.view_prescription(pid))
                
                print_btn = ctk.CTkLabel(row_frame, text="🖨", font=ctk.CTkFont(size=14), cursor="hand2", width=30)
                print_btn.grid(row=0, column=5, padx=5, pady=2)
                print_btn.bind("<Button-1>", lambda e, pid=prescription.id: self.print_prescription(pid))
    
    def view_prescription(self, prescription_id):
        # Clear current tab content and show prescription details
        view_frame = self.tab_view.tab("View Prescriptions")
        for widget in view_frame.winfo_children():
            widget.destroy()
        
        from core.database.connection import db_manager
        from modules.clinic_module.models.entities import Prescription, PrescriptionItem, Patient, Doctor
        from modules.inventory_module.models.entities import Product
        
        with db_manager.get_session() as session:
            prescription = session.query(Prescription).filter(Prescription.id == prescription_id).first()
            if not prescription:
                self.show_message("Prescription not found", "error")
                return
            
            # Header with back button
            header_frame = ctk.CTkFrame(view_frame)
            header_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(header_frame, text="Prescription Details", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
            ctk.CTkButton(header_frame, text="Back", command=lambda: self.return_to_prescriptions_list(), width=80).pack(side="right", padx=10, pady=10)
            
            # Prescription info
            info_frame = ctk.CTkFrame(view_frame)
            info_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(info_frame, text=f"RX Number: {prescription.prescription_number}", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=2)
            ctk.CTkLabel(info_frame, text=f"Patient: {prescription.patient.first_name} {prescription.patient.last_name}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            ctk.CTkLabel(info_frame, text=f"Doctor: Dr. {prescription.doctor.first_name} {prescription.doctor.last_name}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            ctk.CTkLabel(info_frame, text=f"Date: {prescription.prescription_date.strftime('%Y-%m-%d')}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            if prescription.instructions:
                ctk.CTkLabel(info_frame, text=f"Instructions: {prescription.instructions}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            
            # Items
            items_frame = ctk.CTkFrame(view_frame)
            items_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            ctk.CTkLabel(items_frame, text="Prescription Items", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)
            
            # Items header
            items_header = ctk.CTkFrame(items_frame, fg_color="#e0e0e0")
            items_header.pack(fill="x", padx=5, pady=(5, 0))
            
            headers = ["Medicine/Test", "Dosage", "Frequency", "Duration", "Instructions"]
            widths = [200, 100, 100, 100, 200]
            for i, (header, width) in enumerate(zip(headers, widths)):
                ctk.CTkLabel(items_header, text=header, font=ctk.CTkFont(size=10, weight="bold"), width=width).grid(row=0, column=i, padx=2, pady=3, sticky="w")
            
            # Items list
            items_scroll = ctk.CTkScrollableFrame(items_frame, height=200)
            items_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            
            items = session.query(PrescriptionItem).join(Product).filter(PrescriptionItem.prescription_id == prescription_id).all()
            
            for item in items:
                item_frame = ctk.CTkFrame(items_scroll, height=25)
                item_frame.pack(fill="x", padx=2, pady=1)
                item_frame.pack_propagate(False)
                
                ctk.CTkLabel(item_frame, text=item.product.name, width=200, font=ctk.CTkFont(size=9)).grid(row=0, column=0, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=item.dosage or "", width=100, font=ctk.CTkFont(size=9)).grid(row=0, column=1, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=item.frequency or "", width=100, font=ctk.CTkFont(size=9)).grid(row=0, column=2, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=item.duration or "", width=100, font=ctk.CTkFont(size=9)).grid(row=0, column=3, padx=2, pady=1, sticky="w")
                ctk.CTkLabel(item_frame, text=item.instructions or "", width=200, font=ctk.CTkFont(size=9)).grid(row=0, column=4, padx=2, pady=1, sticky="w")
    
    def print_prescription(self, prescription_id):
        # Clear current tab content and show print view
        view_frame = self.tab_view.tab("View Prescriptions")
        for widget in view_frame.winfo_children():
            widget.destroy()
        
        from core.database.connection import db_manager
        from modules.clinic_module.models.entities import Prescription, PrescriptionItem, Patient, Doctor
        from modules.inventory_module.models.entities import Product
        
        with db_manager.get_session() as session:
            prescription = session.query(Prescription).filter(Prescription.id == prescription_id).first()
            if not prescription:
                self.show_message("Prescription not found", "error")
                return
            
            # Header with back button
            header_frame = ctk.CTkFrame(view_frame)
            header_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(header_frame, text="Print Prescription", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
            button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            button_frame.pack(side="right", padx=10, pady=10)
            ctk.CTkButton(button_frame, text="Print", command=lambda: self.show_message("Print functionality will be implemented"), width=70).pack(side="right", padx=5)
            ctk.CTkButton(button_frame, text="Back", command=lambda: self.return_to_prescriptions_list(), width=70).pack(side="right", padx=5)
            
            # Print content
            content_frame = ctk.CTkScrollableFrame(view_frame)
            content_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Clinic header
            ctk.CTkLabel(content_frame, text="MEDICAL PRESCRIPTION", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
            
            # Doctor and prescription details
            details_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            details_frame.pack(fill="x", pady=10)
            
            left_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            left_frame.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(left_frame, text=f"Dr. {prescription.doctor.first_name} {prescription.doctor.last_name}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(left_frame, text=f"Specialization: {prescription.doctor.specialization or 'General Medicine'}", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x")
            ctk.CTkLabel(left_frame, text=f"License: {prescription.doctor.license_number or 'N/A'}", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x")
            
            right_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            right_frame.pack(side="right", fill="x", expand=True)
            
            ctk.CTkLabel(right_frame, text=f"RX Number: {prescription.prescription_number}", font=ctk.CTkFont(size=11, weight="bold"), anchor="e").pack(fill="x")
            ctk.CTkLabel(right_frame, text=f"Date: {prescription.prescription_date.strftime('%d/%m/%Y')}", font=ctk.CTkFont(size=11), anchor="e").pack(fill="x")
            
            # Patient details
            patient_frame = ctk.CTkFrame(content_frame)
            patient_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(patient_frame, text="Patient Information", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=5)
            ctk.CTkLabel(patient_frame, text=f"Name: {prescription.patient.first_name} {prescription.patient.last_name}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=20, pady=2)
            ctk.CTkLabel(patient_frame, text=f"Patient ID: {prescription.patient.patient_number}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=20, pady=2)
            if prescription.patient.phone:
                ctk.CTkLabel(patient_frame, text=f"Phone: {prescription.patient.phone}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=20, pady=2)
            
            # Prescription items
            items_frame = ctk.CTkFrame(content_frame)
            items_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(items_frame, text="Prescription", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=5)
            
            # Items table header
            items_header = ctk.CTkFrame(items_frame, fg_color="#e0e0e0")
            items_header.pack(fill="x", padx=10, pady=(5, 0))
            
            headers = ["Medicine/Test", "Dosage", "Frequency", "Duration", "Instructions"]
            for i, header in enumerate(headers):
                ctk.CTkLabel(items_header, text=header, font=ctk.CTkFont(size=10, weight="bold")).grid(row=0, column=i, padx=10, pady=5, sticky="w")
            
            # Items
            items = session.query(PrescriptionItem).join(Product).filter(PrescriptionItem.prescription_id == prescription_id).all()
            
            for i, item in enumerate(items):
                item_frame = ctk.CTkFrame(items_frame, fg_color="white" if i % 2 == 0 else "#f9f9f9", height=30)
                item_frame.pack(fill="x", padx=10, pady=1)
                item_frame.pack_propagate(False)
                
                ctk.CTkLabel(item_frame, text=item.product.name, font=ctk.CTkFont(size=10)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(item_frame, text=item.dosage or "", font=ctk.CTkFont(size=10)).grid(row=0, column=1, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(item_frame, text=item.frequency or "", font=ctk.CTkFont(size=10)).grid(row=0, column=2, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(item_frame, text=item.duration or "", font=ctk.CTkFont(size=10)).grid(row=0, column=3, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(item_frame, text=item.instructions or "", font=ctk.CTkFont(size=10)).grid(row=0, column=4, padx=10, pady=5, sticky="w")
            
            # General instructions
            if prescription.instructions:
                instructions_frame = ctk.CTkFrame(content_frame)
                instructions_frame.pack(fill="x", pady=10)
                
                ctk.CTkLabel(instructions_frame, text="General Instructions", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=5)
                ctk.CTkLabel(instructions_frame, text=prescription.instructions, font=ctk.CTkFont(size=11), wraplength=600).pack(anchor="w", padx=20, pady=5)
            
            # Doctor signature
            signature_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            signature_frame.pack(fill="x", pady=20)
            
            ctk.CTkLabel(signature_frame, text=f"Dr. {prescription.doctor.first_name} {prescription.doctor.last_name}", font=ctk.CTkFont(size=12, weight="bold"), anchor="e").pack(fill="x", padx=50)
            ctk.CTkLabel(signature_frame, text="Doctor's Signature", font=ctk.CTkFont(size=10), anchor="e").pack(fill="x", padx=50)
    
    def return_to_prescriptions_list(self):
        # Clear the view tab and rebuild the prescriptions list
        view_frame = self.tab_view.tab("View Prescriptions")
        for widget in view_frame.winfo_children():
            widget.destroy()
        
        # Rebuild the view tab
        self.setup_view_tab()