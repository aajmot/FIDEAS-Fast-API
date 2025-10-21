import customtkinter as ctk
import tkinter as tk
from datetime import datetime
from core.shared.components.base_screen import BaseScreen
from modules.clinic_module.services.medical_record_service import MedicalRecordService
from modules.clinic_module.services.patient_service import PatientService
from modules.clinic_module.services.doctor_service import DoctorService
from modules.clinic_module.services.appointment_service import AppointmentService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class MedicalRecordScreen(BaseScreen):
    def __init__(self, parent, clinic_module, **kwargs):
        self.clinic_module = clinic_module
        self.medical_record_service = MedicalRecordService()
        self.patient_service = PatientService()
        self.doctor_service = DoctorService()
        self.appointment_service = AppointmentService()
        self.selected_record = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        ctk.CTkLabel(header_frame, text="Medical Records", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(header_frame, text="Back", command=self.back_to_dashboard, width=80).pack(side="right", padx=10, pady=10)
        
        # Tab view
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create tabs
        self.tab_view.add("Create Record")
        self.tab_view.add("View Records")
        
        self.setup_create_tab()
        self.setup_view_tab()
    
    def setup_create_tab(self):
        create_frame = self.tab_view.tab("Create Record")
        
        # Record Info Frame
        info_frame = ctk.CTkFrame(create_frame)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        # Row 1
        ctk.CTkLabel(info_frame, text="Record Number:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.record_number_input = ctk.CTkEntry(info_frame, width=150)
        self.record_number_input.grid(row=0, column=1, padx=5, pady=5)
        self.generate_record_number()
        
        ctk.CTkLabel(info_frame, text="Patient:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.patient_var = ctk.StringVar()
        self.patient_dropdown = ctk.CTkComboBox(info_frame, variable=self.patient_var, width=200)
        self.patient_dropdown.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(info_frame, text="Visit Date:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.visit_date_input = ctk.CTkEntry(info_frame, width=120, placeholder_text="YYYY-MM-DD")
        self.visit_date_input.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.visit_date_input.grid(row=0, column=5, padx=5, pady=5)
        
        # Row 2
        ctk.CTkLabel(info_frame, text="Doctor:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.doctor_var = ctk.StringVar()
        self.doctor_dropdown = ctk.CTkComboBox(info_frame, variable=self.doctor_var, width=200)
        self.doctor_dropdown.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        
        ctk.CTkLabel(info_frame, text="Appointment:").grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.appointment_var = ctk.StringVar()
        self.appointment_dropdown = ctk.CTkComboBox(info_frame, variable=self.appointment_var, width=200)
        self.appointment_dropdown.grid(row=1, column=4, columnspan=2, padx=5, pady=5)
        
        # Medical Details Frame (scrollable)
        details_frame = ctk.CTkScrollableFrame(create_frame, height=300)
        details_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left column
        left_frame = ctk.CTkFrame(details_frame)
        left_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(left_frame, text="Chief Complaint:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.chief_complaint_text = ctk.CTkTextbox(left_frame, height=80)
        self.chief_complaint_text.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(left_frame, text="Diagnosis:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(0, 5))
        self.diagnosis_text = ctk.CTkTextbox(left_frame, height=80)
        self.diagnosis_text.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(left_frame, text="Treatment Plan:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(0, 5))
        self.treatment_plan_text = ctk.CTkTextbox(left_frame, height=80)
        self.treatment_plan_text.pack(fill="x", padx=10, pady=(0, 10))
        
        # Right column
        right_frame = ctk.CTkFrame(details_frame)
        right_frame.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(right_frame, text="Vital Signs:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Vital signs grid
        vitals_grid = ctk.CTkFrame(right_frame)
        vitals_grid.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(vitals_grid, text="BP:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.bp_input = ctk.CTkEntry(vitals_grid, width=100, placeholder_text="120/80")
        self.bp_input.grid(row=0, column=1, padx=5, pady=2)
        
        ctk.CTkLabel(vitals_grid, text="Temp:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.temp_input = ctk.CTkEntry(vitals_grid, width=100, placeholder_text="98.6°F")
        self.temp_input.grid(row=0, column=3, padx=5, pady=2)
        
        ctk.CTkLabel(vitals_grid, text="Pulse:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.pulse_input = ctk.CTkEntry(vitals_grid, width=100, placeholder_text="72 bpm")
        self.pulse_input.grid(row=1, column=1, padx=5, pady=2)
        
        ctk.CTkLabel(vitals_grid, text="Weight:").grid(row=1, column=2, padx=5, pady=2, sticky="w")
        self.weight_input = ctk.CTkEntry(vitals_grid, width=100, placeholder_text="70 kg")
        self.weight_input.grid(row=1, column=3, padx=5, pady=2)
        
        ctk.CTkLabel(right_frame, text="Lab Results:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.lab_results_text = ctk.CTkTextbox(right_frame, height=80)
        self.lab_results_text.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(right_frame, text="Notes:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(0, 5))
        self.notes_text = ctk.CTkTextbox(right_frame, height=80)
        self.notes_text.pack(fill="x", padx=10, pady=(0, 10))
        
        self.load_dropdowns()
        
        # Action Buttons
        button_frame = ctk.CTkFrame(create_frame)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Save Record", command=self.save_record, height=30, width=150)
        self.save_btn.pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=30, width=100).pack(side="left", padx=5)
    
    def generate_record_number(self):
        record_number = f"MR-{datetime.now().strftime('%d%m%Y%H%M%S%f')[:-3]}"
        self.record_number_input.delete(0, tk.END)
        self.record_number_input.insert(0, record_number)
        self.record_number_input.configure(state="readonly")
    
    def load_dropdowns(self):
        # Load patients
        patients = self.patient_service.get_all(tenant_id=1)
        patient_options = [f"{p.patient_number} - {p.first_name} {p.last_name}" for p in patients]
        self.patient_dropdown.configure(values=patient_options)
        
        # Load doctors
        doctors = self.doctor_service.get_all(tenant_id=1)
        doctor_options = [f"{d.employee_id} - Dr. {d.first_name} {d.last_name}" for d in doctors]
        self.doctor_dropdown.configure(values=doctor_options)
        
        # Load appointments
        appointments = self.appointment_service.get_all(tenant_id=1)
        appointment_options = [f"{a.appointment_number} - {a.appointment_date}" for a in appointments]
        self.appointment_dropdown.configure(values=appointment_options)
    
    @ExceptionMiddleware.handle_exceptions("MedicalRecordScreen")
    def save_record(self):
        if not all([self.patient_var.get(), self.doctor_var.get()]):
            self.show_message("Please select patient and doctor", "error")
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
            
            # Get appointment ID if selected
            appointment_id = None
            if self.appointment_var.get():
                appointment_text = self.appointment_var.get()
                appointment_number = appointment_text.split(" - ")[0]
                appointments = self.appointment_service.get_all(tenant_id=1)
                appointment = next((a for a in appointments if a.appointment_number == appointment_number), None)
                if appointment:
                    appointment_id = appointment.id
            
            if not all([patient, doctor]):
                self.show_message("Invalid patient or doctor selection", "error")
                return
            
            # Prepare vital signs JSON
            vital_signs = {
                "bp": self.bp_input.get(),
                "temp": self.temp_input.get(),
                "pulse": self.pulse_input.get(),
                "weight": self.weight_input.get()
            }
            
            record_data = {
                'patient_id': patient.id,
                'doctor_id': doctor.id,
                'appointment_id': appointment_id,
                'visit_date': datetime.strptime(self.visit_date_input.get(), '%Y-%m-%d'),
                'chief_complaint': self.chief_complaint_text.get("1.0", tk.END).strip(),
                'diagnosis': self.diagnosis_text.get("1.0", tk.END).strip(),
                'treatment_plan': self.treatment_plan_text.get("1.0", tk.END).strip(),
                'vital_signs': str(vital_signs),
                'lab_results': self.lab_results_text.get("1.0", tk.END).strip(),
                'notes': self.notes_text.get("1.0", tk.END).strip(),
                'tenant_id': 1
            }
            
            self.medical_record_service.create(record_data)
            self.show_message("Medical record saved successfully")
            self.load_records()
            self.clear_form()
            
        except Exception as e:
            self.show_message(f"Error saving record: {str(e)}", "error")
    
    def clear_form(self):
        # Generate new record number
        self.record_number_input.configure(state="normal")
        self.generate_record_number()
        
        self.patient_var.set("")
        self.doctor_var.set("")
        self.appointment_var.set("")
        self.visit_date_input.delete(0, tk.END)
        self.visit_date_input.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Clear text areas
        self.chief_complaint_text.delete("1.0", tk.END)
        self.diagnosis_text.delete("1.0", tk.END)
        self.treatment_plan_text.delete("1.0", tk.END)
        self.lab_results_text.delete("1.0", tk.END)
        self.notes_text.delete("1.0", tk.END)
        
        # Clear vital signs
        self.bp_input.delete(0, tk.END)
        self.temp_input.delete(0, tk.END)
        self.pulse_input.delete(0, tk.END)
        self.weight_input.delete(0, tk.END)
    
    def setup_view_tab(self):
        view_frame = self.tab_view.tab("View Records")
        
        # Clear existing content
        for widget in view_frame.winfo_children():
            widget.destroy()
        
        # Header
        header_frame = ctk.CTkFrame(view_frame)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Medical Records", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
        
        # Records list
        records_frame = ctk.CTkScrollableFrame(view_frame)
        records_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Header
        list_header_frame = ctk.CTkFrame(records_frame, fg_color="#e0e0e0")
        list_header_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        headers = ["Record Number", "Patient", "Doctor", "Visit Date", "Actions"]
        widths = [120, 150, 150, 100, 100]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(list_header_frame, text=header, font=ctk.CTkFont(size=11, weight="bold"), 
                        text_color="#333333", width=width).grid(row=0, column=i, padx=2, pady=5)
        
        self.records_list_frame = ctk.CTkFrame(records_frame)
        self.records_list_frame.pack(fill="x", padx=5, pady=5)
        
        # Refresh button
        ctk.CTkButton(view_frame, text="Refresh", command=self.load_records, height=30).pack(pady=5)
        
        self.load_records()
    
    @ExceptionMiddleware.handle_exceptions("MedicalRecordScreen")
    def load_records(self):
        # Clear existing records
        for widget in self.records_list_frame.winfo_children():
            widget.destroy()
        
        from core.database.connection import db_manager
        from modules.clinic_module.models.entities import MedicalRecord, Patient, Doctor
        
        with db_manager.get_session() as session:
            query = session.query(MedicalRecord).join(Patient).join(Doctor)
            query = query.filter(MedicalRecord.tenant_id == 1)
            records = query.all()
            
            for i, record in enumerate(records):
                row_frame = ctk.CTkFrame(self.records_list_frame, height=30)
                row_frame.pack(fill="x", padx=1, pady=1)
                row_frame.pack_propagate(False)
                
                # Record details
                ctk.CTkLabel(row_frame, text=record.record_number, width=120, font=ctk.CTkFont(size=9)).grid(row=0, column=0, padx=2, pady=2)
                ctk.CTkLabel(row_frame, text=f"{record.patient.first_name} {record.patient.last_name}", width=150, font=ctk.CTkFont(size=9)).grid(row=0, column=1, padx=2, pady=2)
                ctk.CTkLabel(row_frame, text=f"Dr. {record.doctor.first_name} {record.doctor.last_name}", width=150, font=ctk.CTkFont(size=9)).grid(row=0, column=2, padx=2, pady=2)
                ctk.CTkLabel(row_frame, text=record.visit_date.strftime('%Y-%m-%d'), width=100, font=ctk.CTkFont(size=9)).grid(row=0, column=3, padx=2, pady=2)
                
                # Action buttons
                view_btn = ctk.CTkLabel(row_frame, text="👁", font=ctk.CTkFont(size=14), cursor="hand2", width=30)
                view_btn.grid(row=0, column=4, padx=5, pady=2)
                view_btn.bind("<Button-1>", lambda e, rid=record.id: self.view_record(rid))
                
                print_btn = ctk.CTkLabel(row_frame, text="🖨", font=ctk.CTkFont(size=14), cursor="hand2", width=30)
                print_btn.grid(row=0, column=5, padx=5, pady=2)
                print_btn.bind("<Button-1>", lambda e, rid=record.id: self.print_record(rid))
    
    def view_record(self, record_id):
        # Clear current tab content and show record details
        view_frame = self.tab_view.tab("View Records")
        for widget in view_frame.winfo_children():
            widget.destroy()
        
        from core.database.connection import db_manager
        from modules.clinic_module.models.entities import MedicalRecord, Patient, Doctor
        
        with db_manager.get_session() as session:
            record = session.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
            if not record:
                self.show_message("Medical record not found", "error")
                return
            
            # Header with back button
            header_frame = ctk.CTkFrame(view_frame)
            header_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(header_frame, text="Medical Record Details", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10, pady=10)
            ctk.CTkButton(header_frame, text="Back", command=lambda: self.return_to_records_list(), width=80).pack(side="right", padx=10, pady=10)
            
            # Record info
            info_frame = ctk.CTkFrame(view_frame)
            info_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(info_frame, text=f"Record Number: {record.record_number}", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=2)
            ctk.CTkLabel(info_frame, text=f"Patient: {record.patient.first_name} {record.patient.last_name}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            ctk.CTkLabel(info_frame, text=f"Doctor: Dr. {record.doctor.first_name} {record.doctor.last_name}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            ctk.CTkLabel(info_frame, text=f"Visit Date: {record.visit_date.strftime('%Y-%m-%d')}", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=1)
            
            # Medical details
            details_frame = ctk.CTkScrollableFrame(view_frame)
            details_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            if record.chief_complaint:
                ctk.CTkLabel(details_frame, text="Chief Complaint:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
                ctk.CTkLabel(details_frame, text=record.chief_complaint, font=ctk.CTkFont(size=10), wraplength=600).pack(anchor="w", padx=20, pady=2)
            
            if record.diagnosis:
                ctk.CTkLabel(details_frame, text="Diagnosis:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
                ctk.CTkLabel(details_frame, text=record.diagnosis, font=ctk.CTkFont(size=10), wraplength=600).pack(anchor="w", padx=20, pady=2)
            
            if record.treatment_plan:
                ctk.CTkLabel(details_frame, text="Treatment Plan:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
                ctk.CTkLabel(details_frame, text=record.treatment_plan, font=ctk.CTkFont(size=10), wraplength=600).pack(anchor="w", padx=20, pady=2)
            
            if record.vital_signs:
                ctk.CTkLabel(details_frame, text="Vital Signs:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
                ctk.CTkLabel(details_frame, text=record.vital_signs, font=ctk.CTkFont(size=10)).pack(anchor="w", padx=20, pady=2)
            
            if record.lab_results:
                ctk.CTkLabel(details_frame, text="Lab Results:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
                ctk.CTkLabel(details_frame, text=record.lab_results, font=ctk.CTkFont(size=10), wraplength=600).pack(anchor="w", padx=20, pady=2)
            
            if record.notes:
                ctk.CTkLabel(details_frame, text="Notes:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
                ctk.CTkLabel(details_frame, text=record.notes, font=ctk.CTkFont(size=10), wraplength=600).pack(anchor="w", padx=20, pady=2)
    
    def print_record(self, record_id):
        # Implementation similar to prescription print
        self.show_message("Print medical record functionality")
    
    def return_to_records_list(self):
        # Clear the view tab and rebuild the records list
        view_frame = self.tab_view.tab("View Records")
        for widget in view_frame.winfo_children():
            widget.destroy()
        
        # Rebuild the view tab
        self.setup_view_tab()