from core.shared.utils.logger import logger
import customtkinter as ctk

class ClinicModule:
    def __init__(self, root):
        self.name = "Clinic Module"
        self.root = root
        self.current_screen = None
        logger.info("Clinic Module initialized", "ClinicModule")
    

    
    def show_patient_screen(self):
        self.clear_current_screen()
        from modules.clinic_module.ui.screens.patient_screen import PatientScreen
        self.current_screen = PatientScreen(self.root, self)
    
    def show_doctor_screen(self):
        self.clear_current_screen()
        from modules.clinic_module.ui.screens.doctor_screen import DoctorScreen
        self.current_screen = DoctorScreen(self.root, self)
    
    def show_appointment_screen(self):
        self.clear_current_screen()
        from modules.clinic_module.ui.screens.appointment_screen import AppointmentScreen
        self.current_screen = AppointmentScreen(self.root, self)
    
    def show_medical_records_screen(self):
        self.clear_current_screen()
        from modules.clinic_module.ui.screens.medical_record_screen import MedicalRecordScreen
        self.current_screen = MedicalRecordScreen(self.root, self)
    
    def show_prescription_screen(self):
        self.clear_current_screen()
        from modules.clinic_module.ui.screens.prescription_screen import PrescriptionScreen
        self.current_screen = PrescriptionScreen(self.root, self)
    
    def show_billing_screen(self):
        self.clear_current_screen()
        from modules.clinic_module.ui.screens.billing_screen import BillingScreen
        self.current_screen = BillingScreen(self.root, self)
    
    def show_inventory_integration_screen(self):
        self.clear_current_screen()
        # Show inventory module for medical supplies
        from modules.inventory_module.inventory_module import InventoryModule
        inventory_module = InventoryModule(self.root)
        # Inventory screens are now accessed through modern dashboard
        pass
    
    def show_employee_screen(self):
        self.clear_current_screen()
        from modules.clinic_module.ui.screens.employee_screen import EmployeeScreen
        self.current_screen = EmployeeScreen(self.root, self)
    
    def show_reports_screen(self):
        self.clear_current_screen()
        # Placeholder for reports
        self.current_screen = ctk.CTkLabel(self.root, text="Healthcare Reports - Coming Soon")
        self.current_screen.pack(pady=50)
    
    def clear_current_screen(self):
        if self.current_screen:
            self.current_screen.destroy()
        logger.info("Screen cleared", "ClinicModule")
    

    

    
    def initialize_data(self):
        """Initialize default data for clinic module"""
        from modules.clinic_module.models.entities import Doctor, Employee
        from core.database.connection import db_manager
        
        with db_manager.get_session() as session:
            # Create default doctor
            doctors = session.query(Doctor).all()
            if not doctors:
                default_doctor = Doctor(
                    employee_id='DOC001',
                    first_name='Dr. John',
                    last_name='Smith',
                    specialization='General Medicine',
                    license_number='LIC123456',
                    phone='555-0123',
                    email='dr.smith@clinic.com',
                    consultation_fee=100.00,
                    tenant_id=1
                )
                session.add(default_doctor)
                logger.info("Default doctor created", "ClinicModule")
            
            # Create default employees
            employees = session.query(Employee).all()
            if not employees:
                default_employees = [
                    Employee(
                        employee_number='EMP001',
                        first_name='Jane',
                        last_name='Doe',
                        role='nurse',
                        department='General',
                        phone='555-0124',
                        email='jane.doe@clinic.com',
                        tenant_id=1
                    ),
                    Employee(
                        employee_number='EMP002',
                        first_name='Mike',
                        last_name='Johnson',
                        role='receptionist',
                        department='Front Desk',
                        phone='555-0125',
                        email='mike.johnson@clinic.com',
                        tenant_id=1
                    )
                ]
                for employee in default_employees:
                    session.add(employee)
                logger.info("Default employees created", "ClinicModule")