# Test Orders API Refactoring Summary

## Changes Made

### 1. Separated Entity Files
**File: `modules/health_module/models/test_order_entity.py`** (NEW)
- Extracted `TestOrder` and `TestOrderItem` entities from `diagnostic_entities.py`
- Maintains all schema changes from previous update

**File: `modules/health_module/models/diagnostic_entities.py`** (UPDATED)
- Now imports `TestOrder` and `TestOrderItem` from `test_order_entity.py`
- Keeps other diagnostic entities (TestPanel, TestResult, etc.)

### 2. Validation Schemas
**File: `api/schemas/health_schemas/test_order_schema.py`** (NEW)

#### TestOrderItemSchema
- Validates line_no (must be > 0)
- Validates test_id or panel_id (exactly one required)
- Validates rates, amounts, percentages (non-negative)
- Validates item_status (PENDING, SAMPLE_COLLECTED, IN_PROGRESS, COMPLETED, CANCELLED)
- All tax fields validated (cgst, sgst, igst, cess rates 0-100%)

#### TestOrderCreateSchema
- Required fields: test_order_number, patient_id, patient_name, patient_phone, doctor_name
- Validates urgency (ROUTINE, URGENT, STAT, CRITICAL)
- Validates status (DRAFT, ORDERED, SAMPLE_COLLECTED, IN_PROGRESS, COMPLETED, CANCELLED, REPORTED)
- Validates all amounts are non-negative
- Validates discount/cess percentages (0-100%)
- Requires at least 1 item

#### TestOrderUpdateSchema
- All fields optional
- Same validation rules as create schema
- Uses exclude_unset=True to only update provided fields

**File: `api/schemas/health_schemas/__init__.py`** (NEW)
- Package initialization with exports

### 3. Service Layer Validation
**File: `modules/health_module/services/test_order_service.py`** (UPDATED)

#### Update Method
- Validates order exists and belongs to tenant
- Prevents modification of COMPLETED/REPORTED orders (except status changes)
- Validates tenant_id for multi-tenant isolation
- Proper error handling with HTTPException

#### Delete Method
- Validates order exists and belongs to tenant
- Prevents deletion of COMPLETED/REPORTED orders
- Validates tenant_id for multi-tenant isolation
- Soft delete (sets is_deleted=True)
- Cascades delete to order items

### 4. API Routes
**File: `api/v1/routers/health_routes/testorders_route.py`** (UPDATED)

#### POST /testorders
- Uses `TestOrderCreateSchema` for validation
- Automatic validation of all fields before processing

#### PUT /testorders/{order_id}
- Uses `TestOrderUpdateSchema` for validation
- Passes tenant_id to service for isolation
- Only updates provided fields (exclude_unset=True)

#### DELETE /testorders/{order_id}
- Passes tenant_id to service for isolation
- Business logic validation in service layer

## Validation Rules Summary

### Create Validations
✓ Required fields present
✓ Patient ID and Doctor name mandatory
✓ At least one order item
✓ Either test_id OR panel_id per item (not both)
✓ All amounts non-negative
✓ Percentages between 0-100
✓ Valid status and urgency values

### Update Validations
✓ Order exists and belongs to tenant
✓ Cannot modify COMPLETED/REPORTED orders
✓ Same field-level validations as create
✓ Only provided fields are updated

### Delete Validations
✓ Order exists and belongs to tenant
✓ Cannot delete COMPLETED/REPORTED orders
✓ Soft delete with cascade to items

## Benefits
1. **Separation of Concerns**: Entities in separate files for better organization
2. **Type Safety**: Pydantic schemas provide automatic validation
3. **Business Logic**: Service layer enforces business rules
4. **Multi-tenant**: Proper tenant isolation in all operations
5. **Error Handling**: Clear error messages with appropriate HTTP status codes
6. **Maintainability**: Easier to modify and extend validation rules
