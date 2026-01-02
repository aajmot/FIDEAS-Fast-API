# Employee API Implementation - People Module

## Overview
Complete REST API for Employee management in the `people_module` following the same architecture pattern.

## Structure

### Entity: `modules/people_module/models/employee_entity.py`
SQLAlchemy ORM model mapping to `employees` table

### Service: `modules/people_module/services/employee_service.py`
Business logic layer with methods:
- `create()` - Create employee
- `get_by_id()` - Get by ID
- `get_by_code()` - Find by code and tenant
- `get_active_employees()` - Get active employees
- `get_by_type()` - Filter by employee type
- `get_paginated()` - Paginated list with search
- `update()` - Update employee
- `soft_delete()` - Soft delete

### Schemas: `api/schemas/people_schema/employee_schemas.py`
Pydantic validation schemas:
- `EmployeeType` - Enum (LAB_TECHNICIAN, DOCTOR, NURSE, ADMIN, OTHER)
- `EmploymentType` - Enum (INTERNAL, EXTERNAL, CONTRACT)
- `EmployeeStatus` - Enum (ACTIVE, INACTIVE, SUSPENDED)
- `EmployeeCreate` - Create schema
- `EmployeeUpdate` - Update schema
- `EmployeeResponse` - Response schema

### Routes: `api/v1/routers/people_routes/employees_route.py`
REST API endpoints

## API Endpoints

Base URL: `/api/v1/people/employees`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create employee |
| GET | `/` | Get paginated employees (with search & type filter) |
| GET | `/active` | Get all active employees |
| GET | `/by-type/{employee_type}` | Get employees by type |
| GET | `/{employee_id}` | Get employee by ID |
| PUT | `/{employee_id}` | Update employee |
| DELETE | `/{employee_id}` | Soft delete employee |

## Features

✅ **Employee Types Support**
- LAB_TECHNICIAN
- DOCTOR
- NURSE
- ADMIN
- OTHER

✅ **Employment Types**
- INTERNAL
- EXTERNAL
- CONTRACT

✅ **Status Management**
- ACTIVE
- INACTIVE
- SUSPENDED

✅ **Professional Details**
- Qualification
- Specialization
- License number & expiry

✅ **Organization Links**
- Branch assignment
- Department assignment

✅ **Search & Filter**
- Search by code, name, or email
- Filter by employee type
- Pagination support

✅ **Security**
- JWT authentication
- Tenant isolation
- Audit trail

## Database Schema

Maps to `public.employees` table:
- `id` - Primary key
- `tenant_id` - Foreign key to tenants (CASCADE)
- `branch_id` - Foreign key to branches (SET NULL)
- `department_id` - Foreign key to departments (SET NULL)
- `employee_code` - Unique per tenant
- `employee_name` - Required
- `employee_type` - Required (enum)
- `phone`, `email` - Contact info
- `qualification`, `specialization` - Professional details
- `license_number`, `license_expiry` - License info
- `employment_type` - INTERNAL/EXTERNAL/CONTRACT
- `status` - ACTIVE/INACTIVE/SUSPENDED
- `remarks` - Optional notes
- Audit fields: created_at, created_by, updated_at, updated_by, is_active, is_deleted

## Usage Examples

### Create Employee
```json
POST /api/v1/people/employees
{
  "employee_code": "EMP001",
  "employee_name": "Dr. John Smith",
  "employee_type": "DOCTOR",
  "phone": "1234567890",
  "email": "john.smith@example.com",
  "qualification": "MBBS, MD",
  "specialization": "Cardiology",
  "license_number": "MED12345",
  "license_expiry": "2025-12-31",
  "department_id": 1,
  "branch_id": 1,
  "employment_type": "INTERNAL",
  "status": "ACTIVE"
}
```

### Get Employees with Filters
```
GET /api/v1/people/employees?page=1&per_page=10&search=john&employee_type=DOCTOR
```

### Get Employees by Type
```
GET /api/v1/people/employees/by-type/LAB_TECHNICIAN
```

### Update Employee
```json
PUT /api/v1/people/employees/1
{
  "employee_name": "Dr. John Smith Jr.",
  "specialization": "Interventional Cardiology",
  "status": "ACTIVE"
}
```

## Testing

Access Swagger UI at: `http://localhost:8000/docs`
Look for the **"people-employees v1"** tag

## Integration

The Employee API integrates with:
- **Departments**: Links employees to departments
- **Branches**: Links employees to branches
- **Tenants**: Multi-tenant isolation

## Notes

- Employee codes must be unique per tenant
- Soft delete preserves data integrity
- License expiry tracking for compliance
- Support for multiple employee types in single table
- Search is case-insensitive
