# People Module - Quick Reference

## 🚀 Quick Start

### Base URL
```
http://localhost:8000/api/v1/people
```

### Authentication
All endpoints require JWT token:
```
Authorization: Bearer {your_jwt_token}
```

## 📋 Department Endpoints

### Create Department
```http
POST /departments
Content-Type: application/json

{
  "department_code": "IT",
  "department_name": "Information Technology",
  "description": "IT Department",
  "branch_id": 1,
  "status": "ACTIVE"
}
```

### List Departments (Paginated)
```http
GET /departments?page=1&per_page=10&search=IT
```

### Get Active Departments
```http
GET /departments/active
```

### Get Department by ID
```http
GET /departments/{id}
```

### Update Department
```http
PUT /departments/{id}
Content-Type: application/json

{
  "department_name": "IT & Digital",
  "status": "ACTIVE"
}
```

### Delete Department (Soft)
```http
DELETE /departments/{id}
```

## 👥 Employee Endpoints

### Create Employee
```http
POST /employees
Content-Type: application/json

{
  "employee_code": "EMP001",
  "employee_name": "Dr. John Smith",
  "employee_type": "DOCTOR",
  "phone": "1234567890",
  "email": "john@example.com",
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

### List Employees (Paginated with Filters)
```http
GET /employees?page=1&per_page=10&search=john&employee_type=DOCTOR
```

### Get Active Employees
```http
GET /employees/active
```

### Get Employees by Type
```http
GET /employees/by-type/LAB_TECHNICIAN
```

### Get Employee by ID
```http
GET /employees/{id}
```

### Update Employee
```http
PUT /employees/{id}
Content-Type: application/json

{
  "employee_name": "Dr. John Smith Jr.",
  "specialization": "Interventional Cardiology",
  "status": "ACTIVE"
}
```

### Delete Employee (Soft)
```http
DELETE /employees/{id}
```

## 📊 Enums

### Department Status
- `ACTIVE`
- `INACTIVE`

### Employee Type
- `LAB_TECHNICIAN`
- `DOCTOR`
- `NURSE`
- `ADMIN`
- `OTHER`

### Employment Type
- `INTERNAL`
- `EXTERNAL`
- `CONTRACT`

### Employee Status
- `ACTIVE`
- `INACTIVE`
- `SUSPENDED`

## 🔍 Search & Filter

### Department Search
Searches in: `department_code`, `department_name`

### Employee Search
Searches in: `employee_code`, `employee_name`, `email`

### Employee Type Filter
```http
GET /employees?employee_type=DOCTOR
```

## 📝 Response Format

### Success Response (Single Item)
```json
{
  "id": 1,
  "tenant_id": 1,
  "department_code": "IT",
  "department_name": "Information Technology",
  "status": "ACTIVE",
  "created_at": "2024-01-01T00:00:00",
  "created_by": "admin",
  "updated_at": "2024-01-01T00:00:00",
  "updated_by": "admin",
  "is_deleted": false
}
```

### Paginated Response
```json
{
  "success": true,
  "message": "Departments retrieved successfully",
  "data": [...],
  "total": 100,
  "page": 1,
  "per_page": 10,
  "total_pages": 10
}
```

### Error Response
```json
{
  "detail": "Department not found"
}
```

## 🔐 Security

- All endpoints require authentication
- Tenant isolation enforced automatically
- Audit trail maintained (created_by, updated_by)
- Soft delete preserves data

## 📚 Swagger Documentation

Interactive API documentation available at:
```
http://localhost:8000/docs
```

Look for tags:
- **people-departments v1**
- **people-employees v1**

## ✅ Validation Rules

### Department
- `department_code`: Required, max 50 chars, unique per tenant
- `department_name`: Required, max 200 chars
- `status`: Must be ACTIVE or INACTIVE

### Employee
- `employee_code`: Required, max 50 chars, unique per tenant
- `employee_name`: Required, max 200 chars
- `employee_type`: Required, must be valid enum value
- `email`: Optional, max 100 chars
- `phone`: Optional, max 20 chars
- `license_expiry`: Optional, date format

## 🎯 Common Use Cases

### 1. Setup Organization Structure
```
1. Create departments
2. Assign departments to branches
3. Create employees
4. Assign employees to departments
```

### 2. Get All Doctors
```http
GET /employees/by-type/DOCTOR
```

### 3. Search for Employee
```http
GET /employees?search=john
```

### 4. Filter Active Lab Technicians
```http
GET /employees?employee_type=LAB_TECHNICIAN&page=1&per_page=50
```

## 🐛 Troubleshooting

### 401 Unauthorized
- Check if JWT token is valid
- Ensure token is in Authorization header

### 404 Not Found
- Verify entity ID exists
- Check if entity belongs to your tenant
- Ensure entity is not soft-deleted

### 400 Bad Request
- Check for duplicate codes
- Validate required fields
- Verify enum values

## 📞 Support

For issues or questions:
1. Check Swagger docs at `/docs`
2. Review error messages in response
3. Check application logs
4. Refer to detailed documentation in `/docs` folder
