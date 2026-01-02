from core.database.connection import db_manager
from modules.health_module.models.clinic_entities import Employee
from core.shared.utils.logger import logger

class EmployeeService:
    def __init__(self):
        self.logger_name = "EmployeeService"
    
    def create(self, employee_data):
        try:
            with db_manager.get_session() as session:
                # Generate employee number
                last_employee = session.query(Employee).order_by(Employee.id.desc()).first()
                employee_number = f"EMP{(last_employee.id + 1):03d}" if last_employee else "EMP001"
                
                employee = Employee(
                    employee_number=employee_number,
                    **employee_data
                )
                session.add(employee)
                session.flush()
                logger.info(f"Employee created: {employee.employee_number}", self.logger_name)
                return employee
        except Exception as e:
            logger.error(f"Error creating employee: {str(e)}", self.logger_name)
            raise
    
    def get_all(self, tenant_id=None):
        try:
            with db_manager.get_session() as session:
                query = session.query(Employee)
                if tenant_id:
                    query = query.filter(Employee.tenant_id == tenant_id)
                employees = query.filter(Employee.is_active == True).all()
                for employee in employees:
                    session.expunge(employee)
                return employees
        except Exception as e:
            logger.error(f"Error fetching employees: {str(e)}", self.logger_name)
            return []
    
    def update(self, employee_id, employee_data):
        try:
            with db_manager.get_session() as session:
                employee = session.query(Employee).filter(Employee.id == employee_id).first()
                if employee:
                    for key, value in employee_data.items():
                        setattr(employee, key, value)
                    logger.info(f"Employee updated: {employee.employee_number}", self.logger_name)
                    return employee
        except Exception as e:
            logger.error(f"Error updating employee: {str(e)}", self.logger_name)
            raise
    
    def delete(self, employee_id):
        try:
            with db_manager.get_session() as session:
                employee = session.query(Employee).filter(Employee.id == employee_id).first()
                if employee:
                    employee.is_active = False
                    logger.info(f"Employee deactivated: {employee.employee_number}", self.logger_name)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting employee: {str(e)}", self.logger_name)
            raise