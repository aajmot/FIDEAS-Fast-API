import customtkinter as ctk
import tkinter as tk
from core.shared.components.base_screen import BaseScreen
from modules.clinic_module.services.employee_service import EmployeeService
from core.shared.middleware.exception_handler import ExceptionMiddleware

class EmployeeScreen(BaseScreen):
    def __init__(self, parent, clinic_module, **kwargs):
        self.clinic_module = clinic_module
        self.employee_service = EmployeeService()
        self.selected_employee = None
        super().__init__(parent, **kwargs)
    
    def setup_ui(self):
        super().setup_ui()
        
        # Title and back button
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(header_frame, text="Employee Management", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=10, pady=10)
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
        
        ctk.CTkLabel(form_frame, text="Role:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.role_var = ctk.StringVar(value="nurse")
        self.role_dropdown = ctk.CTkComboBox(form_frame, variable=self.role_var, 
                                           values=["nurse", "receptionist", "admin", "technician", "cleaner"], width=200)
        self.role_dropdown.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Department:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.department_input = ctk.CTkEntry(form_frame, width=200)
        self.department_input.grid(row=1, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Phone:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.phone_input = ctk.CTkEntry(form_frame, width=200)
        self.phone_input.grid(row=2, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Email:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.email_input = ctk.CTkEntry(form_frame, width=200)
        self.email_input.grid(row=2, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(form_frame, text="Salary:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.salary_input = ctk.CTkEntry(form_frame, width=200)
        self.salary_input.grid(row=3, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="Create", command=self.save_employee, height=25, font=ctk.CTkFont(size=10))
        self.save_btn.pack(side="left", padx=5, pady=5)
        ctk.CTkButton(button_frame, text="Clear", command=self.clear_form, height=25, font=ctk.CTkFont(size=10)).pack(side="left", padx=5, pady=5)
        
        # Data Grid
        columns = [
            {'key': 'id', 'title': 'ID', 'width': 40},
            {'key': 'employee_number', 'title': 'Employee #', 'width': 100},
            {'key': 'first_name', 'title': 'First Name', 'width': 120},
            {'key': 'last_name', 'title': 'Last Name', 'width': 120},
            {'key': 'role', 'title': 'Role', 'width': 100},
            {'key': 'department', 'title': 'Department', 'width': 120},
            {'key': 'phone', 'title': 'Phone', 'width': 120}
        ]
        
        from core.shared.components.data_grid import DataGrid
        self.data_grid = DataGrid(
            self, 
            columns, 
            on_row_select=self.on_employee_select,
            on_delete=self.on_employee_delete,
            items_per_page=10,
            use_enhanced=True
        )
        self.data_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.load_employees()
    
    @ExceptionMiddleware.handle_exceptions("EmployeeScreen")
    def load_employees(self):
        employees = self.employee_service.get_all(tenant_id=1)
        employees_data = []
        
        for employee in employees:
            employee_data = {
                'id': employee.id,
                'employee_number': employee.employee_number,
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'role': employee.role,
                'department': employee.department or '',
                'phone': employee.phone
            }
            employees_data.append(employee_data)
        
        self.data_grid.set_data(employees_data)
    
    def on_employee_select(self, employee_data):
        self.selected_employee = employee_data
        self.first_name_input.delete(0, tk.END)
        self.first_name_input.insert(0, employee_data['first_name'])
        self.last_name_input.delete(0, tk.END)
        self.last_name_input.insert(0, employee_data['last_name'])
        self.role_var.set(employee_data['role'])
        self.department_input.delete(0, tk.END)
        self.department_input.insert(0, employee_data['department'])
        self.phone_input.delete(0, tk.END)
        self.phone_input.insert(0, employee_data['phone'])
        
        # Load full employee details
        employees = self.employee_service.get_all(tenant_id=1)
        employee = next((e for e in employees if e.id == employee_data['id']), None)
        if employee:
            self.email_input.delete(0, tk.END)
            self.email_input.insert(0, employee.email or '')
            self.salary_input.delete(0, tk.END)
            self.salary_input.insert(0, str(employee.salary) if employee.salary else '')
        
        self.save_btn.configure(text="Update")
    
    @ExceptionMiddleware.handle_exceptions("EmployeeScreen")
    def save_employee(self):
        if not all([self.first_name_input.get(), self.last_name_input.get(), self.phone_input.get()]):
            self.show_message("Please fill required fields", "error")
            return
        
        try:
            employee_data = {
                'first_name': self.first_name_input.get(),
                'last_name': self.last_name_input.get(),
                'role': self.role_var.get(),
                'department': self.department_input.get(),
                'phone': self.phone_input.get(),
                'email': self.email_input.get(),
                'salary': float(self.salary_input.get()) if self.salary_input.get() else None,
                'tenant_id': 1
            }
            
            if self.selected_employee:
                self.employee_service.update(self.selected_employee['id'], employee_data)
                action = "updated"
            else:
                self.employee_service.create(employee_data)
                action = "created"
            
            self.show_message(f"Employee {action} successfully")
            self.clear_form()
            self.load_employees()
        except Exception as e:
            action = "updating" if self.selected_employee else "creating"
            self.show_message(f"Error {action} employee: {str(e)}", "error")
    
    def clear_form(self):
        self.selected_employee = None
        self.first_name_input.delete(0, tk.END)
        self.last_name_input.delete(0, tk.END)
        self.role_var.set("nurse")
        self.department_input.delete(0, tk.END)
        self.phone_input.delete(0, tk.END)
        self.email_input.delete(0, tk.END)
        self.salary_input.delete(0, tk.END)
        self.save_btn.configure(text="Create")
    @ExceptionMiddleware.handle_exceptions("EmployeeScreen")
    def on_employee_delete(self, employees_data):
        """Handle employee deletion"""
        try:
            for employee_data in employees_data:
                self.employee_service.delete(employee_data['id'])
            
            self.show_message(f"Successfully deleted {len(employees_data)} employee(s)")
            self.clear_form()
            return True
        except Exception as e:
            self.show_message(f"Error deleting employees: {str(e)}", "error")
            return False