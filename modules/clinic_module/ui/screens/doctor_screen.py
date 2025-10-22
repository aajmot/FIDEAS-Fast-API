import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.clinic_module.services.doctor_service import DoctorService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class DoctorScreen(BaseScreen):
    def __init__(self, parent, clinic_module, **kwargs):
        self.clinic_module = clinic_module
        self.doctor_service = DoctorService()
        self.selected_doctor = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Doctor Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
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
        
        ctk.CTkLabel(form_frame, text="Specialization:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.specialization_input = ctk.CTkEntry(form_frame, width=200)
        self.specialization_input.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="License Number:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.license_number_input = ctk.CTkEntry(form_frame, width=200)
        self.license_number_input.grid(row=1, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Phone:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.phone_input = ctk.CTkEntry(form_frame, width=200)
        self.phone_input.grid(row=2, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Email:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.email_input = ctk.CTkEntry(form_frame, width=200)
        self.email_input.grid(row=2, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Consultation Fee:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.consultation_fee_input = ctk.CTkEntry(form_frame, width=200)
        self.consultation_fee_input.grid(row=3, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_doctor, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'employee_id', 'title': 'Employee ID', 'width': 100},
            {'key': 'first_name', 'title': 'First Name', 'width': 120},
            {'key': 'last_name', 'title': 'Last Name', 'width': 120},
            {'key': 'specialization', 'title': 'Specialization', 'width': 150},
            {'key': 'phone', 'title': 'Phone', 'width': 120},
            {'key': 'consultation_fee', 'title': 'Fee', 'width': 80}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_doctor_select,
            on_delete=self.on_doctor_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_doctors()
    
    @ExceptionMiddleware.handle_exceptions("DoctorScreen")
    def load_doctors(self):
        doctors = self.doctor_service.get_all(tenant_id=1)
        doctors_data = []
        
        for doctor in doctors:
            doctor_data = {
                'id': doctor.id,
                'employee_id': doctor.employee_id,
                'first_name': doctor.first_name,
                'last_name': doctor.last_name,
                'specialization': doctor.specialization or '',
                'phone': doctor.phone,
                'consultation_fee': f"${doctor.consultation_fee}" if doctor.consultation_fee else ''
            }
            doctors_data.append(doctor_data)
        
        self.data_grid.set_data(doctors_data)
    
    def on_doctor_select(self, doctor_data):
        self.selected_doctor = doctor_data
        self.first_name_input.delete(0, tk.END)
        self.first_name_input.insert(0, doctor_data['first_name'])
        self.last_name_input.delete(0, tk.END)
        self.last_name_input.insert(0, doctor_data['last_name'])
        self.specialization_input.delete(0, tk.END)
        self.specialization_input.insert(0, doctor_data['specialization'])
        self.phone_input.delete(0, tk.END)
        self.phone_input.insert(0, doctor_data.get('phone', ''))
        
        # Load full doctor details for other fields
        doctors = self.doctor_service.get_all(tenant_id=1)
        doctor = next((d for d in doctors if d.id == doctor_data['id']), None)
        if doctor:
            self.license_number_input.delete(0, tk.END)
            self.license_number_input.insert(0, doctor.license_number or '')
            self.email_input.delete(0, tk.END)
            self.email_input.insert(0, doctor.email or '')
            self.consultation_fee_input.delete(0, tk.END)
            self.consultation_fee_input.insert(0, str(doctor.consultation_fee) if doctor.consultation_fee else '')
        
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("DoctorScreen")
    def save_doctor(self):
        if not all([self.first_name_input.get(), self.last_name_input.get(), self.phone_input.get()]):
            self.show_message("Please fill required fields", "error")
            return
        
        try:
            doctor_data = {
                'first_name': self.first_name_input.get(),
                'last_name': self.last_name_input.get(),
                'specialization': self.specialization_input.get(),
                'license_number': self.license_number_input.get(),
                'phone': self.phone_input.get(),
                'email': self.email_input.get(),
                'consultation_fee': float(self.consultation_fee_input.get()) if self.consultation_fee_input.get() else None,
                'tenant_id': 1
            }
            
            if self.selected_doctor:
                self.doctor_service.update(self.selected_doctor['id'], doctor_data)
                action = "updated"
            else:
                self.doctor_service.create(doctor_data)
                action = "created"
            
            self.show_message(f"Doctor {action} successfully")
            self.clear_form()
            self.load_doctors()
        except Exception as e:
            action = "updating" if self.selected_doctor else "creating"
            self.show_message(f"Error {action} doctor: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_doctor = None
        self.first_name_input.delete(0, tk.END)
        self.last_name_input.delete(0, tk.END)
        self.specialization_input.delete(0, tk.END)
        self.license_number_input.delete(0, tk.END)
        self.phone_input.delete(0, tk.END)
        self.email_input.delete(0, tk.END)
        self.consultation_fee_input.delete(0, tk.END)
        self.save_btn.configure(text="Create")
    @ExceptionMiddleware.handle_exceptions("DoctorScreen")
    def on_doctor_delete(self, doctors_data):
        """Handle doctor deletion"""
        try:
            for doctor_data in doctors_data:
                self.doctor_service.delete(doctor_data['id'])
            
            self.show_message(f"Successfully deleted {len(doctors_data)} doctor(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting doctors: {str(e)}", "error")
            return False