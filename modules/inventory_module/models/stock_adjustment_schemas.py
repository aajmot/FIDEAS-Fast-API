from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class StockAdjustmentItemRequest(BaseModel):
    """Schema for individual stock adjustment line item"""
    line_no: int = Field(..., description="Line number (sequential)")
    product_id: int = Field(..., description="Product being adjusted")
    batch_number: Optional[str] = Field(None, max_length=50, description="Batch number if applicable")
    adjustment_qty: Decimal = Field(..., description="Quantity adjustment (+ve = increase, -ve = decrease)")
    uom: str = Field("NOS", max_length=20, description="Unit of measurement")
    unit_cost_base: Decimal = Field(..., ge=0, description="Unit cost in base currency")
    
    # Optional per-item fields
    stock_before: Optional[Decimal] = Field(None, ge=0, description="Stock before adjustment (for audit)")
    unit_cost_foreign: Optional[Decimal] = Field(None, ge=0, description="Unit cost in foreign currency")
    reason: Optional[str] = Field(None, max_length=500, description="Item-specific reason")
    
    class Config:
        from_attributes = True


class StockAdjustmentRequest(BaseModel):
    """Schema for creating stock adjustment with multiple items"""
    
    # Header fields - Required
    adjustment_number: str = Field(..., max_length=50, description="Unique adjustment reference number")
    warehouse_id: int = Field(..., description="Warehouse where adjustment is made")
    adjustment_date: datetime = Field(..., description="Date of adjustment")
    adjustment_type: str = Field(..., description="Type: PHYSICAL, DAMAGED, THEFT, OTHER")
    reason: str = Field(..., max_length=500, description="General reason for adjustment")
    
    # Header fields - Optional
    currency_id: Optional[int] = Field(None, description="Currency ID (defaults to tenant's base currency)")
    voucher_id: Optional[int] = Field(None, description="Linked accounting voucher")
    is_active: bool = Field(True, description="Active status")
    
    # Line items - Required (at least one item)
    items: List[StockAdjustmentItemRequest] = Field(..., min_length=1, description="List of adjustment items")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "adjustment_number": "ADJ-2025-001",
                "warehouse_id": 1,
                "adjustment_date": "2025-11-04T10:30:00",
                "adjustment_type": "PHYSICAL",
                "reason": "Physical count variance",
                "currency_id": 1,
                "items": [
                    {
                        "line_no": 1,
                        "product_id": 100,
                        "batch_number": "BATCH-001",
                        "adjustment_qty": 5.0,
                        "uom": "NOS",
                        "unit_cost_base": 150.00,
                        "stock_before": 95.0,
                        "reason": "Found in storage"
                    },
                    {
                        "line_no": 2,
                        "product_id": 101,
                        "adjustment_qty": -3.0,
                        "uom": "NOS",
                        "unit_cost_base": 200.00,
                        "stock_before": 50.0,
                        "reason": "Damaged units"
                    }
                ]
            }
        }
    
    @validator('adjustment_date', pre=True)
    def parse_adjustment_date(cls, v):
        """Allow various date formats"""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
    
    @validator('adjustment_type')
    def validate_adjustment_type(cls, v):
        """Validate adjustment type"""
        allowed_types = ['PHYSICAL', 'DAMAGED', 'THEFT', 'OTHER']
        if v.upper() not in allowed_types:
            raise ValueError(f'adjustment_type must be one of: {", ".join(allowed_types)}')
        return v.upper()
    
    @validator('items')
    def validate_items(cls, v):
        """Ensure at least one item and unique line numbers"""
        if not v or len(v) == 0:
            raise ValueError('At least one adjustment item is required')
        
        line_numbers = [item.line_no for item in v]
        if len(line_numbers) != len(set(line_numbers)):
            raise ValueError('Line numbers must be unique')
        
        return v


class StockAdjustmentItemResponse(BaseModel):
    """Schema for adjustment line item response"""
    id: int
    line_no: int
    product_id: int
    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    adjustment_qty: Decimal
    uom: str
    stock_before: Decimal
    stock_after: Decimal
    unit_cost_base: Decimal
    cost_impact: Decimal
    currency_id: Optional[int] = None
    unit_cost_foreign: Optional[Decimal] = None
    cost_impact_foreign: Optional[Decimal] = None
    exchange_rate: Decimal
    reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class StockAdjustmentResponse(BaseModel):
    """Schema for stock adjustment header response"""
    id: int
    adjustment_number: str
    warehouse_id: int
    warehouse_name: Optional[str] = None
    adjustment_date: datetime
    adjustment_type: str
    reason: str
    total_items: int
    net_quantity_change: Decimal
    total_cost_impact: Decimal
    currency_id: Optional[int] = None
    exchange_rate: Decimal
    voucher_id: Optional[int] = None
    is_active: bool
    is_deleted: bool
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    items: Optional[List[StockAdjustmentItemResponse]] = None
    
    class Config:
        from_attributes = True
