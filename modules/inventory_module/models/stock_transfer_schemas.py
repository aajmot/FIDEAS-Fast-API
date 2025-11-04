from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class StockTransferItemRequest(BaseModel):
    """Schema for individual stock transfer line item"""
    line_no: int = Field(..., description="Line number (sequential)")
    product_id: int = Field(..., description="Product being transferred")
    batch_number: Optional[str] = Field(None, max_length=50, description="Batch number if applicable")
    quantity: Decimal = Field(..., gt=0, description="Quantity to transfer")
    uom: str = Field("NOS", max_length=20, description="Unit of measurement")
    unit_cost_base: Decimal = Field(..., ge=0, description="Unit cost in base currency")
    
    # Optional per-item fields
    from_stock_before: Optional[Decimal] = Field(None, ge=0, description="Source stock before transfer")
    to_stock_before: Optional[Decimal] = Field(None, ge=0, description="Destination stock before transfer")
    unit_cost_foreign: Optional[Decimal] = Field(None, ge=0, description="Unit cost in foreign currency")
    reason: Optional[str] = Field(None, max_length=500, description="Item-specific reason")
    
    class Config:
        from_attributes = True


class StockTransferRequest(BaseModel):
    """Schema for creating stock transfer with multiple items"""
    
    # Header fields - Required
    transfer_number: str = Field(..., max_length=50, description="Unique transfer reference number")
    from_warehouse_id: int = Field(..., description="Source warehouse")
    to_warehouse_id: int = Field(..., description="Destination warehouse")
    transfer_date: datetime = Field(..., description="Date of transfer")
    transfer_type: str = Field(..., description="Type: INTERNAL, INTERCOMPANY, RETURN")
    
    # Header fields - Optional
    reason: Optional[str] = Field(None, max_length=500, description="General reason for transfer")
    status: str = Field("DRAFT", description="Status: DRAFT, APPROVED, IN_TRANSIT, COMPLETED, CANCELLED")
    currency_id: Optional[int] = Field(None, description="Currency ID (defaults to tenant's base currency)")
    approval_request_id: Optional[int] = Field(None, description="Approval request ID")
    is_active: bool = Field(True, description="Active status")
    
    # Line items - Required (at least one item)
    items: List[StockTransferItemRequest] = Field(..., min_length=1, description="List of transfer items")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "transfer_number": "TRF-2025-001",
                "from_warehouse_id": 1,
                "to_warehouse_id": 2,
                "transfer_date": "2025-11-04T10:30:00",
                "transfer_type": "INTERNAL",
                "reason": "Stock rebalancing",
                "status": "DRAFT",
                "items": [
                    {
                        "line_no": 1,
                        "product_id": 100,
                        "batch_number": "BATCH-001",
                        "quantity": 10.0,
                        "uom": "NOS",
                        "unit_cost_base": 150.00
                    },
                    {
                        "line_no": 2,
                        "product_id": 101,
                        "quantity": 5.0,
                        "uom": "NOS",
                        "unit_cost_base": 200.00
                    }
                ]
            }
        }
    
    @validator('transfer_date', pre=True)
    def parse_transfer_date(cls, v):
        """Allow various date formats"""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
    
    @validator('transfer_type')
    def validate_transfer_type(cls, v):
        """Validate transfer type"""
        allowed_types = ['INTERNAL', 'INTERCOMPANY', 'RETURN']
        if v.upper() not in allowed_types:
            raise ValueError(f'transfer_type must be one of: {", ".join(allowed_types)}')
        return v.upper()
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status"""
        allowed_statuses = ['DRAFT', 'APPROVED', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED']
        if v.upper() not in allowed_statuses:
            raise ValueError(f'status must be one of: {", ".join(allowed_statuses)}')
        return v.upper()
    
    @validator('to_warehouse_id')
    def validate_warehouses_different(cls, v, values):
        """Ensure from and to warehouses are different"""
        if 'from_warehouse_id' in values and v == values['from_warehouse_id']:
            raise ValueError('from_warehouse_id and to_warehouse_id must be different')
        return v
    
    @validator('items')
    def validate_items(cls, v):
        """Ensure at least one item and unique line numbers"""
        if not v or len(v) == 0:
            raise ValueError('At least one transfer item is required')
        
        line_numbers = [item.line_no for item in v]
        if len(line_numbers) != len(set(line_numbers)):
            raise ValueError('Line numbers must be unique')
        
        return v


class StockTransferItemResponse(BaseModel):
    """Schema for transfer line item response"""
    id: int
    line_no: int
    product_id: int
    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    quantity: Decimal
    uom: str
    from_stock_before: Decimal
    from_stock_after: Decimal
    to_stock_before: Decimal
    to_stock_after: Decimal
    unit_cost_base: Decimal
    total_cost_base: Decimal
    currency_id: Optional[int] = None
    unit_cost_foreign: Optional[Decimal] = None
    total_cost_foreign: Optional[Decimal] = None
    exchange_rate: Decimal
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class StockTransferResponse(BaseModel):
    """Schema for stock transfer header response"""
    id: int
    transfer_number: str
    from_warehouse_id: int
    from_warehouse_name: Optional[str] = None
    to_warehouse_id: int
    to_warehouse_name: Optional[str] = None
    transfer_date: datetime
    transfer_type: str
    reason: Optional[str] = None
    total_items: int
    total_quantity: Decimal
    total_cost_base: Decimal
    currency_id: Optional[int] = None
    exchange_rate: Decimal
    status: str
    approval_request_id: Optional[int] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    from_voucher_id: Optional[int] = None
    to_voucher_id: Optional[int] = None
    is_active: bool
    is_deleted: bool
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    items: Optional[List[StockTransferItemResponse]] = None
    
    class Config:
        from_attributes = True


class StockTransferListResponse(BaseModel):
    """Schema for paginated list of stock transfers"""
    total: int
    skip: int
    limit: int
    data: List[StockTransferResponse]
    
    class Config:
        from_attributes = True
