# Department API Implementation - People Module

## Overview
Complete REST API for Department management in the new `people_module` following the same architecture pattern as the branches API.

## Structure Created

### 1. Module: `modules/people_module/`
- **Entity**: `models/department_entity.py` - SQLAlchemy ORM model
- **Service**: `services/department_service.py` - Business logic layer
- **Init files**: Proper module initialization

### 2. Schemas: `api/schemas/people_schema/`
- **department_schemas.py**: Pydantic validation schemas
  - `DepartmentStatus` - Enum (ACTIVE, INACTIVE)
  - `DepartmentBase` - Base schema with all fields
  - `DepartmentCreate` - Create schema
  - `DepartmentUpdate` - Update schema (all optional)
  - `DepartmentResponse` - Response schema

### 3. Routes: `api/v1/routers/people_routes/`
- **departments_route.py**: REST API endpoints

## API Endpoints

All endpoints are prefixed with `/api/v1/people/departments`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create new department |
| GET | `/` | Get paginated departments with search |
| GET | `/active` | Get all active departments |
| GET | `/{department_id}` | Get department by ID |
| PUT | `/{department_id}` | Update department |
| DELETE | `/{department_id}` | Soft delete department |

## Features

✅ **Complete CRUD Operations**
- Create, Read, Update, Delete (soft delete)

✅ **Business Logic in Service Layer**
- `create()` - Create department with validation
- `get_by_id()` - Retrieve by ID
- `get_by_code()` - Find by code and tenant
- `get_active_departments()` - Get active departments
- `get_paginated()` - Paginated list with search
- `update()` - Update department
- `soft_delete()` - Non-destructive deletion

✅ **Security & Isolation**
- Authentication required (JWT)
- Tenant isolation (automatic filtering)
- User tracking (created_by, updated_by)

✅ **Data Validation**
- Pydantic schemas for request/response validation
- Field validation (non-empty, length constraints)
- Enum validation for status

✅ **Search & Pagination**
- Search by department_code or department_name
- Configurable page size
- Total count and page metadata

## Database Schema

Maps to `public.departments` table:
- `id` - Primary key
- `tenant_id` - Foreign key to tenants (CASCADE)
- `branch_id` - Foreign key to branches (SET NULL)
- `department_code` - Unique per tenant
- `department_name` - Required
- `description` - Optional text
- `status` - ACTIVE/INACTIVE
- Audit fields: created_at, created_by, updated_at, updated_by, is_deleted

## Registration

✅ Routes registered in `api/main.py`
✅ Model imported for SQLAlchemy registration
✅ Proper module structure with __init__ files

## Usage Example

```python
# Create Department
POST /api/v1/people/departments
{
  "department_code": "IT",
  "department_name": "Information Technology",
  "description": "IT Department",
  "branch_id": 1,
  "status": "ACTIVE"
}

# Get Departments (Paginated)
GET /api/v1/people/departments?page=1&per_page=10&search=IT

# Get Active Departments
GET /api/v1/people/departments/active

# Update Department
PUT /api/v1/people/departments/1
{
  "department_name": "IT & Digital",
  "status": "ACTIVE"
}

# Delete Department (Soft)
DELETE /api/v1/people/departments/1
```

## Testing

Access Swagger UI at: `http://localhost:8000/docs`
Look for the "people-departments v1" tag

## Notes

- All operations are tenant-scoped
- Duplicate department codes per tenant are prevented
- Soft delete preserves data integrity
- Search is case-insensitive (ILIKE)
- Follows the same pattern as branches API for consistency
