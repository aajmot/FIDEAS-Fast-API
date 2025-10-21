import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.clinic_module.services.appointment_service import AppointmentService
from modules.clinic_module.services.patient_service import PatientService
from core.shared.middleware.exception_handler import ExceptionMiddleware
from datetime import date, time

class AppointmentScreen(BaseScreen):
    def __init__(self, parent, clinic_module, **kwargs):
        self.clinic_module = clinic_module
        self.appointment_service = AppointmentService()
        self.patient_service = PatientService()
        self.selected_appointment = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Appointment Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Form frame
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Form fields
        ctk.CTkLabel(form_frame, text="Patient:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.patient_var = ctk.StringVar()
        self.patient_dropdown = ctk.CTkComboBox(form_frame, variable=self.patient_var, width=200)
        self.patient_dropdown.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.date_input = ctk.CTkEntry(form_frame, width=150)
        self.date_input.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Time (HH:MM):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.time_input = ctk.CTkEntry(form_frame, width=150)
        self.time_input.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Reason:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.reason_input = ctk.CTkEntry(form_frame, width=200)
        self.reason_input.grid(row=1, column=3, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Schedule", command=self.save_appointment, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'appointment_number', 'title': 'Appointment #', 'width': 120},
            {'key': 'patient_name', 'title': 'Patient', 'width': 150},
            {'key': 'appointment_date', 'title': 'Date', 'width': 100},
            {'key': 'appointment_time', 'title': 'Time', 'width': 80},
            {'key': 'status', 'title': 'Status', 'width': 100}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_appointment_select,
            on_delete=self.on_appointment_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_patients()
        self.load_appointments()
    
    def load_patients(self):
        patients = self.patient_service.get_all(tenant_id=1)
        patient_options = [f"{p.patient_number} - {p.first_name} {p.last_name}" for p in patients]
        self.patient_dropdown.configure(values=patient_options)
    
    @ExceptionMiddleware.handle_exceptions("AppointmentScreen")
    def load_appointments(self):
        from core.database.connection import db_manager
        from sqlalchemy import text
        
        appointments_data = []
        
        try:
            with db_manager.get_session() as session:
                # Check if appointments table exists
                result = session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'appointments')"))
                if not result.scalar():
                    self.data_grid.set_data([])
                    return
                
                # Simple query without joins to avoid missing table errors
                result = session.execute(text("SELECT id, appointment_number, patient_id, appointment_date, appointment_time, status FROM appointments WHERE tenant_id = 1"))
                
                for row in result:
                    appointment_data = {
                        'id': row[0],
                        'appointment_number': row[1] or f'APT-{row[0]}',
                        'patient_name': f'Patient {row[2]}',
                        'appointment_date': str(row[3]) if row[3] else '',
                        'appointment_time': str(row[4]) if row[4] else '',
                        'status': row[5] or 'scheduled'
                    }
                    appointments_data.append(appointment_data)
        except Exception as e:
            # If any error, just show empty grid
            pass
        
        self.data_grid.set_data(appointments_data)
    
    def on_appointment_select(self, appointment_data):
        self.selected_appointment = appointment_data
        # Load appointment details for editing if needed
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("AppointmentScreen")
    def save_appointment(self):
        patient_text = self.patient_var.get()
        if not patient_text or not self.date_input.get() or not self.time_input.get():
            self.show_message("Please fill required fields", "error")
            return
        
        try:
            patient_number = patient_text.split(" - ")[0]
            patients = self.patient_service.get_all(tenant_id=1)
            patient = next((p for p in patients if p.patient_number == patient_number), None)
            
            if not patient:
                self.show_message("Patient not found", "error")
                return
            
            appointment_data = {
                'patient_id': patient.id,
                'doctor_id': 1,  # Default doctor
                'appointment_date': date.fromisoformat(self.date_input.get()),
                'appointment_time': time.fromisoformat(self.time_input.get()),
                'reason': self.reason_input.get(),
                'tenant_id': 1
            }
            
            self.appointment_service.create(appointment_data)
            self.show_message("Appointment scheduled successfully")
            self.clear_form()
            self.load_appointments()
        except Exception as e:
            self.show_message(f"Error scheduling appointment: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_appointment = None
        self.patient_var.set("")
        self.date_input.delete(0, tk.END)
        self.time_input.delete(0, tk.END)
        self.reason_input.delete(0, tk.END)
        self.save_btn.configure(text="Schedule")
    @ExceptionMiddleware.handle_exceptions("AppointmentScreen")
    def on_appointment_delete(self, appointments_data):
        """Handle appointment deletion"""
        try:
            for appointment_data in appointments_data:
                self.appointment_service.delete(appointment_data['id'])
            
            self.show_message(f"Successfully deleted {len(appointments_data)} appointment(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting appointments: {str(e)}", "error")
            return False