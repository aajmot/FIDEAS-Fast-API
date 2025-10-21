import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.clinic_module.services.prescription_service import PrescriptionService
from modules.clinic_module.services.patient_service import PatientService
from modules.clinic_module.services.doctor_service import DoctorService
from modules.inventory_module.services.product_service import ProductService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class PrescriptionScreen(BaseScreen):
    def __init__(self, parent, clinic_module, **kwargs):
        self.clinic_module = clinic_module
        self.prescription_service = PrescriptionService()
        self.patient_service = PatientService()
        self.doctor_service = DoctorService()
        self.product_service = ProductService()
        self.selected_prescription = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Prescription Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Form fields
        ctk.CTkLabel(form_frame, text="Patient:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.patient_var = ctk.StringVar()
        self.patient_dropdown = ctk.CTkComboBox(form_frame, variable=self.patient_var, width=200)
        self.patient_dropdown.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Doctor:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.doctor_var = ctk.StringVar()
        self.doctor_dropdown = ctk.CTkComboBox(form_frame, variable=self.doctor_var, width=200)
        self.doctor_dropdown.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Instructions:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.instructions_input = ctk.CTkEntry(form_frame, width=400)
        self.instructions_input.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # Medicine/Test Items Frame
        items_frame = ctk.CTkFrame(self)
        items_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(items_frame, text="Add Medicine/Test:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)
        
        # Item input frame
        item_input_frame = ctk.CTkFrame(items_frame)
        item_input_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(item_input_frame, text="Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.item_type_var = ctk.StringVar(value="medicine")
        self.item_type_dropdown = ctk.CTkComboBox(item_input_frame, variable=self.item_type_var, values=["medicine", "test"], width=100)
        self.item_type_dropdown.grid(row=0, column=1, padx=5, pady=5)
        self.item_type_dropdown.configure(command=self.on_item_type_change)
        
        ctk.CTkLabel(item_input_frame, text="Item:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.item_var = ctk.StringVar()
        self.item_dropdown = ctk.CTkComboBox(item_input_frame, variable=self.item_var, width=200)
        self.item_dropdown.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(item_input_frame, text="Dosage/Notes:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.dosage_input = ctk.CTkEntry(item_input_frame, width=150)
        self.dosage_input.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(item_input_frame, text="Frequency:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.frequency_input = ctk.CTkEntry(item_input_frame, width=150)
        self.frequency_input.grid(row=1, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(item_input_frame, text="Duration:").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        self.duration_input = ctk.CTkEntry(item_input_frame, width=150)
        self.duration_input.grid(row=1, column=5, padx=5, pady=5)
        
        ctk.CTkButton(item_input_frame, text="Add Item", command=self.add_item, width=80).grid(row=0, column=4, padx=5, pady=5)
        
        # Items list
        self.items_listbox = ctk.CTkScrollableFrame(items_frame, height=150)
        self.items_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.prescription_items = []
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_prescription, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'prescription_number', 'title': 'Prescription #', 'width': 120},
            {'key': 'patient_name', 'title': 'Patient', 'width': 150},
            {'key': 'doctor_name', 'title': 'Doctor', 'width': 150},
            {'key': 'prescription_date', 'title': 'Date', 'width': 100}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(self, columns, on_row_select=self.on_prescription_select)
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_dropdowns()
        self.load_prescriptions()
    
    def on_item_type_change(self, value):
        if value == "medicine":
            self.load_medicines()
        else:
            self.load_tests()
    
    def load_medicines(self):
        # Load medicines (products from inventory where category is Medicine)
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Product, Category
        from sqlalchemy import or_
        
        medicine_options = []
        with db_manager.get_session() as session:
            parent_alias = session.query(Category).filter(Category.name == 'Medicine').subquery()
            
            query = session.query(Product).join(Category)
            query = query.filter(
                or_(
                    Category.name == 'Medicine',
                    Category.parent_id.in_(session.query(parent_alias.c.id))
                )
            )
            if 1:  # tenant_id
                query = query.filter(Product.tenant_id == 1)
            
            products = query.all()
            medicine_options = [f"{p.code} - {p.name}" for p in products]
        
        self.item_dropdown.configure(values=medicine_options)
    
    def load_tests(self):
        # Load tests (products from inventory where category is Test)
        from core.database.connection import db_manager
        from modules.inventory_module.models.entities import Product, Category
        from sqlalchemy import or_
        
        test_options = []
        with db_manager.get_session() as session:
            parent_alias = session.query(Category).filter(Category.name == 'Test').subquery()
            
            query = session.query(Product).join(Category)
            query = query.filter(
                or_(
                    Category.name == 'Test',
                    Category.parent_id.in_(session.query(parent_alias.c.id))
                )
            )
            if 1:  # tenant_id
                query = query.filter(Product.tenant_id == 1)
            
            products = query.all()
            test_options = [f"{p.code} - {p.name}" for p in products]
        
        self.item_dropdown.configure(values=test_options)
    
    def add_item(self):
        if not self.item_var.get():
            self.show_message("Please select an item", "error")
            return
        
        item_data = {
            'type': self.item_type_var.get(),
            'item': self.item_var.get(),
            'dosage': self.dosage_input.get(),
            'frequency': self.frequency_input.get(),
            'duration': self.duration_input.get()
        }
        
        self.prescription_items.append(item_data)
        self.refresh_items_display()
        self.clear_item_form()
    
    def refresh_items_display(self):
        # Clear existing items
        for widget in self.items_listbox.winfo_children():
            widget.destroy()
        
        # Display items
        for i, item in enumerate(self.prescription_items):
            item_frame = ctk.CTkFrame(self.items_listbox)
            item_frame.pack(fill="x", padx=5, pady=2)
            
            item_text = f"{item['type'].title()}: {item['item']} - {item['dosage']} - {item['frequency']} - {item['duration']}"
            ctk.CTkLabel(item_frame, text=item_text).pack(side="left", padx=10, pady=5)
            
            ctk.CTkButton(item_frame, text="Remove", width=60, command=lambda idx=i: self.remove_item(idx)).pack(side="right", padx=5, pady=2)
    
    def remove_item(self, index):
        if 0 <= index < len(self.prescription_items):
            self.prescription_items.pop(index)
            self.refresh_items_display()
    
    def clear_item_form(self):
        self.item_var.set("")
        self.dosage_input.delete(0, tk.END)
        self.frequency_input.delete(0, tk.END)
        self.duration_input.delete(0, tk.END)
    
    def load_dropdowns(self):
        # Load patients
        patients = self.patient_service.get_all(tenant_id=1)
        patient_options = [f"{p.patient_number} - {p.first_name} {p.last_name}" for p in patients]
        self.patient_dropdown.configure(values=patient_options)
        
        # Load doctors
        doctors = self.doctor_service.get_all(tenant_id=1)
        doctor_options = [f"{d.employee_id} - Dr. {d.first_name} {d.last_name}" for d in doctors]
        self.doctor_dropdown.configure(values=doctor_options)
        
        # Load initial medicines
        self.load_medicines()
    
    @ExceptionMiddleware.handle_exceptions("PrescriptionScreen")
    def load_prescriptions(self):
        from core.database.connection import db_manager
        from modules.clinic_module.models.entities import Prescription, Patient, Doctor
        
        prescriptions_data = []
        
        with db_manager.get_session() as session:
            query = session.query(Prescription).join(Patient).join(Doctor)
            query = query.filter(Prescription.tenant_id == 1)
            prescriptions = query.all()
            
            for prescription in prescriptions:
                prescription_data = {
                    'id': prescription.id,
                    'prescription_number': prescription.prescription_number,
                    'patient_name': f"{prescription.patient.first_name} {prescription.patient.last_name}",
                    'doctor_name': f"Dr. {prescription.doctor.first_name} {prescription.doctor.last_name}",
                    'prescription_date': str(prescription.prescription_date.date())
                }
                prescriptions_data.append(prescription_data)
        
        self.data_grid.set_data(prescriptions_data)
    
    def on_prescription_select(self, prescription_data):
        self.selected_prescription = prescription_data
        # Load prescription details for viewing
    
    @ExceptionMiddleware.handle_exceptions("PrescriptionScreen")
    def save_prescription(self):
        if not all([self.patient_var.get(), self.doctor_var.get()]) or not self.prescription_items:
            self.show_message("Please fill required fields and add at least one item", "error")
            return
        
        try:
            # Get patient ID
            patient_text = self.patient_var.get()
            patient_number = patient_text.split(" - ")[0]
            patients = self.patient_service.get_all(tenant_id=1)
            patient = next((p for p in patients if p.patient_number == patient_number), None)
            
            # Get doctor ID
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
                    item_code = item['item'].split(" - ")[0]
                    product = session.query(Product).filter(Product.code == item_code, Product.tenant_id == 1).first()
                    
                    if product:
                        items_data.append({
                            'product_id': product.id,
                            'dosage': item['dosage'],
                            'frequency': item['frequency'],
                            'duration': item['duration'],
                            'instructions': f"{item['type'].title()}: {item['dosage']} {item['frequency']} {item['duration']}"
                        })
            
            if not items_data:
                self.show_message("No valid items found", "error")
                return
            
            self.prescription_service.create(prescription_data, items_data)
            self.show_message("Prescription created successfully")
            self.clear_form()
            self.load_prescriptions()
        except Exception as e:
            self.show_message(f"Error creating prescription: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_prescription = None
        self.patient_var.set("")
        self.doctor_var.set("")
        self.instructions_input.delete(0, tk.END)
        self.prescription_items = []
        self.refresh_items_display()
        self.clear_item_form()
        self.save_btn.configure(text="Create")