import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.clinic_module.services.patient_service import PatientService
from core.shared.middleware.exception_handler import ExceptionMiddleware
from core.shared.components.import_mixin import ImportMixin

class PatientScreen(BaseScreen, ImportMixin):
    def __init__(self, parent, clinic_module, **kwargs):
        self.clinic_module = clinic_module
        self.patient_service = PatientService()
        self.selected_patient = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Patient Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Form fields
        ctk.CTkLabel(form_frame, text="First Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.first_name_input = ctk.CTkEntry(form_frame, width=200)
        self.first_name_input.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Last Name:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.last_name_input = ctk.CTkEntry(form_frame, width=200)
        self.last_name_input.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Phone:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.phone_input = ctk.CTkEntry(form_frame, width=200)
        self.phone_input.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Email:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.email_input = ctk.CTkEntry(form_frame, width=200)
        self.email_input.grid(row=1, column=3, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_patient, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        self.add_import_button(button_frame)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'patient_number', 'title': 'Patient #', 'width': 100},
            {'key': 'first_name', 'title': 'First Name', 'width': 120},
            {'key': 'last_name', 'title': 'Last Name', 'width': 120},
            {'key': 'phone', 'title': 'Phone', 'width': 120},
            {'key': 'email', 'title': 'Email', 'width': 150}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_patient_select,
            on_delete=self.on_patient_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_patients()
    
    @ExceptionMiddleware.handle_exceptions("PatientScreen")
    def load_patients(self):
        patients = self.patient_service.get_all(tenant_id=1)
        patients_data = []
        
        for patient in patients:
            patient_data = {
                'id': patient.id,
                'patient_number': patient.patient_number,
                'first_name': patient.first_name,
                'last_name': patient.last_name,
                'phone': patient.phone,
                'email': patient.email or ''
            }
            patients_data.append(patient_data)
        
        self.data_grid.set_data(patients_data)
    
    def on_patient_select(self, patient_data):
        self.selected_patient = patient_data
        self.first_name_input.delete(0, tk.END)
        self.first_name_input.insert(0, patient_data['first_name'])
        self.last_name_input.delete(0, tk.END)
        self.last_name_input.insert(0, patient_data['last_name'])
        self.phone_input.delete(0, tk.END)
        self.phone_input.insert(0, patient_data['phone'])
        self.email_input.delete(0, tk.END)
        self.email_input.insert(0, patient_data['email'])
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("PatientScreen")
    def save_patient(self):
        if not all([self.first_name_input.get(), self.last_name_input.get(), self.phone_input.get()]):
            self.show_message("Please fill required fields", "error")
            return
        
        try:
            patient_data = {
                'first_name': self.first_name_input.get(),
                'last_name': self.last_name_input.get(),
                'phone': self.phone_input.get(),
                'email': self.email_input.get(),
                'tenant_id': 1
            }
            
            if self.selected_patient:
                self.patient_service.update(self.selected_patient['id'], patient_data)
                action = "updated"
            else:
                self.patient_service.create(patient_data)
                action = "created"
            
            self.show_message(f"Patient {action} successfully")
            self.clear_form()
            self.load_patients()
        except Exception as e:
            action = "updating" if self.selected_patient else "creating"
            self.show_message(f"Error {action} patient: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_patient = None
        self.first_name_input.delete(0, tk.END)
        self.last_name_input.delete(0, tk.END)
        self.phone_input.delete(0, tk.END)
        self.email_input.delete(0, tk.END)
        self.save_btn.configure(text="Create")
    
    def download_template(self):
        template_data = {
            'First Name': ['John', 'Jane', 'Mike'],
            'Last Name': ['Doe', 'Smith', 'Johnson'],
            'Phone': ['1234567890', '0987654321', '5555555555'],
            'Email': ['john@example.com', 'jane@example.com', 'mike@example.com'],
            'Gender': ['Male', 'Female', 'Male'],
            'Blood Group': ['O+', 'A+', 'B+']
        }
        self.create_template_file(template_data, 'patients')
    
    def import_from_excel(self):
        def process_patient_row(row, index):
            first_name = str(row['First Name']).strip()
            last_name = str(row['Last Name']).strip()
            phone = str(row['Phone']).strip()
            email = str(row.get('Email', '')).strip()
            gender = str(row.get('Gender', '')).strip()
            blood_group = str(row.get('Blood Group', '')).strip()
            
            if not first_name or not last_name or not phone:
                return False
            
            patient_data = {
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone,
                'email': email,
                'gender': gender if gender else None,
                'blood_group': blood_group if blood_group else None,
                'tenant_id': 1
            }
            
            self.patient_service.create(patient_data)
            return True
        
        self.process_import_file(['First Name', 'Last Name', 'Phone'], process_patient_row, 'patients')
    
    def load_data(self):
        self.load_patients()
    @ExceptionMiddleware.handle_exceptions("PatientScreen")
    def on_patient_delete(self, patients_data):
        """Handle patient deletion"""
        try:
            for patient_data in patients_data:
                self.patient_service.delete(patient_data['id'])
            
            self.show_message(f"Successfully deleted {len(patients_data)} patient(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting patients: {str(e)}", "error")
            return False